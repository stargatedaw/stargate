from . import _shared
from sglib.math import (
    clip_value,
    pitch_to_hz,
    pitch_to_ratio,
    ratio_to_pitch,
)
from .knob import PixmapKnob
from .nested_combobox import NestedComboBox
from .note_selector import NoteSelectorWidget
from sgui import shared as glbl_shared
from sglib.lib import util
from sglib.lib.translate import _
from sglib.log import LOG
from sgui.sgqt import *
import collections
import math
from typing import Optional, Tuple


LAST_TEMPO_COMBOBOX_INDEX = 2

class GridLayoutControl:
    def add_to_grid_layout(
            self,
            a_layout,
            a_x,
            a_alignment=QtCore.Qt.AlignmentFlag.AlignHCenter,
            a_row=0,
        ):
        row_offset = a_row * 3
        if self.name_label is not None:
            if a_alignment:
                a_layout.addWidget(
                    self.name_label,
                    row_offset,
                    a_x,
                    alignment=a_alignment,
                )
            else:
                a_layout.addWidget(
                    self.name_label,
                    row_offset,
                    a_x,
                )
        if a_alignment:
            a_layout.addWidget(
                self.control,
                row_offset + 1,
                a_x,
                alignment=a_alignment,
            )
        else:
            a_layout.addWidget(
                self.control,
                row_offset + 1,
                a_x,
            )
        if self.value_label is not None:
            if a_alignment:
                a_layout.addWidget(
                    self.value_label,
                    row_offset + 2,
                    a_x,
                    alignment=a_alignment,
                )
            else:
                a_layout.addWidget(
                    self.value_label,
                    row_offset + 2,
                    a_x,
                )

class AbstractUiControl(GridLayoutControl):
    def __init__(
        self,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
        a_default_value=None,
        min_text=None,
        max_text=None,
        text_lookup=None,  # Required to be a tuple if KC_TEXT
        value_multiplier=None,
        control_res=127.,
    ):
        self.control_res = control_res
        self.value_multiplier = value_multiplier
        self.min_text = min_text
        self.max_text = max_text
        if a_label is None:
            self.name_label = None
        else:
            self.name_label = QLabel(str(a_label))
            self.name_label.setObjectName("plugin_name_label")
            self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.name_label.setMinimumWidth(15)
        self.undo_history = collections.deque()
        self.value_set = 0
        self.port_num = int(a_port_num)
        self.val_callback = a_val_callback
        self.rel_callback = a_rel_callback
        self.suppress_changes = False
        self.val_conversion = a_val_conversion
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)
        self.default_value = a_default_value
        self.ratio_callback = None
        self.midi_learn_callback = None

    def set_midi_learn(self, a_callback, a_get_cc_map):
        self.midi_learn_callback = a_callback
        self.get_cc_map = a_get_cc_map

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def set_value(self, a_val, a_changed=False):
        f_val = int(a_val)
        if self.value_set < 2:
            self.value_set += 1
            self.add_undo_history(f_val)
        if not a_changed:
            self.suppress_changes = True
        self.control.setValue(f_val)
        self.control_value_changed(f_val)
        self.suppress_changes = False

    def get_value(self):
        return self.control.value()

    def set_min_max(self, a_min, a_max):
        self._min = a_min;
        self._max = a_max;
        self._add = 0.0 - a_min;
        self._mult = ((a_max - a_min) / self.control_res);

    def add_undo_history(self, value):
        self.undo_history.append(value)
        if len(self.undo_history) > 10:
            self.undo_history.popleft()

    def control_released(self):
        value = self.control.value()
        self.add_undo_history(value)
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, value)

    def hide(self):
        self.name_label.hide()
        self.control.hide()
        if self.value_label:
            self.value_label.hide()

    def show(self):
        self.name_label.show()
        self.control.show()
        if self.value_label:
            self.value_label.show()

    def value_conversion(self, a_value):
        """ Convert a control value to a human-readable string """
        if self.min_text and a_value == self.control.minimum():
            return self.min_text
        elif self.max_text and a_value == self.control.maximum():
            return self.max_text
        elif self.val_conversion == _shared.KC_TEXT:
            return self.text_lookup[a_value]

        f_value = float(a_value)
        if self.value_multiplier:
            f_value *= self.value_multiplier
        f_dec_value = 0.0
        if self.val_conversion == _shared.KC_NONE:
            return None
        elif self.val_conversion in (
            _shared.KC_DECIMAL,
            _shared.KC_TIME_DECIMAL,
            _shared.KC_HZ_DECIMAL
        ):
            return str(round(f_value * .01, 2))
        elif self.val_conversion in (
            _shared.KC_INTEGER,
            _shared.KC_INT_PITCH,
            _shared.KC_MILLISECOND,
        ):
            return str(int(f_value))
        elif self.val_conversion == _shared.KC_PITCH:
            f_val = int(pitch_to_hz(f_value))
            if f_val >= 1000:
                f_val = str(round(f_val * 0.001, 1)) + "k"
            return str(f_val)
        elif self.val_conversion == _shared.KC_127_PITCH:
            f_val = int(
                pitch_to_hz(
                    (f_value * 0.818897638) + 20.0
                )
            )
            if f_val >= 1000:
                f_val = str(round(f_val * 0.001, 1)) + "k"
            return (str(f_val))
        elif self.val_conversion == _shared.KC_127_PITCH_MIN_MAX:
            mult = (self._max - self._min) / self.control_res
            pitch = (f_value * mult) + self._min
            f_val = int(pitch_to_hz(pitch))
            if f_val >= 1000:
                f_val = str(round(f_val * 0.001, 1)) + "k"
            return str(f_val)
        elif self.val_conversion == _shared.KC_127_ZERO_TO_X:
            f_dec_value = (float(f_value) * self._mult) - self._add
            f_dec_value = ((int)(f_dec_value * 10.0)) * 0.1
            return str(round(f_dec_value, 2))
        elif self.val_conversion == _shared.KC_127_ZERO_TO_X_INT:
            f_dec_value = (float(f_value) * self._mult) - self._add
            return str(int(f_dec_value))
        elif self.val_conversion == _shared.KC_LOG_TIME:
            f_dec_value = float(f_value) * 0.01
            f_dec_value = f_dec_value * f_dec_value
            return str(round(f_dec_value, 2))
        elif self.val_conversion == _shared.KC_TENTH:
            return str(round(f_value * .1, 1))

        raise ValueError(
            f"Unknown self.val_conversion: {self.val_conversion}",
        )

    def control_value_changed(self, a_value=None):
        if not self.suppress_changes and self.val_callback:
            self.val_callback(self.port_num, self.control.value())

        if self.value_label is not None:
            self.value_label.setText(
                self.value_conversion(self.control.value()),
            )

    def set_value_dialog(self):
        def ok_handler(a_self=None, a_val=None):
            self.control.setValue(f_spinbox.value())
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setWindowTitle(_("Set Value"))
        vlayout = QVBoxLayout(f_dialog)
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_layout.addWidget(QLabel(_("Value:")), 3, 0)
        f_spinbox = QSpinBox()
        f_spinbox.setToolTip(
            'The raw value of the controller.  This is the underlying value, '
            'not the display value'
        )
        f_spinbox.setMinimum(self.control.minimum())
        f_spinbox.setMaximum(self.control.maximum())
        f_spinbox.setValue(self.control.value())
        f_layout.addWidget(f_spinbox, 3, 1)
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(ok_cancel_layout)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        ok_cancel_layout.addWidget(f_ok_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def tempo_sync_dialog(self):
        def sync_button_pressed(a_self=None):
            global LAST_TEMPO_COMBOBOX_INDEX
            f_frac = 1.0
            f_switch = (f_beat_frac_combobox.currentIndex())
            f_dict = {0 : 0.25, 1 : 0.33333, 2 : 0.5, 3 : 0.666666, 4 : 0.75,
                      5 : 1.0, 6 : 2.0, 7 : 4.0}
            f_frac = f_dict[f_switch]
            f_seconds_per_beat = 60 / (f_spinbox.value())
            if self.val_conversion == _shared.KC_TIME_DECIMAL:
                f_result = round(f_seconds_per_beat * f_frac * 100)
            elif self.val_conversion == _shared.KC_HZ_DECIMAL:
                f_result = round((1.0 / (f_seconds_per_beat * f_frac)) * 100)
            elif self.val_conversion == _shared.KC_LOG_TIME:
                f_result = round(math.sqrt(f_seconds_per_beat * f_frac) * 100)
            elif self.val_conversion == _shared.KC_MILLISECOND:
                f_result = round(f_seconds_per_beat * f_frac * 1000)
            f_result = clip_value(
                f_result, self.control.minimum(), self.control.maximum())
            self.control.setValue(f_result)
            LAST_TEMPO_COMBOBOX_INDEX = f_beat_frac_combobox.currentIndex()
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setWindowTitle(_("Tempo Sync"))
        vlayout = QVBoxLayout(f_dialog)
        f_groupbox_layout = QGridLayout()
        vlayout.addLayout(f_groupbox_layout)
        f_spinbox = QDoubleSpinBox()
        f_spinbox.setToolTip('The tempo to sync to in BPM')
        f_spinbox.setDecimals(1)
        f_spinbox.setRange(60., 200.)
        f_spinbox.setSingleStep(0.1)
        f_spinbox.setValue(_shared.TEMPO)
        f_beat_fracs = ["1/16", "1/12", "1/8", "2/12", "3/16",
                        "1/4", "2/4", "4/4"]
        f_beat_frac_combobox = QComboBox()
        f_beat_frac_combobox.setToolTip(
            'The fraction of a beat, at the set tempo, to sync this control to'
        )
        f_beat_frac_combobox.setMinimumWidth(75)
        f_beat_frac_combobox.addItems(f_beat_fracs)
        f_beat_frac_combobox.setCurrentIndex(LAST_TEMPO_COMBOBOX_INDEX)
        f_sync_button = QPushButton(_("Sync"))
        f_sync_button.pressed.connect(sync_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_groupbox_layout.addWidget(QLabel(_("BPM")), 0, 0)
        f_groupbox_layout.addWidget(f_spinbox, 1, 0)
        f_groupbox_layout.addWidget(QLabel("Length"), 0, 1)
        f_groupbox_layout.addWidget(f_beat_frac_combobox, 1, 1)
        ok_cancel_layout = QHBoxLayout()
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        vlayout.addLayout(ok_cancel_layout)
        ok_cancel_layout.addWidget(f_sync_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def set_note_dialog(self):
        def ok_button_pressed():
            f_value = f_note_selector.get_value()
            f_value = clip_value(
                f_value,
                self.control.minimum(),
                self.control.maximum(),
            )
            self.set_value(f_value, a_changed=True)
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Note"))
        f_vlayout = QVBoxLayout(f_dialog)
        f_note_selector = NoteSelectorWidget(0, None, None)
        f_note_selector.set_value(self.get_value())
        f_vlayout.addWidget(f_note_selector.widget)
        f_vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_cancel_layout = QHBoxLayout()
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_vlayout.addLayout(f_ok_cancel_layout)
        f_dialog.exec()

    def set_ratio_dialog(self):
        def ok_button_pressed():
            f_value = ratio_to_pitch(f_ratio_spinbox.value())
            if self.ratio_callback:
                f_int = round(f_value)
                self.set_value(f_int, True)
                f_frac = round((f_value - f_int) * 100)
                self.ratio_callback(f_frac, True)
            else:
                self.set_value(f_value, True)
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Ratio"))
        vlayout = QVBoxLayout(f_dialog)
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_layout.addWidget(QLabel(_("Ratio:")), 0, 0)
        f_ratio_spinbox = QDoubleSpinBox()

        f_min = pitch_to_ratio(self.control.minimum())
        f_max = pitch_to_ratio(self.control.maximum())
        f_ratio_spinbox.setRange(f_min, round(f_max))
        f_ratio_spinbox.setDecimals(4)
        f_ratio_spinbox.setValue(
            pitch_to_ratio(self.get_value()),
        )
        f_layout.addWidget(f_ratio_spinbox, 0, 1)

        ok_cancel_layout = QHBoxLayout()
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        vlayout.addLayout(ok_cancel_layout)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        ok_cancel_layout.addWidget(f_ok_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def set_octave_dialog(self):
        def ok_button_pressed():
            f_value = f_spinbox.value() * 12
            self.set_value(f_value, True)
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Octave"))
        vlayout = QVBoxLayout(f_dialog)
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_layout.addWidget(QLabel(_("Octave:")), 0, 0)
        f_spinbox = QSpinBox()
        f_min = self.control.minimum() // 12
        f_max = self.control.maximum() // 12
        f_spinbox.setRange(int(f_min), int(f_max))
        f_spinbox.setValue(int(self.get_value() // 12))
        f_layout.addWidget(f_spinbox, 0, 1)
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(ok_cancel_layout)
        ok_cancel_layout.addWidget(f_ok_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def copy_automation(self):
        f_value = ((self.get_value() - self.control.minimum()) /
                  (self.control.maximum() - self.control.minimum())) * 127.0
        glbl_shared.CC_CLIPBOARD = clip_value(f_value, 0.0, 127.0)

    def paste_automation(self):
        f_frac = glbl_shared.CC_CLIPBOARD / 127.0
        f_frac = clip_value(f_frac, 0.0, 1.0)
        f_min = self.control.minimum()
        f_max = self.control.maximum()
        f_value = round(((f_max - f_min) * f_frac) + f_min)
        self.set_value(f_value, True)

    def midi_learn(self):
        self.midi_learn_callback(self)

    def cc_menu_triggered(self, a_item):
        self.midi_learn_callback(self, a_item.cc_num)

    def cc_range_dialog(self, a_item):
        f_cc = a_item.cc_num

        def get_zero_to_one(a_val):
            a_val = float(a_val)
            f_min = float(self.control.minimum())
            f_max = float(self.control.maximum())
            f_range = f_max - f_min
            f_result = (a_val - f_min) / f_range
            return round(f_result, 6)

        def get_real_value(a_val):
            a_val = float(a_val)
            f_min = float(self.control.minimum())
            f_max = float(self.control.maximum())
            f_range = f_max - f_min
            f_result = (a_val * f_range) + f_min
            return int(round(f_result))

        def ok_hander():
            f_low = get_zero_to_one(f_low_spinbox.value())
            f_high = get_zero_to_one(f_high_spinbox.value())
            LOG.info((f_low, f_high))
            self.midi_learn_callback(self, f_cc, f_low, f_high)
            f_dialog.close()

        f_cc_map = self.get_cc_map()
        f_default_low, f_default_high = (
            int(get_real_value(x))
            for x in f_cc_map[f_cc].ports[self.port_num]
        )

        f_dialog = QDialog(self.control)
        f_dialog.setWindowTitle(_("Set Range for CC"))
        f_layout = QVBoxLayout(f_dialog)
        f_spinbox_layout = QHBoxLayout()
        f_layout.addLayout(f_spinbox_layout)
        f_spinbox_layout.addWidget(QLabel(_("Low")))
        f_low_spinbox = QSpinBox()
        f_low_spinbox.setToolTip(
            'This is the control value that will be set when a CC event with '
            'value 0 is sent to this plugin'
        )
        f_low_spinbox.setRange(self.control.minimum(), self.control.maximum())
        f_low_spinbox.setValue(f_default_low)
        f_spinbox_layout.addWidget(f_low_spinbox)
        f_spinbox_layout.addWidget(QLabel(_("High")))
        f_high_spinbox = QSpinBox()
        f_high_spinbox.setToolTip(
            'This is the control value that will be set when a CC event with '
            'value 127 is sent to this plugin'
        )
        f_high_spinbox.setRange(self.control.minimum(), self.control.maximum())
        f_high_spinbox.setValue(f_default_high)
        f_spinbox_layout.addWidget(f_high_spinbox)
        f_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_hander)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def undo_action_callback(self, a_action):
        value = a_action.control_value
        self.set_value(value, True)
        self.add_undo_history(value)

    def contextMenuEvent(self, a_event):
        f_menu = QMenu(self.control)
        if self.undo_history:
            undo_menu = QMenu(_("Undo"), f_menu)
            f_menu.addMenu(undo_menu)
            undo_menu.triggered.connect(self.undo_action_callback)
            for x in reversed(self.undo_history):
                value = self.value_conversion(x)
                if value:
                    action = undo_menu.addAction(self.value_conversion(x))
                    if action is not None: # Not sure why this happens
                        action.control_value = x

        if self.midi_learn_callback:
            f_ml_action = QAction(_("MIDI Learn"), f_menu)
            f_ml_action.setToolTip(
                'MIDI Learn: Go to the Hardware tab, enable your device and '
                'route it to this track. Use this action, move a control on '
                'your device to pair the plugin and hardware controls'
            )
            f_menu.addAction(f_ml_action)
            f_ml_action.triggered.connect(self.midi_learn)
            f_cc_menu = QMenu(_("CCs"), f_menu)
            f_menu.addMenu(f_cc_menu)
            f_cc_menu.triggered.connect(self.cc_menu_triggered)
            f_cc_map = self.get_cc_map()
            if f_cc_map:
                f_range_menu = QMenu(_("Set Range for CC"), f_menu)
                f_range_menu.triggered.connect(self.cc_range_dialog)
                f_menu.addMenu(f_range_menu)
            for f_i in range(1, 128):
                f_cc_action = f_cc_menu.addAction(str(f_i))
                f_cc_action.cc_num = f_i
                f_cc_action.setCheckable(True)
                if f_i in f_cc_map and f_cc_map[f_i].has_port(self.port_num):
                    f_cc_action.setChecked(True)
                    f_action = f_range_menu.addAction(str(f_i))
                    f_action.cc_num = f_i
            f_menu.addSeparator()

        f_reset_action = QAction(_("Reset to Default Value"), f_menu)
        f_reset_action.setToolTip(
            'Reset this control to the default value that it has when you '
            'first open the plugin without selecting a preset'
        )
        f_menu.addAction(f_reset_action)
        f_reset_action.triggered.connect(self.reset_default_value)

        f_set_value_action = QAction(_("Set Raw Controller Value..."), f_menu)
        f_menu.addAction(f_set_value_action)
        f_set_value_action.setToolTip(
            'Open a dialog to set the raw value of the control by typing it'
        )
        f_set_value_action.triggered.connect(self.set_value_dialog)

        f_menu.addSeparator()

        f_copy_automation_action = QAction(_("Copy"), f_menu)
        f_menu.addAction(f_copy_automation_action)
        f_copy_automation_action.setToolTip(
            'Copy the control value to the clipboard. Can be pasted to other '
            'controls, sequencer automation, or MIDI CCs. Use this to listen '
            'to controller positions and convert to automation'
        )
        f_copy_automation_action.triggered.connect(self.copy_automation)

        if glbl_shared.CC_CLIPBOARD:
            f_paste_automation_action = QAction(_("Paste"), f_menu)
            f_menu.addAction(f_paste_automation_action)
            f_paste_automation_action.setToolTip(
                'Paste a control value previously copied using the copy '
                'action. You can also paste these values into the CCs item '
                'editor and sequencer automation'
            )
            f_paste_automation_action.triggered.connect(self.paste_automation)

        f_menu.addSeparator()

        if self.val_conversion in (
            _shared.KC_TIME_DECIMAL,
            _shared.KC_HZ_DECIMAL,
            _shared.KC_LOG_TIME,
            _shared.KC_MILLISECOND,
        ):
            f_tempo_sync_action = QAction(_("Tempo Sync..."), f_menu)
            f_menu.addAction(f_tempo_sync_action)
            f_tempo_sync_action.setToolTip(
                'Open a dialog to sync the control value to an arbirary '
                'tempo'
            )
            f_tempo_sync_action.triggered.connect(self.tempo_sync_dialog)
        if self.val_conversion == _shared.KC_PITCH:
            f_set_note_action = QAction(_("Set to Note..."), f_menu)
            f_menu.addAction(f_set_note_action)
            f_set_note_action.setToolTip(
                'Open a dialog to set the control value to an arbitrary '
                'western musical note'
            )
            f_set_note_action.triggered.connect(self.set_note_dialog)
        if self.val_conversion == _shared.KC_INT_PITCH:
            f_set_ratio_action = f_menu.addAction(_("Set to Ratio..."))
            f_set_ratio_action.triggered.connect(self.set_ratio_dialog)
            f_set_octave_action = f_menu.addAction(_("Set to Octave..."))
            f_set_octave_action.triggered.connect(self.set_octave_dialog)

        f_menu.exec(QCursor.pos())

class MultiplexedControl(GridLayoutControl):
    """ A control whose name label is a QComboBox or combobox_control

        If the name_label is a custom combobox_control, the selected state
        will be sent to the engine and stored in the plugin state file,
        as long as the selected item is not in @excluded_items
    """
    def __init__(
        self,
        controls: Tuple[AbstractUiControl],
        size: Optional[int]=None,
        name_label: Optional[QComboBox]=None,
        tooltip=None,
    ):
        self.controls = controls

        if name_label:
            self.name_label = name_label
        else:
            items = [str(x.name_label.text()) for x in controls]
            self.name_label = QComboBox()
            self.name_label.addItems(items)
            self.name_label.setToolTip(tooltip)
        self.name_label.currentIndexChanged.connect(self.index_changed)
        self.name_label.setObjectName("plugin_name_label")

        stylesheet = "background-color: transparent;"
        self.control = QStackedWidget()
        if size is not None:
            self.control.setFixedSize(size, size)
        self.control.setStyleSheet(stylesheet)
        self.value_label = QStackedWidget()
        self.value_label.setStyleSheet(stylesheet)
        for control in controls:
            self.control.addWidget(control.control)
            self.value_label.addWidget(control.value_label)

    def index_changed(self, index):
        self.control.setCurrentIndex(index)
        self.value_label.setCurrentIndex(index)

    def get_value(self):
        index = self.name_label.currentIndex()
        return self.controls[index].get_value()

    def set_value(self, value, changed=False):
        index = self.name_label.currentIndex()
        return self.controls[index].set_value(value, changed)


class null_control:
    """ For controls with no visual representation,
        ie: controls that share a UI widget
        depending on selected index, so that they can participate
        normally in the data representation mechanisms
    """
    def __init__(
        self,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_default_val,
        a_port_dict,
        a_preset_mgr=None,
    ):
        self.name_label = None
        self.value_label = None
        self.port_num = int(a_port_num)
        self.val_callback = a_val_callback
        self.rel_callback = a_rel_callback
        self.suppress_changes = False
        self.value = a_default_val
        a_port_dict[self.port_num] = self
        self.default_value = a_default_val
        self.control_callback = None
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def get_value(self):
        return self.value

    def set_value(self, a_val, a_changed=False):
        self.value = a_val
        if self.control_callback is not None:
            self.control_callback.set_value(self.value)
        if a_changed:
            self.control_value_changed(a_val)

    def set_control_callback(self, a_callback=None):
        self.control_callback = a_callback

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.value)

    def control_value_changed(self, a_value):
        self.val_callback(self.port_num, self.value)

    def set_midi_learn(self, a_ignored, a_ignored2):
        pass

class knob_control(AbstractUiControl):
    def __init__(
        self,
        a_size,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_min_val,
        a_max_val,
        a_default_val,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
        knob_kwargs={},
        min_text=None,
        max_text=None,
        text_lookup=None,
        value_multiplier=None,
        tooltip=None,
    ):
        """
            a_size: The size of the knob (x or y), in pixels
            a_label: The text to display as the name label
            a_port_num: The port number of this control
            a_rel_callback: The callback function on knob release
            a_val_callback: The callback function on knob value changed
            a_min_val: The minimum value of this knob
            a_max_val: The maximum value of this knob
            a_default_val: The default value of this knob
            a_val_conversion:
                The conversion algorithm from raw knob value to the
                value label
            a_port_dict: The plugin port dictionary
            a_preset_mgr: The plugin preset manager
            knob_kwargs: Keyword arguments to pass to PixmapKnob(...)
            min_text:
                Special text to display on the value label when it is at
                it's minimum value
            max_text:
                Special text to display on the value label when it is at
                it's maximum value
            text_lookup:
                A tuple of strings to display as the knob value label.  If
                not None, a_min_val must be 0, a_max_val must be
                len(text_lookup) - 1, and a_val_conversion=_shared.KC_TEXT.
            value_multiplier:
                Number to multiply the raw knob value by before converting
                to the value label text
        """
        if a_val_conversion == _shared.KC_TEXT:
            assert (
                text_lookup
                and
                a_min_val == 0
                and a_max_val == len(text_lookup) - 1
            ), (text_lookup, a_min_val, a_max_val)
        self.control = PixmapKnob(
            a_size,
            a_min_val,
            a_max_val,
            **knob_kwargs
        )
        self.control.setToolTip(tooltip)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.sliderReleased.connect(self.control_released)
        self.control.contextMenuEvent = self.contextMenuEvent
        self.value_label = QLabel("")
        self.value_label.setObjectName("plugin_value_label")
        self.value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumWidth(15)
        AbstractUiControl.__init__(
            self,
            a_label,
            a_port_num,
            a_rel_callback,
            a_val_callback,
            a_val_conversion,
            a_port_dict,
            a_preset_mgr,
            a_default_val,
            min_text,
            max_text,
            text_lookup,
            value_multiplier=value_multiplier,
        )
        self.set_value(a_default_val)


class slider_control(AbstractUiControl):
    def __init__(
        self,
        a_orientation,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_min_val,
        a_max_val,
        a_default_val,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
        min_text=None,
        max_text=None,
        value_multiplier=None,
        tooltip=None,
    ):
        self.control = QSlider(a_orientation)
        self.control.contextMenuEvent = self.contextMenuEvent
        self.control.setRange(int(a_min_val), int(a_max_val))
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.sliderReleased.connect(self.control_released)
        self.control.setToolTip(tooltip)
        self.value_label = QLabel("")
        self.value_label.setObjectName("plugin_value_label")
        self.value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumWidth(15)
        AbstractUiControl.__init__(
            self,
            a_label,
            a_port_num,
            a_rel_callback,
            a_val_callback,
            a_val_conversion,
            a_port_dict,
            a_preset_mgr,
            a_default_val,
            min_text,
            max_text,
            value_multiplier,
        )
        self.set_value(a_default_val)


class spinbox_control(AbstractUiControl):
    def __init__(
        self,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_min_val,
        a_max_val,
        a_default_val,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
        tooltip=None,
    ):
        AbstractUiControl.__init__(
            self,
            a_label,
            a_port_num,
            a_rel_callback,
            a_val_callback,
            a_val_conversion,
            a_port_dict,
            a_preset_mgr,
            a_default_val,
        )
        self.control = QSpinBox()
        self.widget = self.control
        self.control.setRange(int(a_min_val), int(a_max_val))
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.valueChanged.connect(self.control_released)
        self.control.setToolTip(tooltip)
        self.value_label = None
        self.set_value(a_default_val)


class doublespinbox_control(AbstractUiControl):
    def __init__(
        self,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_min_val,
        a_max_val,
        a_default_val,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
        tooltip=None,
    ):
        AbstractUiControl.__init__(
            self,
            a_label,
            a_port_num,
            a_rel_callback,
            a_val_callback,
            a_val_conversion,
            a_port_dict,
            a_preset_mgr,
            a_default_val,
        )
        self.control = QDoubleSpinBox()
        self.widget = self.control
        self.control.setRange(float(a_min_val), float(a_max_val))
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.valueChanged.connect(self.control_released)
        self.control.setToolTip(tooltip)
        self.value_label = None
        self.set_value(a_default_val)


class checkbox_control(AbstractUiControl):
    def __init__(
        self,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_preset_mgr=None,
        a_default=0,
        tooltip=None,
    ):
        AbstractUiControl.__init__(
            self,
            None,
            a_port_num,
            a_rel_callback,
            a_val_callback,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            a_default_value=a_default,
        )
        self.control = QCheckBox(a_label)
        if a_default:
            self.control.setChecked(True)
        self.widget = self.control
        self.control.stateChanged.connect(self.control_value_changed)
        self.control.setToolTip(tooltip)
        #self.control.stateChanged.connect(self.control_released)
        self.value_label = None
        self.suppress_changes = False

    def control_value_changed(self, a_val=None):
        if not self.suppress_changes:
            self.val_callback(self.port_num, self.get_value())

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.get_value())

    def set_value(self, a_val, a_changed=False):
        self.suppress_changes = True
        f_val = int(a_val)
        if f_val == 0:
            self.control.setChecked(False)
        else:
            self.control.setChecked(True)
        self.suppress_changes = False
        if a_changed:
            self.control_value_changed()

    def get_value(self):
        if self.control.isChecked():
            return 1
        else:
            return 0


class combobox_control(AbstractUiControl):
    def __init__(
        self,
        a_size,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_items_list=[],
        a_port_dict=None,
        a_default_index=None,
        a_preset_mgr=None,
        tooltip=None,
    ):
        self.suppress_changes = True
        self.name_label = QLabel(str(a_label))
        self.name_label.setObjectName("plugin_name_label")
        self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.control = QComboBox()
        self.control.wheelEvent = self.wheel_event
        self.widget = self.control
        self.control.setMinimumWidth(a_size)
        self.control.addItems(a_items_list)
        self.control.setCurrentIndex(0)
        self.control.currentIndexChanged.connect(self.control_value_changed)
        self.control.setToolTip(tooltip)
        self.port_num = int(a_port_num)
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.suppress_changes = False
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        self.value_label = None
        self.default_value = a_default_index
        if a_default_index is not None:
            self.set_value(a_default_index)
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def wheel_event(self, a_event=None):
        pass

    def control_value_changed(self, a_val):
        if not self.suppress_changes:
            self.val_callback(self.port_num, a_val)
            if self.rel_callback is not None:
                self.rel_callback(self.port_num, a_val)

    def set_value(self, a_val, a_changed=False):
        if not a_changed:
            self.suppress_changes = True
        self.control.setCurrentIndex(int(a_val))
        self.suppress_changes = False

    def get_value(self):
        return self.control.currentIndex()


class NestedComboboxControl(AbstractUiControl):
    def __init__(
        self,
        a_size,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        lookup,
        items,
        a_port_dict=None,
        a_default_index=None,
        a_preset_mgr=None,
        tooltip=None,
    ):
        self.suppress_changes = True
        self.name_label = QLabel(str(a_label))
        self.name_label.setObjectName("plugin_name_label")
        self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.control = NestedComboBox(
            lookup,
        )
        self.control.wheelEvent = self.wheel_event
        self.widget = self.control
        self.control.setMinimumWidth(a_size)
        self.control.addItems(items)
        self.control.setCurrentIndex(0)
        self.control.currentIndexChanged_connect(
            self.control_value_changed,
        )
        self.control.setToolTip(tooltip)
        self.port_num = int(a_port_num)
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.suppress_changes = False
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        self.value_label = None
        self.default_value = a_default_index
        if a_default_index is not None:
            self.set_value(a_default_index)
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def wheel_event(self, a_event=None):
        pass

    def control_value_changed(self, val):
        if not self.suppress_changes:
            self.val_callback(self.port_num, val)
            if self.rel_callback is not None:
                self.rel_callback(self.port_num, val)

    def set_value(self, a_val, a_changed=False):
        if not a_changed:
            self.suppress_changes = True
        self.control.setCurrentIndex(int(a_val))
        self.suppress_changes = False

    def get_value(self):
        return self.control.currentIndex()

