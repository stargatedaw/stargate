from sglib.lib.util import *
from sgui.sgqt import *

from sglib import constants
from sglib.lib import util
from sglib.lib.translate import _


class TimePitchDialogWidget:
    def __init__(
        self,
        audio_item=None,
        modes=TIMESTRETCH_MODES,
        ps_pitch=False,
    ):
        self.ps_pitch = ps_pitch
        self.widget = QDialog()
        self.widget.setMaximumWidth(480)

        self.vlayout = QVBoxLayout(self.widget)
        self.start_hlayout = QHBoxLayout()
        self.vlayout.addLayout(self.start_hlayout)

        self.timestretch_hlayout = QHBoxLayout()
        self.time_pitch_gridlayout = QGridLayout()
        self.vlayout.addLayout(self.timestretch_hlayout)
        self.vlayout.addLayout(self.time_pitch_gridlayout)
        self.timestretch_hlayout.addWidget(QLabel(_("Mode:")))
        self.timestretch_mode = QComboBox()

        self.timestretch_mode.setMinimumWidth(240)
        self.timestretch_hlayout.addWidget(self.timestretch_mode)
        self.timestretch_mode.addItems(modes)
        self.timestretch_mode.currentIndexChanged.connect(
            self.timestretch_mode_changed,
        )
        self.pitch_label = QLabel("Pitch:")
        self.time_pitch_gridlayout.addWidget(self.pitch_label, 0, 0)
        self.pitch_shift = QDoubleSpinBox()
        self.pitch_controls = (self.pitch_label, self.pitch_shift)
        self.pitch_shift.setToolTip('The pitch adjustment, in semitones')
        self.pitch_shift.setRange(-36, 36)
        self.pitch_shift.setDecimals(6)
        self.pitch_shift.setValue(0.0)
        self.time_pitch_gridlayout.addWidget(self.pitch_shift, 0, 1)

        self.pitch_shift_end_checkbox = QCheckBox(_("End:"))
        self.pitch_shift_end_checkbox.setToolTip(
            'SBSMS only.  Check this box to use a pitch bend from the '
            'start of the item to the end'
        )
        self.pitch_shift_end_checkbox.toggled.connect(
            self.pitch_end_mode_changed)
        self.time_pitch_gridlayout.addWidget(
            self.pitch_shift_end_checkbox, 0, 2)
        self.pitch_shift_end = QDoubleSpinBox()
        self.pitch_shift_end.setToolTip(
            'SBSMS only.  The pitch adjustment at the end of the audio item, '
            'the pitch will gradually shift from the starting pitch '
            'adjustment to the end value'
        )
        self.pitch_shift_end.setRange(-36, 36)
        self.pitch_shift_end.setDecimals(6)
        self.pitch_shift_end.setValue(0.0)
        self.time_pitch_gridlayout.addWidget(self.pitch_shift_end, 0, 3)

        self.time_label = QLabel(_("Time:"))
        self.time_pitch_gridlayout.addWidget(self.time_label, 1, 0)
        self.timestretch_amt = QDoubleSpinBox()
        self.time_controls = (self.time_label, self.timestretch_amt)
        self.timestretch_amt.setToolTip(
            'The time stretch amount.  2.0 doubles the length of the item, '
            '0.5 halfs the length of the item,  Note that the algorithms are '
            'not precise, and actual length may vary'
        )
        self.timestretch_amt.setRange(0.1, 200.0)
        self.timestretch_amt.setDecimals(6)
        self.timestretch_amt.setValue(1.0)
        self.timestretch_amt.setSingleStep(0.1)
        self.time_pitch_gridlayout.addWidget(self.timestretch_amt, 1, 1)

        self.crispness_layout = QHBoxLayout()
        self.vlayout.addLayout(self.crispness_layout)
        self.crispness_label = QLabel(_("Crispness"))
        self.crispness_layout.addWidget(self.crispness_label)
        self.crispness_combobox = QComboBox()
        self.crispness_combobox.setToolTip(
            'Rubberband crispness settings, see the Rubberband documentation'
        )
        self.crispness_combobox.addItems(CRISPNESS_SETTINGS)
        self.crispness_combobox.setCurrentIndex(5)
        self.crispness_layout.addWidget(self.crispness_combobox)

        self.timestretch_amt_end_checkbox = QCheckBox(_("End:"))
        self.timestretch_amt_end_checkbox.setToolTip(
            'SBSMS-only.  Check this box to gradually shift the rate of '
            'stretching from the start of the audio item to the end'
        )
        self.timestretch_amt_end_checkbox.toggled.connect(
            self.timestretch_end_mode_changed)
        self.time_pitch_gridlayout.addWidget(
            self.timestretch_amt_end_checkbox, 1, 2)
        self.timestretch_amt_end = QDoubleSpinBox()
        self.timestretch_amt_end.setToolTip(
            'SBSMS only.  The end time stretch amount.  Time stretch amount '
            'will be gradually bent from the start value to the end value'
        )
        self.timestretch_amt_end.setRange(0.2, 4.0)
        self.timestretch_amt_end.setDecimals(6)
        self.timestretch_amt_end.setValue(1.0)
        self.timestretch_amt_end.setSingleStep(0.1)
        self.time_pitch_gridlayout.addWidget(self.timestretch_amt_end, 1, 3)

        self.end_controls = (
            self.pitch_shift_end_checkbox,
            self.pitch_shift_end,
            self.timestretch_amt_end_checkbox,
            self.timestretch_amt_end,
        )
        self.crispness_controls = (
            self.crispness_label,
            self.crispness_combobox,
        )

        if audio_item:
            self.timestretch_mode.setCurrentIndex(audio_item.time_stretch_mode)
            self.pitch_shift.setValue(float(audio_item.pitch_shift))
            self.pitch_shift_end_checkbox.setChecked(
                audio_item.pitch_shift != audio_item.pitch_shift_end
            )
            self.pitch_shift_end.setValue(float(audio_item.pitch_shift_end))
            self.timestretch_amt.setValue(float(audio_item.timestretch_amt))
            self.crispness_combobox.setCurrentIndex(audio_item.crispness)
            self.timestretch_amt_end.setValue(
                float(audio_item.timestretch_amt_end),
            )

        self.timestretch_mode_changed()

        self.timestretch_mode.currentIndexChanged.connect(
            self.timestretch_changed)
        self.pitch_shift.valueChanged.connect(self.timestretch_changed)
        self.pitch_shift_end.valueChanged.connect(self.timestretch_changed)
        self.timestretch_amt.valueChanged.connect(self.timestretch_changed)
        self.timestretch_amt_end.valueChanged.connect(self.timestretch_changed)
        self.crispness_combobox.currentIndexChanged.connect(
            self.timestretch_changed,
        )

        self.ok_layout = QHBoxLayout()
        self.ok = QPushButton(_("OK"))
        self.ok.pressed.connect(self.ok_handler)
        self.ok_layout.addWidget(self.ok)
        self.cancel = QPushButton(_("Cancel"))
        self.cancel.pressed.connect(self.widget.close)
        self.ok_layout.addWidget(self.cancel)
        self.vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        self.vlayout.addLayout(self.ok_layout)

        self.last_open_dir = HOME

    def hide_controls(
        self,
        end=False,
        crisp=False,
        pitch=False,
        _time=False,
    ):
        for control in self.end_controls:
            if end:
                control.show()
            else:
                control.hide()
        for control in self.crispness_controls:
            if crisp:
                control.show()
            else:
                control.hide()
        for control in self.pitch_controls:
            if pitch:
                control.show()
            else:
                control.hide()
        for control in self.time_controls:
            if _time:
                control.show()
            else:
                control.hide()

    def timestretch_end_mode_changed(self, a_val=None):
        if not self.timestretch_amt_end_checkbox.isChecked():
            self.timestretch_amt_end.setValue(
                float(self.timestretch_amt.value()),
            )

    def pitch_end_mode_changed(self, a_val=None):
        if not self.pitch_shift_end_checkbox.isChecked():
            self.pitch_shift_end.setValue(
                float(self.pitch_shift.value()),
            )

    def end_mode_changed(self, a_val=None):
        self.end_mode_checkbox.setChecked(True)

    def timestretch_changed(self, a_val=None):
        if not self.pitch_shift_end_checkbox.isChecked():
            self.pitch_shift_end.setValue(
                float(self.pitch_shift.value()),
            )
        if not self.timestretch_amt_end_checkbox.isChecked():
            self.timestretch_amt_end.setValue(
                float(self.timestretch_amt.value()),
            )

    def timestretch_mode_changed(self, a_val=None):
        a_val = util.TIMESTRETCH_INDEXES[
            str(self.timestretch_mode.currentText())
        ]
        if a_val == 0:
            self.hide_controls()
            self.pitch_shift.setValue(0.0)
            self.pitch_shift_end.setValue(0.0)
            self.timestretch_amt.setValue(1.0)
            self.timestretch_amt_end.setValue(1.0)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
        elif a_val == 1:
            self.hide_controls(pitch=True)
            self.timestretch_amt.setValue(1.0)
            self.timestretch_amt_end.setValue(1.0)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
        elif a_val == 2:
            self.hide_controls(_time=True)
            self.pitch_shift.setValue(0.0)
            self.pitch_shift_end.setValue(0.0)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
        elif a_val == 3 or a_val == 4:
            self.hide_controls(pitch=True, _time=True, crisp=True)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setChecked(False)
        elif a_val == 5:
            self.hide_controls(pitch=True, _time=True, end=True)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
        elif a_val == 6:
            # TODO Stargate v2: Deprecate pitch completely for Paulstretch
            self.hide_controls(pitch=self.ps_pitch, _time=True)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)


    def ok_handler(self):
        raise NotImplementedError

