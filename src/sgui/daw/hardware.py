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
        self.record_checkbox.toggled.connect(self.device_changed)
        f_index = int(a_index) + 1
        a_layout.addWidget(self.record_checkbox, f_index, 0)
        a_layout.addWidget(QLabel(a_name), f_index, 1)
        self.track_combobox = QComboBox()
        self.track_combobox.setMinimumWidth(180)
        self.track_combobox.addItems(shared.TRACK_NAMES)
        shared.TRACK_NAME_COMBOBOXES.append(self.track_combobox)
        self.track_combobox.currentIndexChanged.connect(self.device_changed)
        a_layout.addWidget(self.track_combobox, f_index, 2)
        self.suppress_updates = False

    def device_changed(self, a_val=None):
        if (
            shared.SUPPRESS_TRACK_COMBOBOX_CHANGES
            or
            self.suppress_updates
        ):
            return
        track_index = self.track_combobox.currentIndex()
        constants.DAW_PROJECT.ipc().midi_device(
            self.record_checkbox.isChecked(),
            self.index,
            track_index,
        )
        if track_index:  # not master
            constants.DAW_PROJECT.check_output(track_index)
        self.save_callback()

    def get_routing(self):
        return MIDIRoute(
            1 if self.record_checkbox.isChecked() else 0,
            self.track_combobox.currentIndex(),
            self.name,
        )

    def set_routing(self, a_routing):
        self.suppress_updates = True
        self.track_combobox.setCurrentIndex(a_routing.track_num)
        self.record_checkbox.setChecked(a_routing.on)
        self.suppress_updates = False

class MidiDevicesDialog:
    """ The container for all of the MidiDevice objects, located in
        the DAW Hardware tab
    """
    def __init__(self):
        self.layout = QGridLayout()
        self.devices = []
        self.devices_dict = {}
        if not util.MIDI_IN_DEVICES:
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
            QLabel(_("Output")),
            0,
            2,
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

    def get_routings(self):
        return MIDIRoutes([x.get_routing() for x in self.devices])

    def save_callback(self):
        constants.DAW_PROJECT.save_midi_routing(self.get_routings())

    def set_routings(self):
        f_routings = constants.DAW_PROJECT.get_midi_routing()
        for f_routing in f_routings.routings:
            if f_routing.device_name in self.devices_dict:
                self.devices_dict[f_routing.device_name].set_routing(f_routing)


class HardwareWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.vlayout = QVBoxLayout(self)

        self.overdub_checkbox = QCheckBox(_("Overdub"))
        self.overdub_checkbox.clicked.connect(self.on_overdub_changed)
        #self.vlayout.addWidget(self.overdub_checkbox)
        self.vlayout.addWidget(
            QLabel(_("MIDI Input Devices"))
        )

        self.vlayout.addLayout(shared.MIDI_DEVICES_DIALOG.layout)
        self.active_devices = []

        self.audio_inputs = AudioInputWidget()
        self.vlayout.addWidget(self.audio_inputs.widget)
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
#        self.loop_mode_combobox.currentIndex() > 0:
#            QMessageBox.warning(
#                self.group_box, _("Error"),
#                _("Cannot use overdub mode with loop mode to record"))
#            return False
        self.setDisabled(True)

    def on_stop(self):
        self.setEnabled(True)

