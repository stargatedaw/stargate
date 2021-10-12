#!/usr/bin/env python3

"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

from sglib.hardware.rpi import is_rpi
from sglib.math import clip_value
import ctypes
import os
import sys
import time

if __name__ == "__main__":
    # For running as a stand-alone script
    f_parent_dir = os.path.dirname(os.path.abspath(__file__))
    f_parent_dir = os.path.abspath(os.path.join(f_parent_dir, "../.."))
    sys.path.insert(0, f_parent_dir)
from sgui.sgqt import *
from sglib.models import theme

from sglib.lib import (
    portaudio,
    portmidi,
    util,
)
from sglib.lib.translate import _, TEXT_ENCODING
from sglib.log import (
    LOG,
    setup_logging,
)

THREADS_TOOLTIP = _("""\
This sets the number of worker threads for processing
plugins and effects.

Setting to 1 can result in the best latency, but
may (or may not) provide enough CPU power depending
on your CPU's single-threaded performance.  Also,
projects with complex audio routing may perform
better with fewer threads.

It is recommended that you not more than one thread
per CPU core. (Intel hyperthreading should NOT be
considered additional cores).

Auto attempts to pick a sane number of worker threads
automatically based on your CPU.

If you're not sure how to use this setting, you should
leave it on 'Auto'.

It is also recommended that you leave one or more
cores unused to power the UI and operating system,
for example:

dual-core:  1 worker thread
quad-core:  1 - 3 worker threads
""")

HUGEPAGES_TOOLTIP = _("""\
HugePages can improve memory/cache performance (sometimes significantly),
but you must allocate system memory for it that can only be used for HugePages.

It is recommended that you allocate at least 1GB of HugePages, and that you
leave AT LEAST 2GB of non-HugePage memory for other processes.  (if you use
other memory intensive applications that are not HugePage-enabled, you may
need to leave more than 2GB)

To allocate HugePages, run this command to see your HugePage size:

grep -i hugepage /proc/meminfo

Then add a line like this to the end of /etc/sysctl.conf and reboot:

# 1024 * 2MB HugePages = 2GB of HugePages
vm.nr_hugepages=1024

Some older CPUs and kernels don't support or have buggy support for HugePages,
disable this if it causes performance problems on your configuration.
"""
)

HOST_API_TOOLTIP = _("""\
Select the host API to list devices for in the
"Audio Device" dropdown.
""")

if util.IS_LINUX:
    HOST_API_TOOLTIP += _("""\
Unless you are using Firewire (for which JACK is the only choice on Linux),
it is recommended that you stop the JACK server and use your
device directly using ALSA for best performance, stability and latency.
""")
elif util.IS_WINDOWS:
    HOST_API_TOOLTIP += _("""\
If possible, you should use an API capable of low latency
such as ASIO or WDM-KS.
""")

DEVICE_TOOLTIP = _("""\
Select your audio interface from this list.
""")

class hardware_dialog:
    def __init__(self, a_is_running=False, splash_screen=None):
        self.splash_screen = splash_screen
        self.devices_open = False
        self.is_running = a_is_running
        self.device_name = None
        self.sample_rates = ["44100", "48000", "88200", "96000", "192000"]
        self.buffer_sizes = ["32", "64", "128", "256", "512", "1024", "2048"]

    def open_devices(self):
        if util.IS_LINUX:
            pa_paths = ("libportaudio.so.2", "libportaudio.so.2")
            pm_paths = ("libportmidi.so.0", "libportmidi.so.0")
        elif util.IS_MAC_OSX:
            pa_paths = ("libportaudio.dylib",)
            pm_paths = ("libportmidi.dylib",)
        elif util.IS_WINDOWS:
            pm_paths = (
                os.path.join(
                    util.ENGINE_DIR,
                    "libportmidi.dll",
                ),
            )
            pa_paths = (
                os.path.join(
                    util.ENGINE_DIR,
                    "libportaudio.dll",
                ),
            )
        else:
            LOG.error(
                "Unsupported platform, don't know where to look "
                "for shared libraries."
            )
            raise NotImplementedError

        LOG.info("Loading Portaudio library")
        self.pyaudio = None
        for path in pa_paths:
            try:
                ctypes.cdll.LoadLibrary(path)
                self.pyaudio = ctypes.CDLL(path)
            except Exception as ex:
                LOG.warn(f"Failed to load portaudio: {ex}")
        if not self.pyaudio:
            raise ImportError(
                f"Cannot find one of {pa_paths}, please "
                "install Portaudio"
            )
        self.pyaudio.Pa_GetDeviceInfo.restype = ctypes.POINTER(
            portaudio.PaDeviceInfo)
        self.pyaudio.Pa_GetDeviceInfo.argstype = [ctypes.c_int]
        self.pyaudio.Pa_GetHostApiInfo.restype = ctypes.POINTER(
            portaudio.PaHostApiInfo)
        self.pyaudio.Pa_GetHostApiInfo.argstype = [ctypes.c_int]
        self.pyaudio.Pa_IsFormatSupported.argstype = [
            ctypes.POINTER(portaudio.PaStreamParameters),
            ctypes.POINTER(portaudio.PaStreamParameters),
            ctypes.c_double,
        ]
        LOG.info("Initializing Portaudio")
        self.pyaudio.Pa_Initialize()

        LOG.info("Loading PortMIDI library")
        self.pypm = None
        for path in pm_paths:
            try:
                ctypes.cdll.LoadLibrary(path)
                self.pypm = ctypes.CDLL(path)
            except Exception as ex:
                LOG.warn(f"Could not find {path}")
        if not self.pypm:
            raise ImportError(
                f"Unable to find one of {pm_paths}, please install Portmidi"
            )
        self.pypm.Pm_GetDeviceInfo.restype = ctypes.POINTER(
            portmidi.PmDeviceInfo,
        )
        LOG.info("Initializing PortMIDI")
        self.pypm.Pm_Initialize()
        self.devices_open = True
        LOG.info("Finished opening hardware devices")

    def close_devices(self):
        if self.devices_open:
            import _ctypes
            import gc
            LOG.info("Terminating Portaudio")
            self.pyaudio.Pa_Terminate()
            LOG.info("Terminating PortMIDI")
            self.pypm.Pm_Terminate()
            LOG.info("Cleaning up...")
            for x in (self.pyaudio._handle, self.pypm._handle):
                if util.IS_WINDOWS:
                    _ctypes.FreeLibrary(x)
                else:
                    _ctypes.dlclose(x)
            del self.pyaudio
            del self.pypm
            gc.collect()
            self.devices_open = False
            time.sleep(0.5)  # Give the kernel audio API time to close
            LOG.info("Finished")
        else:
            pass
#            LOG.error("close_devices called, but devices are not open")
#            import traceback
#            traceback.print_stack()

    def check_device(self, a_splash_screen=None):
        if not util.DEVICE_SETTINGS:
            self.show_hardware_dialog(
                None,
                a_exit_on_cancel=True,
            )
            return
        elif [
            x for x in ("hostApi", "name")
            if x not in util.DEVICE_SETTINGS
        ]:
            if a_splash_screen:
                LOG.info("Hiding splash screen")
                a_splash_screen.hide()
            self.show_hardware_dialog(
                _("Invalid device configuration"),
                a_exit_on_cancel=True,
            )
            if a_splash_screen:
                LOG.info("Showing splash screen")
                a_splash_screen.show()
            return

        f_device_str = util.DEVICE_SETTINGS["name"]

        self.open_devices()

        f_count = self.pyaudio.Pa_GetDeviceCount()

        f_audio_device_names = []

        for i in range(f_count):
            f_dev = self.pyaudio.Pa_GetDeviceInfo(i)
            f_dev_name = f_dev.contents.name.decode(TEXT_ENCODING)
            f_audio_device_names.append(f_dev_name)
            if f_device_str == f_dev_name:
                break

        self.close_devices()

        if not f_device_str in f_audio_device_names:
            LOG.info("{} not in {}".format(f_device_str, f_audio_device_names))
            util.DEVICE_SETTINGS.pop("name")
            if "(hw:" in f_device_str:
                f_device_arr = f_device_str.split("(hw:")
                f_device_name = f_device_arr[0]
                f_device_num = f_device_arr[1].split(",", 1)[1]
                for f_device in f_audio_device_names:
                    if f_device.startswith(f_device_name) and \
                    f_device.endswith(f_device_num):
                        LOG.info(
                            _("It appears that the system switched up the "
                            "ALSA hw:X number, fixing it all sneaky-like "
                            "in the background.  (grumble, grumble...)"))
                        LOG.info(f_device)
                        util.DEVICE_SETTINGS["name"] = f_device
                        f_file = open(
                            util.DEVICE_CONFIG_PATH,
                            "w", newline="\n")
                        for k, v in util.DEVICE_SETTINGS.items():
                            f_file.write("{}|{}\n".format(k, v))
                        f_file.write("\\")
                        f_file.close()
                        return
                if a_splash_screen:
                    a_splash_screen.hide()
                self.show_hardware_dialog(
                    _(
                        "Device not found: {}\n\n"
                        "If this is not expected, then another application "
                        "may be using the device"
                    ).format(f_device_str),
                    a_exit_on_cancel=True,
                )
                if a_splash_screen:
                    a_splash_screen.show()
            else:
                if a_splash_screen:
                    a_splash_screen.hide()
                self.show_hardware_dialog(
                    _("Device not found: {}").format(f_device_str),
                    a_exit_on_cancel=True,
                )
                if a_splash_screen:
                    a_splash_screen.show()

    def show_hardware_dialog(
        self,
        a_msg=None,
        a_exit_on_cancel=False,
        notify_of_restart=True,
    ) -> bool:
        self.dialog_result = False
        self.open_devices()
        if self.is_running:
            f_window = QDialog()
        else:
            f_window = QWidget()
            f_window.setObjectName("plugin_ui")
        LOG.info("Created dialog window, adding widgets")

        def f_close_event(a_self=None, a_event=None):
            self.close_devices()
            if a_exit_on_cancel and not self.dialog_result:
                sys.exit(9876)
        self.input_name = ""

        f_window.closeEvent = f_close_event
        f_window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        f_window.setStyleSheet(theme.QSS)
        f_window.setWindowTitle(_("Hardware Settings..."))
        f_main_layout = QVBoxLayout(f_window)
        f_tab_widget = QTabWidget()
        f_main_layout.addWidget(f_tab_widget)

        f_audio_out_tab = QWidget()
        f_tab_widget.addTab(f_audio_out_tab, _("Audio"))
        f_window_layout = QGridLayout(f_audio_out_tab)

        f_midi_in_tab = QTabWidget()
        f_tab_widget.addTab(f_midi_in_tab, _("MIDI In"))
        f_midi_in_layout = QVBoxLayout(f_midi_in_tab)

        f_window_layout.addWidget(QLabel(_("Host API")), 2, 0)
        f_subsystem_combobox = QComboBox()
        f_subsystem_combobox.setToolTip(HOST_API_TOOLTIP)
        f_subsystem_combobox.setMinimumWidth(390)
        f_window_layout.addWidget(f_subsystem_combobox, 2, 1)

        f_window_layout.addWidget(QLabel(_("Audio Device")), 5, 0)
        f_device_name_combobox = QComboBox()
        f_device_name_combobox.setToolTip(DEVICE_TOOLTIP)
        f_device_name_combobox.setMinimumWidth(390)
        f_window_layout.addWidget(f_device_name_combobox, 5, 1)
        # TODO: Investigate if this is sitll needed
        if util.IS_WINDOWS or util.IS_MAC_OSX:
            f_window_layout.addWidget(QLabel(_("Input Device")), 6, 0)
            f_input_name_combobox = QComboBox()
            f_input_name_combobox.setMinimumWidth(390)
            f_window_layout.addWidget(f_input_name_combobox, 6, 1)
        f_window_layout.addWidget(QLabel(_("Sample Rate")), 10, 0)
        f_samplerate_combobox = QComboBox()
        f_samplerate_combobox.addItems(self.sample_rates)
        f_window_layout.addWidget(f_samplerate_combobox, 10, 1)
        f_buffer_size_combobox = QComboBox()
        f_buffer_size_combobox.addItems(self.buffer_sizes)
        f_buffer_size_combobox.setCurrentIndex(4)
        f_window_layout.addWidget(QLabel(_("Buffer Size")), 20, 0)
        f_window_layout.addWidget(f_buffer_size_combobox, 20, 1)
        f_latency_label = QLabel("")
        f_window_layout.addWidget(f_latency_label, 20, 2)

        f_window_layout.addWidget(QLabel(_("Worker Threads")), 30, 0)
        f_worker_threads_combobox = QComboBox()
        f_worker_threads_combobox.addItems(
            [_("Auto")] + [str(x) for x in range(1, util.CPU_COUNT + 1)])
        f_worker_threads_combobox.setToolTip(THREADS_TOOLTIP)
        f_window_layout.addWidget(f_worker_threads_combobox, 30, 1)

        if util.IS_LINUX:
            f_thread_affinity_checkbox = QCheckBox(
                _("Lock worker threads to own core?"))
            f_thread_affinity_checkbox.setToolTip(
                _(
                    "This locks worker threads to their own CPU core and "
                    "may give better\nperformance with fewer "
                    "audio drop-outs at low latency,"
                    "but may perform badly\non some configurations."
                )
            )
            f_window_layout.addWidget(f_thread_affinity_checkbox, 50, 1)
            f_hugepages_checkbox = QCheckBox(
                _("Use HugePages? (You must configure HugePages on your "
                "system first)"))
            f_hugepages_checkbox.setToolTip(_(HUGEPAGES_TOOLTIP))
            f_window_layout.addWidget(f_hugepages_checkbox, 70, 1)

        f_ok_cancel_layout = QHBoxLayout()
        f_main_layout.addLayout(f_ok_cancel_layout)
        f_ok_button = QPushButton(_("OK"))
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)

        f_count = self.pyaudio.Pa_GetHostApiCount()

        f_host_api_names = []
        host_api_dict = {}

        for i in range(f_count):
            name = self.pyaudio.Pa_GetHostApiInfo(
                i,
            ).contents.name.decode(TEXT_ENCODING)
            f_host_api_names.append(name)
            host_api_dict[i] = name

        f_count = self.pyaudio.Pa_GetDeviceCount()

        f_result_dict = {x:{} for x in f_host_api_names}
        f_name_to_index = {x:{} for x in f_host_api_names}
        f_host_api_device_names = {x:[] for x in f_host_api_names}

        LOG.info("Enumerating audio devices")
        for i in range(f_count):
            f_dev = self.pyaudio.Pa_GetDeviceInfo(i)
            f_dev_name = f_dev.contents.name.decode(TEXT_ENCODING)
            host_api_name = host_api_dict[f_dev.contents.hostApi]
            LOG.info(
                f"{i}: {host_api_name}: {f_dev_name} "
                f"in: {f_dev.contents.maxInputChannels} "
                f"out: {f_dev.contents.maxOutputChannels} "
                f"sr: {f_dev.contents.defaultSampleRate} "
            )
            if f_dev.contents.maxOutputChannels < 2:
                LOG.info(f"Skipping {f_dev_name}, less than 2 outputs")
                continue
            f_host_api = f_host_api_names[f_dev.contents.hostApi]
            f_name_to_index[f_host_api][f_dev_name] = i
            f_result_dict[f_host_api][f_dev_name] = f_dev.contents
            f_host_api_device_names[f_host_api].append(f_dev_name)
        LOG.info("Finished enumerating audio devices")

        f_host_api_input_names = {
            k:[x for x in v if f_result_dict[k][x].maxInputChannels]
            for k, v in f_host_api_device_names.items() if v}

        f_host_api_device_names = {
            k:[x for x in v if f_result_dict[k][x].maxOutputChannels]
            for k, v in f_host_api_device_names.items() if v}

        for f_list in list(f_host_api_device_names.values()
        ) + list(f_host_api_input_names.values()):
            f_list.sort(key=lambda x: x.lower())

        f_io_layout = QHBoxLayout()
        f_window_layout.addLayout(f_io_layout, 7, 1)

        f_io_layout.addWidget(QLabel(_("Input Count")))
        f_audio_in_spinbox = QSpinBox()
        f_audio_in_spinbox.setRange(0, 0)
        f_io_layout.addWidget(f_audio_in_spinbox)

        def out_count_changed(a_val):
            for x in OUT_SPINBOXES:
                x.setMaximum(a_val - 1)

        f_io_layout.addWidget(QLabel(_("Output Count")))
        f_audio_out_spinbox = QSpinBox()
        f_audio_out_spinbox.setRange(2, 2)
        f_io_layout.addWidget(f_audio_out_spinbox)
        f_audio_out_spinbox.valueChanged.connect(out_count_changed)

        f_window_layout.addWidget(QLabel(_("Default Output")), 8, 0)
        f_default_outs_layout = QHBoxLayout()
        f_window_layout.addLayout(f_default_outs_layout, 8, 1)

        f_default_outs_layout.addWidget(QLabel("L"))
        f_default_L = QSpinBox()
        f_default_L.setRange(0, 1)
        f_default_outs_layout.addWidget(f_default_L)
        f_default_outs_layout.addWidget(QLabel("R"))
        f_default_R = QSpinBox()
        f_default_R.setRange(0, 1)
        f_default_R.setValue(1)
        f_default_outs_layout.addWidget(f_default_R)

        OUT_SPINBOXES = (f_default_L, f_default_R)

        self.midi_in_checkboxes = {}

        LOG.info("Enumerating MIDI devices")
        for loop in range(self.pypm.Pm_CountDevices()):
            f_midi_device = self.pypm.Pm_GetDeviceInfo(loop)
            f_midi_device_name = \
                f_midi_device.contents.name.decode(TEXT_ENCODING)
#                LOG.info("DeviceID: {} Name: '{}' Input?: {} "
#                    "Output?: {} Opened: {} ".format(
#                    loop, f_midi_device_name, f_midi_device.contents.input,
#                    f_midi_device.contents.output,
#                    f_midi_device.contents.opened))
            if f_midi_device.contents.input == 1:
                f_checkbox = QCheckBox(f_midi_device_name)
                if f_midi_device_name in util.MIDI_IN_DEVICES:
                    f_checkbox.setChecked(True)
                self.midi_in_checkboxes[f_midi_device_name] = f_checkbox

            for f_cbox in sorted(
            self.midi_in_checkboxes, key=lambda x: x.lower()):
                f_midi_in_layout.addWidget(self.midi_in_checkboxes[f_cbox])
        LOG.info("Finished enumerating MIDI devices")

        f_midi_in_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )

        def latency_changed(a_self=None, a_val=None):
            f_sample_rate = float(str(f_samplerate_combobox.currentText()))
            f_buffer_size = float(str(f_buffer_size_combobox.currentText()))
            f_latency = (f_buffer_size / f_sample_rate) * 1000.0
            f_latency_label.setText("{} ms".format(round(f_latency, 1)))

        f_samplerate_combobox.currentIndexChanged.connect(latency_changed)
        f_buffer_size_combobox.currentIndexChanged.connect(latency_changed)

        def subsystem_changed(a_self=None, a_val=None):
            self.subsystem = str(f_subsystem_combobox.currentText())
            f_device_name_combobox.clear()
            f_device_name_combobox.addItems(
                f_host_api_device_names[self.subsystem])
            if util.IS_WINDOWS or util.IS_MAC_OSX:
                f_input_name_combobox.clear()
                f_input_name_combobox.addItems(
                    f_host_api_input_names[self.subsystem])

        def combobox_changed(a_self=None, a_val=None):
            f_str = str(f_device_name_combobox.currentText())
            if not f_str:
                return
            self.device_name = f_str
            f_samplerate = str(
                int(f_result_dict[self.subsystem
                ][self.device_name].defaultSampleRate))
            if f_samplerate in self.sample_rates:
                f_samplerate_combobox.setCurrentIndex(
                    f_samplerate_combobox.findText(f_samplerate))
            if not util.IS_WINDOWS and not util.IS_MAC_OSX:
                f_in_count = f_result_dict[
                    self.subsystem][self.device_name].maxInputChannels
                f_in_count = clip_value(f_in_count, 0, 128)
                f_audio_in_spinbox.setMaximum(f_in_count)
                f_audio_in_spinbox.setValue(
                    f_in_count if f_in_count < 16 else 16)

            f_out_count = f_result_dict[
                self.subsystem][self.device_name].maxOutputChannels
            f_out_count = clip_value(f_out_count, 0, 128)
            if f_out_count == 1:
                f_audio_out_spinbox.setMinimum(1)
            else:
                f_audio_out_spinbox.setMinimum(2)
            f_audio_out_spinbox.setMaximum(f_out_count)

        def input_combobox_changed(a_self=None, a_val=None):
            f_str = str(f_input_name_combobox.currentText())
            self.input_name = f_str
            if not f_str:
                f_audio_in_spinbox.setMaximum(0)
                return
            f_in_count = f_result_dict[
                self.subsystem][self.input_name].maxInputChannels
            f_in_count = clip_value(f_in_count, 0, 128)
            f_audio_in_spinbox.setMaximum(f_in_count)
            f_audio_in_spinbox.setValue(
                    f_in_count if f_in_count < 16 else 16)

        def on_ok(a_self=None):
            if is_rpi() and self.device_name.startswith('bcm'):
                f_warn_result = QMessageBox.question(
                    f_window,
                    _("Warning"),
                    _(
                        "It appears that you chose the built-in Raspberry "
                        "Pi audio device, which is known to work poorly with "
                        "real-time audio.  It is recommended that you use a "
                        "high quality USB audio device with a "
                        "class-compliant driver.  Do you still want to use"
                        "this device?"
                    ),
                    (
                        QMessageBox.StandardButton.Yes
                        |
                        QMessageBox.StandardButton.Cancel
                    ),
                    QMessageBox.StandardButton.Cancel,
                )
                if f_warn_result == QMessageBox.StandardButton.Cancel:
                    return
            elif self.device_name == "default":
                f_warn_result = QMessageBox.question(
                    f_window,
                    _("Warning"),
                    _("You have selected the 'default' audio device, "
                    "which may not be a valid device.  It is recommended "
                    "that you explicitly pick the audio device you "
                    "intend to use.  Use the 'default' device anyway?"),
                    (
                        QMessageBox.StandardButton.Yes
                        |
                        QMessageBox.StandardButton.Cancel
                    ),
                    QMessageBox.StandardButton.Cancel,
                )
                if f_warn_result == QMessageBox.StandardButton.Cancel:
                    return
            f_buffer_size = int(str(f_buffer_size_combobox.currentText()))
            f_samplerate = int(str(f_samplerate_combobox.currentText()))

            f_midi_in_devices = sorted(str(k)
                for k, v in self.midi_in_checkboxes.items()
                if v.isChecked())
            if len(f_midi_in_devices) >= 8:
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _("Using more than 8 MIDI devices is not supported, "
                    "please de-select some devices"),
                )
                return
            f_worker_threads = f_worker_threads_combobox.currentIndex()
            if util.IS_LINUX:
                f_thread_affinity = \
                    1 if f_thread_affinity_checkbox.isChecked() else 0
                f_hugepages = 1 if f_hugepages_checkbox.isChecked() else 0
            f_audio_inputs = f_audio_in_spinbox.value()
            f_out_tuple = (f_audio_out_spinbox,) + OUT_SPINBOXES
            f_audio_outputs = "|".join(str(x.value()) for x in f_out_tuple)

            try:
                #This doesn't work if the device is open already,
                #so skip the test, and if it fails the
                #user will be prompted again next time Stargate starts
                if (
                    not self.is_running
                    or
                    "name" not in util.DEVICE_SETTINGS
                    or (
                        util.DEVICE_SETTINGS["name"]
                        !=
                        self.device_name
                    )
                ):
                    if (
                        (util.IS_WINDOWS or util.IS_MAC_OSX)
                        and
                        f_audio_inputs
                    ):
                        f_input = portaudio.PaStreamParameters(
                            f_name_to_index[self.subsystem][self.device_name],
                            f_audio_inputs, portaudio.paInt16,
                            float(f_buffer_size) / float(f_samplerate), None)
                        f_input_ref = ctypes.byref(f_input)
                    else:
                        f_input_ref = 0
                    f_output = portaudio.PaStreamParameters(
                        f_name_to_index[self.subsystem][self.device_name],
                        2, portaudio.paInt16,
                        float(f_buffer_size) / float(f_samplerate), None)
                    f_supported = self.pyaudio.Pa_IsFormatSupported(
                        f_input_ref, ctypes.byref(f_output), f_samplerate)
                    if not f_supported:
                        raise Exception()
                f_file = open(
                    util.DEVICE_CONFIG_PATH, "w", newline="\n")
                f_file.write("hostApi|{}\n".format(self.subsystem))
                f_file.write("name|{}\n".format(self.device_name))
                if (
                    util.IS_WINDOWS
                    or
                    util.IS_MAC_OSX
                ) and self.input_name:
                    f_file.write("inputName|{}\n".format(self.input_name))
                f_file.write("bufferSize|{}\n".format(f_buffer_size))
                f_file.write("sampleRate|{}\n".format(f_samplerate))
                f_file.write("threads|{}\n".format(f_worker_threads))

                if util.IS_LINUX:
                    f_file.write(
                        "threadAffinity|{}\n".format(f_thread_affinity)
                    )
                    f_file.write("hugePages|{}\n".format(f_hugepages))
                f_file.write("audioInputs|{}\n".format(f_audio_inputs))
                f_file.write("audioOutputs|{}\n".format(f_audio_outputs))
                for f_midi_in_device in f_midi_in_devices:
                    f_file.write("midiInDevice|{}\n".format(
                        f_midi_in_device))

                f_file.write("\\")
                f_file.close()
                self.close_devices()

                self.dialog_result = True

                time.sleep(1.0)
                util.read_device_config()
                notify_restart()
                f_window.setResult(QDialog.DialogCode.Accepted)
                f_window.close()

            except Exception as ex:
                LOG.exception(ex)
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _(
                        "Couldn't open audio device\n\n{ex}\n\n"
                        "This may (or may not) be because the "
                        "device is already open by another application or "
                        "a sound daemon such as JACK."
                    ),
                )

        def on_cancel(a_self=None):
            # notify_restart()
            f_window.close()

        def notify_restart():
            if self.splash_screen:
                self.splash_screen.show()
            elif notify_of_restart:
                QMessageBox.warning(
                    f_window,
                    _("Info"),
                    _("Stargate will restart now"),
                )

        f_ok_button.pressed.connect(on_ok)
        f_cancel_button.pressed.connect(on_cancel)

        f_subsystem_combobox.currentIndexChanged.connect(subsystem_changed)
        f_device_name_combobox.currentIndexChanged.connect(combobox_changed)
        if util.IS_WINDOWS or util.IS_MAC_OSX:
            f_input_name_combobox.currentIndexChanged.connect(
                input_combobox_changed)

        f_subsystem_combobox.addItems(
            sorted(
                f_host_api_device_names, key=lambda x: x.lower()
            )
        )

        if "hostApi" in util.DEVICE_SETTINGS:
            f_host_api = util.DEVICE_SETTINGS["hostApi"]
            if f_host_api in f_host_api_device_names:
                self.subsystem = f_host_api
                f_subsystem_combobox.setCurrentIndex(
                    f_subsystem_combobox.findText(self.subsystem))

                if "name" in util.DEVICE_SETTINGS:
                    f_name = util.DEVICE_SETTINGS["name"]
                    if f_name in f_result_dict[self.subsystem]:
                        f_device_name_combobox.setCurrentIndex(
                            f_device_name_combobox.findText(f_name))
                    elif "(hw:" in f_name:
                        f_name = f_name.split("(hw:")[0]
                        for f_dev in f_result_dict[self.subsystem]:
                            if f_dev.startswith(f_name):
                                LOG.info("Device number changed, fixing")
                                f_device_name_combobox.setCurrentIndex(
                                    f_device_name_combobox.findText(f_dev))
                                break
                if (
                    (util.IS_WINDOWS or util.IS_MAC_OSX)
                    and
                    "inputName" in util.DEVICE_SETTINGS
                ):
                    f_name = util.DEVICE_SETTINGS["inputName"]
                    if f_name in f_result_dict[self.subsystem]:
                        f_input_name_combobox.setCurrentIndex(
                            f_input_name_combobox.findText(f_name))

        if "audioInputs" in util.DEVICE_SETTINGS:
            f_count = int(util.DEVICE_SETTINGS["audioInputs"])
            f_audio_in_spinbox.setValue(f_count)

        if "audioOutputs" in util.DEVICE_SETTINGS:
            f_count, f_L, f_R = (int(x) for x in
                util.DEVICE_SETTINGS["audioOutputs"].split("|"))
            f_audio_out_spinbox.setValue(f_count)
            f_default_L.setValue(f_L)
            f_default_R.setValue(f_R)

        if "bufferSize" in util.DEVICE_SETTINGS and \
        util.DEVICE_SETTINGS["bufferSize"] in self.buffer_sizes:
            f_buffer_size_combobox.setCurrentIndex(
                f_buffer_size_combobox.findText(
                    util.DEVICE_SETTINGS["bufferSize"]))

        if "sampleRate" in util.DEVICE_SETTINGS and \
        util.DEVICE_SETTINGS["sampleRate"] in self.sample_rates:
            f_samplerate_combobox.setCurrentIndex(
                f_samplerate_combobox.findText(
                    util.DEVICE_SETTINGS["sampleRate"]))

        if "threads" in util.DEVICE_SETTINGS:
            f_worker_threads_combobox.setCurrentIndex(
                int(util.DEVICE_SETTINGS["threads"]))

        if util.IS_LINUX:
            if "threadAffinity" in util.DEVICE_SETTINGS:
                if int(util.DEVICE_SETTINGS[
                "threadAffinity"]) == 1:
                    f_thread_affinity_checkbox.setChecked(True)

            if "hugePages" in util.DEVICE_SETTINGS and \
            int(util.DEVICE_SETTINGS["hugePages"]) == 1:
                f_hugepages_checkbox.setChecked(True)

        if a_msg is not None:
            QMessageBox.warning(f_window, _("Error"), a_msg)
        if self.splash_screen:
            self.splash_screen.hide()
        latency_changed()
        LOG.info("Showing dialog")
        if self.is_running:
            f_window.setResult(QDialog.DialogCode.Rejected)
            f_window.exec()
            result =f_window.result()
            LOG.info(f"hardware dialog returned {result}")
            return result == QDialog.DialogCode.Accepted
        else:
            f_window.show()

if __name__ == "__main__":
    setup_logging()
    def _hardware_dialog_standalone():
        app = QApplication(sys.argv)
        if len(sys.argv) == 2:
            f_msg = sys.argv[1]
        else:
            f_msg = None

        f_hardware_dialog = hardware_dialog()
        f_hardware_dialog.show_hardware_dialog(f_msg)
        sys.exit(app.exec())

    _hardware_dialog_standalone()
