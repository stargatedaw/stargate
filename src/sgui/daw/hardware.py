from sglib import constants
from sglib.models.daw.routing import MIDIRoute, MIDIRoutes
from sgui.daw import shared
from sgui.daw.sequencer.audio_input import AudioInputWidget
from sgui.daw.shared import *
from sglib.lib import  util
from sglib.lib.translate import _
from sgui.sgqt import *


class MidiDevice:
    """ The controls for an individual MIDI hardware device, as
        configured in the hardware dialog
    """
    def __init__(self, a_name, a_index, a_layout, a_save_callback):
        self.suppress_updates = True
        self.name = str(a_name)
        self.index = int(a_index)
        self.save_callback = a_save_callback
        self.record_checkbox = QCheckBox()
        self.record_checkbox.setToolTip(
            "Enable this MIDI device.  MIDI events events from this device "
            "will be sent to all plugins on the selected track, on the "
            "selected channel."
        )
        self.record_checkbox.toggled.connect(self.device_changed)
        f_index = int(a_index) + 1
        a_layout.addWidget(self.record_checkbox, f_index, 0)
        a_layout.addWidget(QLabel(a_name), f_index, 1)
        self.track_combobox = QComboBox()
        self.track_combobox.setToolTip(
            "The track to output this MIDI device to.  All MIDI events from "
            "this MIDI device will be recorded to this track, and sent to "
            "all plugins in this track's plugin rack"
        )
        self.track_combobox.setMinimumWidth(180)
        self.track_combobox.addItems(shared.TRACK_NAMES)
        shared.TRACK_NAME_COMBOBOXES.append(self.track_combobox)
        self.track_combobox.currentIndexChanged.connect(self.device_changed)
        a_layout.addWidget(self.track_combobox, f_index, 2)

        self.channel_combobox = QComboBox()
        self.channel_combobox.setMinimumWidth(48)
        self.channel_combobox.addItems(
            constants.MIDI_CHANNELS + ['Any'],
        )
        self.channel_combobox.setToolTip(
            'The MIDI channel on the output track to send MIDI events to.  '
            'Choose "All" to send to all channels, or "Any" to preserve the '
            'original channel(s) the MIDI device sent the events on.'
        )
        self.channel_combobox.currentIndexChanged.connect(self.device_changed)
        a_layout.addWidget(self.channel_combobox, f_index, 3)

        self.suppress_updates = False

    def device_changed(self, a_val=None):
        if (
            shared.SUPPRESS_TRACK_COMBOBOX_CHANGES
            or
            self.suppress_updates
        ):
            return
        channel = self.channel_combobox.currentIndex()
        track_index = self.track_combobox.currentIndex()
        constants.DAW_PROJECT.ipc().midi_device(
            self.record_checkbox.isChecked(),
            self.index,
            track_index,
            channel,
        )
        if track_index:  # not main
            constants.DAW_PROJECT.check_output(track_index)
        self.save_callback()

    def get_routing(self):
        return MIDIRoute(
            1 if self.record_checkbox.isChecked() else 0,
            self.track_combobox.currentIndex(),
            self.name,
            self.channel_combobox.currentIndex(),
        )

    def set_routing(self, a_routing):
        self.suppress_updates = True
        self.track_combobox.setCurrentIndex(a_routing.track_num)
        self.record_checkbox.setChecked(a_routing.on)
        self.suppress_updates = False

NO_MIDI_DEVICES_INSTRUCTIONS = """\
No MIDI devices enabled.  If you are using MIDI devices, ensure that they are
plugged in, and press the Hardware Settings button, go to the MIDI In tab, and
enable your MIDI device(s).
"""

class MidiDevicesDialog:
    """ The container for all of the MidiDevice objects, located in
        the DAW Hardware tab
    """
    def __init__(self):
        self.layout = QGridLayout()
        self.devices = []
        self.devices_dict = {}
        if not util.MIDI_IN_DEVICES:
            self.layout.addWidget(
                QLabel(NO_MIDI_DEVICES_INSTRUCTIONS),
                0,
                0,
            )
            return
        self.layout.addWidget(
            QLabel(_("On")),
            0,
            0,
        )
        self.layout.addWidget(
            QLabel(_("MIDI Device")),
            0,
            1,
        )
        self.layout.addWidget(
            QLabel(_("Output Track")),
            0,
            2,
        )
        self.layout.addWidget(
            QLabel(_("Output Channel")),
            0,
            3,
        )
        for f_name, f_i in zip(
            util.MIDI_IN_DEVICES,
            range(len(util.MIDI_IN_DEVICES)),
        ):
            f_device = MidiDevice(
                f_name,
                f_i,
                self.layout,
                self.save_callback,
            )
            self.devices.append(f_device)
            self.devices_dict[f_name] = f_device
        self.layout.addItem(
            QSpacerItem(
                10,
                10,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            ),
            0,
            10,
        )

    def get_routings(self):
        return MIDIRoutes([x.get_routing() for x in self.devices])

    def save_callback(self):
        constants.DAW_PROJECT.save_midi_routing(self.get_routings())

    def set_routings(self):
        f_routings = constants.DAW_PROJECT.get_midi_routing()
        LOG.info('set_routings: routings {}'.format(
            [x.__dict__ for x in f_routings.routings]
        ))
        LOG.info('set_routings: device dict {}'.format(
            {k:v.__dict__ for k, v in self.devices_dict.items()}
        ))
        for f_routing in f_routings.routings:
            if f_routing.device_name in self.devices_dict:
                self.devices_dict[f_routing.device_name].set_routing(f_routing)


class HardwareWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.vlayout = QVBoxLayout(self.widget)
        self.widget.setLayout(self.vlayout)
        self.hardware_settings_button = QPushButton('Hardware Settings')
        self.vlayout.addWidget(self.hardware_settings_button)
        self.hardware_settings_button.setToolTip(
            'Show the hardware settings dialog where you can enable or '
            'disable audio inputs and MIDI devices.  This will close and '
            'reopen the project window'
        )

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

        self.overdub_checkbox = QCheckBox(_("Overdub"))
        self.overdub_checkbox.clicked.connect(self.on_overdub_changed)
        #self.vlayout.addWidget(self.overdub_checkbox)
        self.vlayout.addWidget(
            QLabel(_("MIDI Input Devices"))
        )

        self.vlayout.addLayout(shared.MIDI_DEVICES_DIALOG.layout)
        self.active_devices = []

        self.vlayout.addWidget(QLabel(_("Audio Inputs")))
        self.audio_inputs = AudioInputWidget()
        self.vlayout.addLayout(self.audio_inputs.layout)
        self.vlayout.addItem(
            QSpacerItem(
                10,
                10,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

    def on_overdub_changed(self, a_val=None):
        constants.DAW_PROJECT.ipc().set_overdub_mode(
            self.overdub_checkbox.isChecked(),
        )

    def on_play(self):
        self.setDisabled(True)

    def on_rec(self):
#        if self.overdub_checkbox.isChecked() and \
#        self.loop_mode_checkbox.checkState() > 0:
#            QMessageBox.warning(
#                self.group_box, _("Error"),
#                _("Cannot use overdub mode with loop mode to record"))
#            return False
        self.setDisabled(True)

    def on_stop(self):
        self.setEnabled(True)

