from . import _shared
from .multifx_tooltips import mfx_set_tooltip, MULTIFX_INFO
from .control import *
from sglib.models.multifx_settings import multifx_settings
from sglib.lib.translate import _
from sgui.sgqt import *

import copy


MULTIFX_CLIPBOARD = None
MULTIFX_EFFECTS_LOOKUP = {
    k: (v.index, v.tooltip)
    for k, v in MULTIFX_INFO.items()
}

MULTIFX_FILTERS_SYNTH = [
    "BP2",
    "BP4",
    'BP D/W',
    "BP Spread",
    "EQ",
    "Formant",
    "Growl Filter",
    "HP D/W",
    "HP2",
    "HP4",
    "Ladder4",
    "LP D/W",
    "LP Screech",
    "LP2",
    "LP4",
    "LP<-->HP",
    "Notch D/W",
    "Notch Spread",
    "Notch2",
    "Notch4",
]

MULTIFX_FILTERS_EFFECT = copy.deepcopy(MULTIFX_FILTERS_SYNTH)
MULTIFX_FILTERS_EFFECT.remove('Ladder4')

MULTIFX_DISTORTION = [
    "Distortion",
    "Foldback",
    "Glitch",
    "LoFi",
    "RingMod",
    "S/H",
    "Saturator",
    "Soft Clipper",
]

MULTIFX_DELAY = [
    "Stereo Chorus",
    "Comb Filter",
    "Flanger Static",
    "Metal Comb",
    "Phaser Static",
]

MULTIFX_DYNAMICS = [
    "Amp/Pan",
    "DC Offset",
    "Limiter",
    "Monofier",
]

MULTIFX_ITEMS_SYNTH = [
    "Off",
    ("Filters", MULTIFX_FILTERS_SYNTH),
    ("Distortion", MULTIFX_DISTORTION),
    ("Delay", MULTIFX_DELAY),
    ("Dynamics", MULTIFX_DYNAMICS),
]

MULTIFX_ITEMS_EFFECT = [
    "Off",
    ("Filters", MULTIFX_FILTERS_EFFECT),
    ("Distortion", MULTIFX_DISTORTION),
    ("Delay", MULTIFX_DELAY),
    ("Dynamics", MULTIFX_DYNAMICS),
]

class MultiFXSingle:
    def __init__(
        self,
        a_title,
        a_port_k1,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_preset_mgr=None,
        a_knob_size=51,
        knob_kwargs={},
        fixed_height=False,
        fixed_width=False,
        multifx_items=MULTIFX_ITEMS_EFFECT,
    ):
        self.group_box = QGroupBox()
        self.group_box.contextMenuEvent = self.contextMenuEvent
        self.group_box.setObjectName("plugin_groupbox")
        if a_title is not None:
            self.group_box.setTitle(str(a_title))
        self.layout = QGridLayout()
        self.layout.setContentsMargins(3, 3, 3, 3)
        #self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.group_box.setLayout(self.layout)
        self.knobs = []
        for f_i in range(3):
            f_knob = knob_control(
                a_knob_size,
                "",
                a_port_k1 + f_i,
                a_rel_callback,
                a_val_callback,
                0,
                127,
                64,
                a_port_dict=a_port_dict,
                a_preset_mgr=a_preset_mgr,
                knob_kwargs=knob_kwargs,
            )
            f_knob.name_label.setObjectName('transparent')
            f_knob.value_label.setObjectName('transparent')
            f_knob.add_to_grid_layout(self.layout, f_i)
            self.knobs.append(f_knob)
        if fixed_height:
            self.group_box.adjustSize()
            self.group_box.setFixedHeight(
                self.group_box.height(),
            )
        if fixed_width:
            self.group_box.adjustSize()
            self.group_box.setFixedHeight(
                self.group_box.height(),
            )
        for knob in self.knobs:
            knob.control.hide()
        self.combobox = NestedComboboxControl(
            132,
            "Type",
            a_port_k1 + 3,
            a_rel_callback,
            a_val_callback,
            MULTIFX_EFFECTS_LOOKUP,
            multifx_items,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            a_default_index=0,
        )
        self.combobox.name_label.setObjectName('transparent')
        self.combobox.control.currentIndexChanged_connect(
            self.type_combobox_changed,
        )
        self.layout.addWidget(self.combobox.name_label, 0, 3)
        self.layout.addWidget(self.combobox.control, 1, 3)

    def wheel_event(self, a_event=None):
        pass

    def disable_mousewheel(self):
        """ Mousewheel events cause problems with
            per-audio-item-fx because they rely on the mouse release event.
        """
        for knob in self.knobs:
            knob.control.wheelEvent = self.wheel_event
        self.combobox.control.wheelEvent = self.wheel_event

    def contextMenuEvent(self, a_event):
        f_menu = QMenu(self.group_box)

        f_copy_action = QAction(_("Copy"), f_menu)
        f_copy_action.setToolTip(
            'Copy this effect and control settings to the clipboard, to '
            'paste to another effect'
        )
        f_menu.addAction(f_copy_action)
        f_copy_action.triggered.connect(self.copy_settings)

        f_cut_action = QAction(_("Cut"), f_menu)
        f_cut_action.setToolTip(
            'Copy this effect and controls to the clipboard, and reset this '
            'effect to the default (off) value'
        )
        f_menu.addAction(f_cut_action)
        f_cut_action.triggered.connect(self.cut_settings)

        f_paste_action = QAction(_('Paste'), f_menu)
        f_menu.addAction(f_paste_action)
        f_paste_action.setToolTip(
            'Paste a previously copied effect to this effect, replacing the '
            'current effect and controls'
        )
        f_paste_action.triggered.connect(self.paste_settings)

        f_paste_and_copy_action = QAction(_("Paste and Copy"), f_menu)
        f_paste_and_copy_action.setToolTip(
            'Paste the effect setting previously copied to the clipboard, '
            'while replacing the clipboard contents with the current settings '
            'of this effect.  Use this to swap effects'
        )
        f_menu.addAction(f_paste_and_copy_action)
        f_paste_and_copy_action.triggered.connect(self.paste_and_copy)

        f_reset_action = QAction(_("Reset"), f_menu)
        f_reset_action.setToolTip(
            'Reset this effect to the default (off) settings'
        )
        f_menu.addAction(f_reset_action)
        f_reset_action.triggered.connect(self.reset_settings)

        f_menu.exec(QCursor.pos())

    def copy_settings(self):
        global MULTIFX_CLIPBOARD
        MULTIFX_CLIPBOARD = self.get_class()

    def paste_and_copy(self):
        """ Copy the existing setting and then paste,
            for rearranging effects
        """
        self.paste_settings(True)

    def paste_settings(self, a_copy=False):
        global MULTIFX_CLIPBOARD
        if MULTIFX_CLIPBOARD is None:
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("Nothing copied to clipboard"),
            )
        else:
            f_class = self.get_class()
            self.set_from_class(MULTIFX_CLIPBOARD)
            self.update_all_values()
            if a_copy:
                MULTIFX_CLIPBOARD = f_class

    def update_all_values(self):
        for f_knob in self.knobs:
            f_knob.control_value_changed(f_knob.get_value())
        self.combobox.control_value_changed(self.combobox.get_value())

    def cut_settings(self):
        self.copy_settings()
        self.reset_settings()

    def reset_settings(self):
        self.set_from_class(multifx_settings(64, 64, 64, 0))
        self.update_all_values()

    def set_from_class(self, a_class):
        """ a_class is a multifx_settings instance """
        self.knobs[0].set_value(a_class.knobs[0])
        self.knobs[1].set_value(a_class.knobs[1])
        self.knobs[2].set_value(a_class.knobs[2])
        self.combobox.set_value(a_class.fx_type)

    def get_class(self):
        """ return a multifx_settings instance """
        return multifx_settings(
            self.knobs[0].control.value(),
            self.knobs[1].control.value(),
            self.knobs[2].control.value(),
            self.combobox.control.currentIndex(),
        )

    def type_combobox_changed(self, a_val):
        if a_val == 0: #Off
            self.knobs[0].control.hide()
            self.knobs[1].control.hide()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText("")
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 1: #LP2
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 2: #LP4
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 3: #HP2
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 4: #HP4
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 5: #BP2
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 6: #BP4
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 7: #Notch2
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 8: #Notch4
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 9: #EQ
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("BW"))
            self.knobs[2].name_label.setText(_("Gain"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(1.0, 6.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(-24.0, 24.0)
            self.knobs[1].value_label.setText("")
        elif a_val == 10: #Distortion
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Gain"))
            self.knobs[1].name_label.setText(_("D/W"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(0.0, 48.0)
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(-30.0, 0.0)
        elif a_val == 11: #Comb Filter
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 12: #Amp/Panner
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-40.0, 24.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 13: #Limiter
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Ceil"))
            self.knobs[2].name_label.setText(_("Rel"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-30.0, 0.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-12.0, -0.1)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X_INT
            self.knobs[2].set_min_max(50.0, 1500.0)
        elif a_val == 14: #Saturator
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Gain"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-12.0, 12.0)
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(-12.0, 12.0)
        elif a_val == 15: #Formant Filter
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 16: #Chorus
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Rate"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("Fine")
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(0.3, 6.0)
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(0.1, 1.9)
        elif a_val == 17: #Glitch
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Glitch"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 18: #RingMod
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 19: #LoFi
            self.knobs[0].control.show()
            self.knobs[1].control.hide()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Bits"))
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(4.0, 16.0)
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 20: #Sample and Hold
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 21: #LP2-Dry/Wet
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 22: #HP2-Dry/Wet
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 23: #Monofier
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 6.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 24: #LP<-->HP
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(("LP/HP"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 25: #Growl Filter
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Type"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 26: #LP Screech
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 27: #Metal Comb
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[2].name_label.setText(_("Spread"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 28: #Notch4-Dry/Wet
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 29: #Foldback Distortion
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Gain"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-12.0, 0.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(0.0, 12.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 30: #Notch Spread
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Spread"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH_MIN_MAX
            self.knobs[0].set_min_max(44.0, 100.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-10.0, -1.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(0.0, 36.0)
        elif a_val == 31: # DC Offset
            self.knobs[0].control.hide()
            self.knobs[1].control.hide()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText("")
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
        elif a_val == 32: # BP Spread
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Spread"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH_MIN_MAX
            self.knobs[0].set_min_max(44.0, 100.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-10.0, -1.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(0.0, 48.0)
        elif a_val == 33: # Phaser Static
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Feed"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 34: # Flanger Static
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Feed"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 35: # Soft Clipper
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Shape"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-12.0, 0.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(0.0, 2.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(-12.0, 12.0)
        elif a_val == 37: #BP2-Dry/Wet
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.show()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 38: #Ladder4
            self.knobs[0].control.show()
            self.knobs[1].control.show()
            self.knobs[2].control.hide()
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")

        self.knobs[0].set_value(self.knobs[0].control.value())
        self.knobs[1].set_value(self.knobs[1].control.value())
        self.knobs[2].set_value(self.knobs[2].control.value())
        mfx_set_tooltip(self.knobs, a_val)

