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

from sgui import shared as glbl_shared
from sgui.widgets.control import slider_control
from sglib.lib._ctypes import *
from sglib.hardware.rpi import is_rpi
from sglib.lib.process import run_process
from sglib.math import clip_value
from sgui import sgqt

import ctypes
import locale
import os
import sys
import time

NO_MIDI_DEVICES_MSG = """\
No MIDI devices detected.  If this is not expected, try closing Stargate DAW,
then unplugging and plugging your MIDI device back in,  Check that you have
drivers installed if required by your device
"""

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
from sglib.log import LOG

THREADS_TOOLTIP = _("""\
Number of worker threads for processing plugins and effects.  Setting to 1 can
result in the best latency, but may not provide enough CPU power.  Should be
set to less than the number of cores, not threads.
""")

HUGEPAGES_TOOLTIP = _("""\
HugePages can improve memory/cache performance (sometimes significantly),
but you must allocate system memory for it that can only be used for HugePages.
"""
)

HOST_API_TOOLTIP = _("""\
Select the audio API to list devices for in the "Audio Device" dropdown.  Not
all host APIs are ideal for audio, research the host APIs available for your
operating system.
""")

if util.IS_LINUX:
    HOST_API_TOOLTIP = """\
Select the audio API to list devices for in the "Audio Device" dropdown.
If possible, use ALSA directly, without Pipewire, for the best performance,
latency and stability.
"""

DEVICE_TOOLTIP = _("""\
Select your audio interface from this list.  If you are unsure, use the Test
button until you hear audio come out of the correct speakers.
""")

class HardwareDialog:
    def __init__(self):
        self.devices_open = False
        self.device_name = None
        self.sample_rates = ["44100", "48000", "88200", "96000", "192000"]
        self.buffer_sizes = ["32", "64", "128", "256", "512", "1024", "2048"]

    def open_devices(self):
        if util.IS_LINUX:
            pa_paths = ("libportaudio.so.2", "libportaudio.so")
            pm_paths = (
                'libportmidi.so.2',
                'libportmidi.so.0',
                'libportmidi.so',
            )
        elif util.IS_MACOS:
            pa_paths = (
                os.path.join(util.INSTALL_PREFIX, 'libportaudio.2.dylib'),
                os.path.join(util.ENGINE_DIR, 'libportaudio.2.dylib'),
                "/usr/local/lib/libportaudio.dylib",
                "libportaudio.dylib",
            )
            pm_paths = (
                os.path.join(util.INSTALL_PREFIX, 'libportmidi.dylib'),
                os.path.join(util.ENGINE_DIR, 'libportmidi.dylib'),
                "/usr/local/lib/libportmidi.dylib",
                "libportmidi.dylib",
            )
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
        patch_ctypes(True)
        self.pyaudio = ctypes.CDLL(pa_paths)
        self.pyaudio.Pa_GetDeviceInfo.restype = ctypes.POINTER(
            portaudio.PaDeviceInfo)
        self.pyaudio.Pa_GetDeviceInfo.argstype = [ctypes.c_int]
        self.pyaudio.Pa_GetHostApiInfo.restype = ctypes.POINTER(
            portaudio.PaHostApiInfo,
        )
        self.pyaudio.Pa_GetHostApiInfo.argstype = [ctypes.c_int]
        self.pyaudio.Pa_IsFormatSupported.argstype = [
            ctypes.POINTER(portaudio.PaStreamParameters),
            ctypes.POINTER(portaudio.PaStreamParameters),
            ctypes.c_double,
        ]
        self.pyaudio.Pa_IsFormatSupported.restype = ctypes.c_int
        self.pyaudio.Pa_GetErrorText.argstype = [ctypes.c_int]
        self.pyaudio.Pa_GetErrorText.restype = ctypes.c_char_p
        LOG.info("Initializing Portaudio")
        self.pyaudio.Pa_Initialize()

        LOG.info("Loading PortMIDI library")
        self.pypm = None
        try:
            self.pypm = ctypes.CDLL(pm_paths)
        except ImportError:
            pass
        if not self.pypm:
            LOG.warning(
                "No Portmidi detected, the user will not be able to "
                "configure a MIDI device"
            )
        else:
            self.pypm.Pm_GetDeviceInfo.restype = ctypes.POINTER(
                portmidi.PmDeviceInfo,
            )
            LOG.info("Initializing PortMIDI")
            self.pypm.Pm_Initialize()
        self.devices_open = True
        LOG.info("Finished opening hardware devices")
        revert_patch_ctypes()

    def close_devices(self):
        if self.devices_open:
            import _ctypes
            import gc
            LOG.info("Terminating Portaudio")
            self.pyaudio.Pa_Terminate()
            LOG.info("Terminating PortMIDI")
            if self.pypm:
                self.pypm.Pm_Terminate()
                if util.IS_WINDOWS:
                    _ctypes.FreeLibrary(self.pypm._handle)
                else:
                    _ctypes.dlclose(self.pypm._handle)
                del self.pypm

            if util.IS_WINDOWS:
                _ctypes.FreeLibrary(self.pyaudio._handle)
            else:
                _ctypes.dlclose(self.pyaudio._handle)
            del self.pyaudio
            gc.collect()
            self.devices_open = False
            time.sleep(0.5)  # Give the kernel audio API time to close
            LOG.info("Finished")
        else:
            pass
#            LOG.error("close_devices called, but devices are not open")

    def check_device(self):
        if not util.DEVICE_SETTINGS:
            return (
                "No hardware settings detected, please configure your "
                "sound card and MIDI hardware now"
            )
        elif [
            x for x in ("hostApi", "name")
            if x not in util.DEVICE_SETTINGS
        ]:
            return _("Invalid device configuration")

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
                            "w",
                            encoding='utf-8',
                            newline="\n",
                        )
                        for k, v in util.DEVICE_SETTINGS.items():
                            f_file.write("{}|{}\n".format(k, v))
                        f_file.write("\\")
                        f_file.close()
                        return
                return _(
                    "Device not found: {}\n\n"
                    "If this is not expected, then another application "
                    "may be using the device"
                ).format(f_device_str)
            else:
                return _("Device not found: {}").format(f_device_str)

    def hardware_dialog_factory(
        self,
        a_msg=None,
    ):
        self.dialog_result = False
        self.open_devices()
        f_window = QWidget()
        f_window.setObjectName("plugin_ui")
        LOG.info("Created dialog window, adding widgets")

        def f_close_event(a_self=None, a_event=None):
            self.close_devices()
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
        audio_tab_layout = QVBoxLayout(f_audio_out_tab)
        f_window_layout = QGridLayout()
        audio_tab_layout.addLayout(f_window_layout)

        f_midi_in_tab = QScrollArea()
        midi_in_tab_widget = QWidget()
        if self.pypm:
            f_tab_widget.addTab(f_midi_in_tab, _("MIDI In"))
        f_midi_in_layout = QVBoxLayout(midi_in_tab_widget)
        f_midi_in_tab.setWidgetResizable(True)
        f_midi_in_tab.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        f_midi_in_tab.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        f_midi_in_tab.setWidget(midi_in_tab_widget)

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
        if util.IS_WINDOWS or util.IS_MACOS:
            f_window_layout.addWidget(QLabel(_("Input Device")), 6, 0)
            f_input_name_combobox = QComboBox()
            f_input_name_combobox.setMinimumWidth(390)
            f_window_layout.addWidget(f_input_name_combobox, 6, 1)
        else:
            f_input_name_combobox = None
        f_window_layout.addWidget(QLabel(_("Sample Rate")), 10, 0)
        f_samplerate_combobox = QComboBox()
        f_samplerate_combobox.setToolTip(
            'The sample rate to request from this audio device.  Be sure to '
            'click the test button, as not all devices support all sample '
            'rates'
        )
        f_samplerate_combobox.addItems(self.sample_rates)
        f_window_layout.addWidget(f_samplerate_combobox, 10, 1)
        f_buffer_size_combobox = QComboBox()
        f_buffer_size_combobox.setToolTip(
            'The buffer size to request from the audio device, this will '
            'affect latency.  Note that not all audio devices support all '
            'buffer sizes, some will use a default value if this is too low'
        )
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
            f_hugepages_checkbox = QCheckBox(
                _("Use HugePages? (You must configure HugePages on your "
                "system first)"))
            f_hugepages_checkbox.setToolTip(_(HUGEPAGES_TOOLTIP))
            f_window_layout.addWidget(f_hugepages_checkbox, 70, 1)

        test_layout = QHBoxLayout()
        audio_tab_layout.addLayout(test_layout)
        f_test_button = QPushButton(_("Test"))
        f_test_button.setMinimumWidth(90)
        f_test_button.setToolTip(
            "Send a test sound to your soundcard using this configuration.  "
        )
        test_layout.addWidget(f_test_button)
        test_volume_slider = slider_control(
            QtCore.Qt.Orientation.Horizontal,
            'Test Volume',
            0,
            None,
            None,
            -36,
            -6,
            -15,
            tooltip=(
                'Adjust the volume of the sound played when the Test button '
                'is pressed'
            ),
        )
        test_layout.addWidget(test_volume_slider.control)

        f_ok_cancel_layout = QHBoxLayout()
        f_main_layout.addLayout(f_ok_cancel_layout)
        f_ok_button = QPushButton(_("OK"))
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_main_layout.addWidget(sgqt.HINT_BOX)
        sgqt.HINT_BOX.setMinimumHeight(120)
        sgqt.HINT_BOX.setMinimumWidth(100)
        sgqt.HINT_BOX.setMaximumHeight(100000)
        sgqt.HINT_BOX.setMaximumWidth(100000)

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
            try:
                f_dev_name = f_dev.contents.name.decode(TEXT_ENCODING)
            except Exception as ex:
                try:
                    dev_name = f_dev.contents.name.decode(
                        TEXT_ENCODING,
                        errors='replace',
                    )
                except Exception as ex2:
                    dev_name = str(ex2)
                LOG.error(
                    f"{host_api_name}: Unable to decode a device name: {ex}, "
                    f"{locale.getlocale()}, {dev_name}"
                )
                continue
            host_api_name = host_api_dict[f_dev.contents.hostApi]
            LOG.info(
                f"{i}: {host_api_name}: {f_dev_name} "
                f"in: {f_dev.contents.maxInputChannels} "
                f"out: {f_dev.contents.maxOutputChannels} "
                f"sr: {f_dev.contents.defaultSampleRate} "
            )
            f_host_api = f_host_api_names[f_dev.contents.hostApi]
            f_name_to_index[f_host_api][f_dev_name] = i
            f_result_dict[f_host_api][f_dev_name] = f_dev.contents
            f_host_api_device_names[f_host_api].append(f_dev_name)
        LOG.info("Finished enumerating audio devices")

        f_host_api_input_names = {
            k:[x for x in v if f_result_dict[k][x].maxInputChannels]
            for k, v in f_host_api_device_names.items()
            if v
        }

        f_host_api_device_names = {
            k:[x for x in v if f_result_dict[k][x].maxOutputChannels >= 2]
            for k, v in f_host_api_device_names.items()
            if v
        }

        for f_list in list(
            f_host_api_device_names.values()
        ) + list(
            f_host_api_input_names.values()
        ):
            f_list.sort(key=lambda x: x.lower())

        f_io_layout = QHBoxLayout()
        f_window_layout.addLayout(f_io_layout, 7, 1)

        f_io_layout.addWidget(QLabel(_("Input Count")))
        f_audio_in_spinbox = QSpinBox()
        f_audio_in_spinbox.setToolTip(
            'Configure the number of audio inputs, up to the maximum '
            'supported by this audio device.  If not using the inputs, '
            'setting to zero can improve latency and performance'
        )
        f_audio_in_spinbox.setRange(0, 0)
        f_io_layout.addWidget(f_audio_in_spinbox)

        def out_count_changed(a_val):
            for x in OUT_SPINBOXES:
                x.setMaximum(a_val - 1)

        f_io_layout.addWidget(QLabel(_("Output Count")))
        f_audio_out_spinbox = QSpinBox()
        f_audio_out_spinbox.setToolTip(
            'The output count, up to the maximum supported by this audio '
            'device.  Currently, Stargate only supports using 2 outputs as '
            'a stereo pair, this affects which outputs can be selected below'
        )
        f_audio_out_spinbox.setRange(2, 2)
        f_io_layout.addWidget(f_audio_out_spinbox)
        f_audio_out_spinbox.valueChanged.connect(out_count_changed)

        f_window_layout.addWidget(QLabel(_("Default Output")), 8, 0)
        f_default_outs_layout = QHBoxLayout()
        f_window_layout.addLayout(f_default_outs_layout, 8, 1)

        f_default_outs_layout.addWidget(QLabel("L"))
        f_default_L = QSpinBox()
        f_default_L.setToolTip(
            'The output channel to use on this audio device for the left '
            'channel.  If you soundcard has more than 2 output channels, '
            'and you are not using the first pair, you may need to change this'
        )
        f_default_L.setRange(0, 1)
        f_default_outs_layout.addWidget(f_default_L)
        f_default_outs_layout.addWidget(QLabel("R"))
        f_default_R = QSpinBox()
        f_default_R.setRange(0, 1)
        f_default_R.setToolTip(
            'The output channel to use on this audio device for the right '
            'channel.  If you soundcard has more than 2 output channels, '
            'and you are not using the first pair, you may need to change this'
        )
        f_default_R.setValue(1)
        f_default_outs_layout.addWidget(f_default_R)

        OUT_SPINBOXES = (f_default_L, f_default_R)

        self.midi_in_checkboxes = {}

        if self.pypm:
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
                f_midi_device_name = f_midi_device_name.replace('|', '')
                if f_midi_device.contents.input == 1:
                    f_checkbox = QCheckBox(f_midi_device_name)
                    f_checkbox.setToolTip(
                        'Check this box to enable the use of this MIDI device '
                        'in Stargate DAW'
                    )
                    if f_midi_device_name in util.MIDI_IN_DEVICES:
                        f_checkbox.setChecked(True)
                    self.midi_in_checkboxes[f_midi_device_name] = f_checkbox

            for f_cbox in sorted(
                self.midi_in_checkboxes,
                key=lambda x: x.lower(),
            ):
                f_midi_in_layout.addWidget(self.midi_in_checkboxes[f_cbox])
            if not self.midi_in_checkboxes:
                f_midi_in_layout.addWidget(
                    QLabel(NO_MIDI_DEVICES_MSG)
                )
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
                f_host_api_device_names[self.subsystem],
            )
            if util.IS_WINDOWS or util.IS_MACOS:
                f_input_name_combobox.clear()
                f_input_name_combobox.addItems(
                    [""] + f_host_api_input_names[self.subsystem],
                )

        def output_combobox_changed(a_self=None, a_val=None):
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
            if util.IS_WINDOWS or util.IS_MACOS:
                idx_lookup = {
                    f_input_name_combobox.itemText(i): i
                    for i in range(f_input_name_combobox.count())
                }
                if f_str in idx_lookup:
                    f_input_name_combobox.setCurrentIndex(idx_lookup[f_str])
                else:
                    f_input_name_combobox.setCurrentIndex(0)
            else:
                f_in_count = f_result_dict[
                    self.subsystem][self.device_name].maxInputChannels
                f_in_count = clip_value(f_in_count, 0, 128)
                f_audio_in_spinbox.setMaximum(f_in_count)
                f_audio_in_spinbox.setValue(
                    int(f_in_count if f_in_count < 16 else 16),
                )

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
                f_audio_in_spinbox.setValue(0)
                return
            f_in_count = f_result_dict[
                self.subsystem][self.input_name].maxInputChannels
            f_in_count = clip_value(f_in_count, 0, 128)
            f_audio_in_spinbox.setMaximum(f_in_count)
            f_audio_in_spinbox.setValue(
                int(f_in_count if f_in_count < 16 else 16),
            )

        def create_config(config_path):
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
                f_hugepages = 1 if f_hugepages_checkbox.isChecked() else 0
            f_audio_inputs = f_audio_in_spinbox.value()
            f_out_tuple = (f_audio_out_spinbox,) + OUT_SPINBOXES
            f_audio_outputs = "|".join(str(x.value()) for x in f_out_tuple)
            test_volume = test_volume_slider.control.value()

            try:
                #if (
                #    (util.IS_WINDOWS or util.IS_MACOS)
                #    and
                #    f_audio_inputs
                #):
                if False:
                    f_input = portaudio.PaStreamParameters(
                        f_name_to_index[self.subsystem][self.device_name],
                        f_audio_inputs,
                        portaudio.paInt16,
                        float(f_buffer_size) / float(f_samplerate),
                        None,
                    )
                    f_input_ref = ctypes.byref(f_input)
                else:
                    f_input_ref = 0
                f_output = portaudio.PaStreamParameters(
                    f_name_to_index[self.subsystem][self.device_name],
                    f_audio_out_spinbox.value(),
                    portaudio.paFloat32,
                    float(f_buffer_size) / float(f_samplerate),
                    None,
                )
                f_supported = self.pyaudio.Pa_IsFormatSupported(
                    f_input_ref,
                    ctypes.byref(f_output),
                    ctypes.c_double(float(f_samplerate)),
                )
                LOG.info(f"Pa_IsFormatSupported returned {f_supported}")
                if f_supported:  # != 0
                    msg = self.pyaudio.Pa_GetErrorText(f_supported).decode()
                    LOG.error(msg)
                    QMessageBox.warning(
                        f_window,
                        _("Error"),
                        _(f"Audio device returned: {msg}"),
                    )
                    raise Exception(msg)
                with open(
                    config_path,
                    "w",
                    encoding='utf-8',
                    newline="\n",
                ) as f:
                    f.write("hostApi|{}\n".format(self.subsystem))
                    f.write("name|{}\n".format(self.device_name))
                    if (
                        util.IS_WINDOWS
                        or
                        util.IS_MACOS
                    ) and self.input_name:
                        f.write("inputName|{}\n".format(self.input_name))
                    f.write("bufferSize|{}\n".format(f_buffer_size))
                    f.write("sampleRate|{}\n".format(f_samplerate))
                    f.write("threads|{}\n".format(f_worker_threads))

                    if util.IS_LINUX:
                        f.write("hugePages|{}\n".format(f_hugepages))
                    f.write("audioInputs|{}\n".format(f_audio_inputs))
                    f.write("audioOutputs|{}\n".format(f_audio_outputs))
                    f.write("testVolume|{}\n".format(test_volume))
                    for f_midi_in_device in f_midi_in_devices:
                        f.write(f"midiInDevice|{f_midi_in_device}\n")
                    f.write("\\")
            except Exception as ex:
                LOG.exception(ex)
                raise ex

        def on_test():
            config_path = util.DEVICE_CONFIG_PATH + '.test'
            create_config(config_path)
            cmd = [
                util.BIN_PATH,
                "soundcheck",
                config_path,
            ]
            cmd = util.has_pasuspender(cmd)
            proc = run_process(cmd)
            for i in range(5):
                time.sleep(1)
                retcode = proc.poll()
                if retcode is None:
                    continue
                elif retcode == 0:
                    return
                else:
                    msg = f"soundcheck returned error code {retcode}"
                    LOG.error(msg)
                    QMessageBox.warning(f_window, _("Error"), msg)
                    return
            proc.kill()

        def on_ok(a_self=None):
            try:
                create_config(util.DEVICE_CONFIG_PATH)
                self.close_devices()

                self.dialog_result = True

                time.sleep(1.0)
                util.read_device_config()
                glbl_shared.MAIN_STACKED_WIDGET.next()
            except Exception as ex:
                LOG.exception(ex)

        def on_cancel(a_self=None):
            glbl_shared.MAIN_STACKED_WIDGET.previous()

        f_test_button.pressed.connect(on_test)
        f_ok_button.pressed.connect(on_ok)
        f_cancel_button.pressed.connect(on_cancel)

        f_subsystem_combobox.currentIndexChanged.connect(subsystem_changed)
        f_device_name_combobox.currentIndexChanged.connect(
            output_combobox_changed,
        )
        if util.IS_WINDOWS or util.IS_MACOS:
            f_input_name_combobox.currentIndexChanged.connect(
                input_combobox_changed,
            )

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
                    (util.IS_WINDOWS or util.IS_MACOS)
                    and
                    "inputName" in util.DEVICE_SETTINGS
                ):
                    f_name = util.DEVICE_SETTINGS["inputName"]
                    if f_name in f_result_dict[self.subsystem]:
                        f_input_name_combobox.setCurrentIndex(
                            f_input_name_combobox.findText(f_name),
                        )

        if "audioInputs" in util.DEVICE_SETTINGS:
            f_count = int(util.DEVICE_SETTINGS["audioInputs"])
            f_audio_in_spinbox.setValue(f_count)

        if "testVolume" in util.DEVICE_SETTINGS:
            test_volume = int(util.DEVICE_SETTINGS["testVolume"])
            test_volume_slider.control.setValue(test_volume)

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
            if "hugePages" in util.DEVICE_SETTINGS and \
            int(util.DEVICE_SETTINGS["hugePages"]) == 1:
                f_hugepages_checkbox.setChecked(True)

        if a_msg is not None:
            QMessageBox.warning(f_window, _("Information"), a_msg)
        latency_changed()
        container = QWidget()
        container_layout = QGridLayout(container)
        container_layout.addWidget(f_window, 1, 1)
        container_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            0,
            1,
        )
        container_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            1,
            2,
        )
        container_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            2,
            1,
        )
        container_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            1,
            0,
        )
        return container

