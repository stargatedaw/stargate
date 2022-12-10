from sglib import constants
from sglib.log import LOG
from sglib.lib.util import *
from sglib.models.daw import *
from sgui.daw.shared import *
from sgui.plugins import *
from sgui.sgqt import *

from sglib.lib import util
from sglib.lib.translate import _
from sglib.models.stargate import AudioInputTrack, AudioInputTracks
from sgui.daw import shared


class AudioInput:
    def __init__(self, a_num, a_layout, a_callback, a_count):
        self.input_num = int(a_num)
        self.callback = a_callback
        a_layout.addWidget(QLabel(str(a_num)), a_num + 1, 21)
        self.name_lineedit = QLineEdit(str(a_num))
        self.name_lineedit.setToolTip(
            'A friendly, human-readable name for this audio input channel.  '
            'Set this to something that describes your recording setup.'
        )
        self.name_lineedit.setMaxLength(64)
        self.name_lineedit.setMaximumWidth(240)
        self.name_lineedit.editingFinished.connect(self.name_update)
        a_num += 1
        a_layout.addWidget(self.name_lineedit, a_num, 0)
        self.rec_checkbox = QCheckBox()
        self.rec_checkbox.setToolTip(
            "Record arm this track.  It's audio will be recorded to the "
            "selected track when the record button is pressed"
        )
        self.rec_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.rec_checkbox, a_num, 1)

        self.monitor_checkbox = QCheckBox()
        self.monitor_checkbox.setToolTip(
            "Monitor this input.  It's audio will be sent through the "
            "selected track at all times"
        )
        self.monitor_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.monitor_checkbox, a_num, 2)

        self.vol_layout = QHBoxLayout()
        a_layout.addLayout(self.vol_layout, a_num, 6)
        self.vol_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.vol_slider.setToolTip(
            "The volume gain of this input channel"
        )
        self.vol_slider.setRange(-240, 240)
        self.vol_slider.setValue(0)
        self.vol_slider.setMinimumWidth(240)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_slider.sliderReleased.connect(self.update_engine)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QLabel("0.0dB")
        self.vol_label.setMinimumWidth(64)
        self.vol_layout.addWidget(self.vol_label)
        self.stereo_combobox = QComboBox()
        self.stereo_combobox.setToolTip(
            "Select another input channel to pair as a stereo channel "
            "to this channel"
        )
        a_layout.addWidget(self.stereo_combobox, a_num, 3)
        self.stereo_combobox.setMinimumWidth(75)
        self.stereo_combobox.addItems(
            [_("None")] + [str(x) for x in range(a_count + 1)]
        )
        self.stereo_combobox.currentIndexChanged.connect(self.update_engine)
        self.output_mode_combobox = QComboBox()
        self.output_mode_combobox.setToolTip(
            "The track input to send this input to.  Normal: The normal audio "
            "input, Sidechain: the sidechain input only, Both: The normal and "
            "sidechain inputs of the track"
        )
        self.output_mode_combobox.setMinimumWidth(100)
        self.output_mode_combobox.addItems([
            _("Normal"),
            _("Sidechain"),
            _("Both"),
        ])
        a_layout.addWidget(self.output_mode_combobox, a_num, 4)
        self.output_mode_combobox.currentIndexChanged.connect(
            self.update_engine)
        self.output_track_combobox = QComboBox()
        self.output_track_combobox.setToolTip(
            "The track to send this input to"
        )
        self.output_track_combobox.setMinimumWidth(140)
        shared.TRACK_NAME_COMBOBOXES.append(self.output_track_combobox)
        self.output_track_combobox.addItems(shared.TRACK_NAMES)
        self.output_track_combobox.currentIndexChanged.connect(
            self.output_track_changed)
        a_layout.addWidget(self.output_track_combobox, a_num, 5)
        self.suppress_updates = False

    def output_track_changed(self, a_val=None):
        if (
            not self.suppress_updates
            and
            not shared.SUPPRESS_TRACK_COMBOBOX_CHANGES
        ):
            f_track = self.output_track_combobox.currentIndex()
            if f_track in shared.TRACK_PANEL.tracks:
                constants.DAW_PROJECT.check_output(f_track)
                self.update_engine()
            else:
                LOG.info("{} not in shared.TRACK_PANEL".format(f_track))

    def name_update(self, a_val=None):
        self.update_engine(a_notify=False)

    def update_engine(self, a_val=None, a_notify=True):
        if not self.suppress_updates:
            self.callback(a_notify)

    def vol_changed(self):
        f_vol = self.get_vol()
        self.vol_label.setText("{}dB".format(f_vol))
        if not self.suppress_updates:
            constants.IPC.audio_input_volume(self.input_num, f_vol)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def get_name(self):
        return str(self.name_lineedit.text())

    def get_value(self):
        f_on = 1 if self.rec_checkbox.isChecked() else 0
        f_vol = self.get_vol()
        f_monitor = 1 if self.monitor_checkbox.isChecked() else 0
        f_stereo = self.stereo_combobox.currentIndex() - 1
        f_mode = self.output_mode_combobox.currentIndex()
        f_output = self.output_track_combobox.currentIndex()
        f_name = self.name_lineedit.text()

        return AudioInputTrack(
            f_on,
            f_monitor,
            f_vol,
            f_output,
            f_stereo,
            f_mode,
            f_name,
        )

    def set_value(self, a_val):
        self.suppress_updates = True
        f_rec = True if a_val.rec else False
        f_monitor = True if a_val.monitor else False
        self.name_lineedit.setText(a_val.name)
        self.rec_checkbox.setChecked(f_rec)
        self.monitor_checkbox.setChecked(f_monitor)
        self.vol_slider.setValue(int(a_val.vol * 10.0))
        self.stereo_combobox.setCurrentIndex(a_val.stereo + 1)
        self.output_mode_combobox.setCurrentIndex(a_val.sidechain)
        self.output_track_combobox.setCurrentIndex(a_val.output)
        self.suppress_updates = False

NO_AUDIO_INPUTS_INSTRUCTIONS = """\
No audio inputs available.  If you are using an audio device that inputs, press
the Hardware Settings button and ensure that the audio inputs control is set to
a number greater than 0.
"""

class AudioInputWidget:
    def __init__(self):
        self.layout = QGridLayout()
        self.inputs = []
        f_count = 0
        if "audioInputs" in util.DEVICE_SETTINGS:
            f_count = int(util.DEVICE_SETTINGS["audioInputs"])
        if f_count == 0:
            self.layout.addWidget(
                QLabel(NO_AUDIO_INPUTS_INSTRUCTIONS),
            )
            return
        f_labels = (
            _("Name"),
            _("Rec."),
            _("Mon."),
            _("Stereo"),
            _("Mode"),
            _("Output"),
            _("Gain"),
        )
        for f_i, f_label in zip(range(len(f_labels)), f_labels):
            self.layout.addWidget(QLabel(f_label), 0, f_i)
        for f_i in range(f_count):
            f_input = AudioInput(
                f_i,
                self.layout,
                self.callback,
                f_count - 1,
            )
            self.inputs.append(f_input)

    def get_inputs(self):
        f_result = AudioInputTracks()
        for f_i, f_input in zip(range(len(self.inputs)), self.inputs):
            f_result.add_track(f_i, f_input.get_value())
        return f_result

    def callback(self, a_notify):
        f_result = self.get_inputs()
        constants.DAW_PROJECT.save_audio_inputs(f_result)
        if a_notify:
            constants.DAW_PROJECT.ipc().save_audio_inputs()

    def active(self):
        return [x.get_value() for x in self.inputs
            if x.rec_checkbox.isChecked()]

    def open_project(self):
        f_audio_inputs = constants.DAW_PROJECT.get_audio_inputs()
        for k, v in f_audio_inputs.tracks.items():
            if k < len(self.inputs):
                self.inputs[k].set_value(v)

