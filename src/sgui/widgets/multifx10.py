from . import _shared
from .control import *
from .knob import ArcType
from sglib.lib.translate import _
from sgui.sgqt import *


MULTIFX10_CLIPBOARD = None

class MultiFX10Info:
    def __init__(
        self,
        index: int,
    ):
        self.index = index

MULTIFX10_INFO = {
    "Off": MultiFX10Info(0),
    "LP2": MultiFX10Info(1),
    "LP4": MultiFX10Info(2),
    "HP2": MultiFX10Info(3),
    "HP4": MultiFX10Info(4),
    "BP2": MultiFX10Info(5),
    "BP4": MultiFX10Info(6),
    "Notch2": MultiFX10Info(7),
    "Notch4": MultiFX10Info(8),
    "EQ": MultiFX10Info(9),
    "Distortion": MultiFX10Info(10),
    "Comb Filter": MultiFX10Info(11),
    "Amp/Pan": MultiFX10Info(12),
    "Limiter": MultiFX10Info(13),
    "Saturator": MultiFX10Info(14),
    "Formant": MultiFX10Info(15),
    "Stereo Chorus": MultiFX10Info(16),
    "Glitch": MultiFX10Info(17),
    "RingMod": MultiFX10Info(18),
    "LoFi": MultiFX10Info(19),
    "S/H": MultiFX10Info(20),
    "LP D/W": MultiFX10Info(21),
    "HP D/W": MultiFX10Info(22),
    "Monofier": MultiFX10Info(23),
    "LP<-->HP": MultiFX10Info(24),
    "Growl Filter": MultiFX10Info(25),
    "LP Screech": MultiFX10Info(26),
    "Metal Comb": MultiFX10Info(27),
    "Notch D/W": MultiFX10Info(28),
    "Foldback": MultiFX10Info(29),
    "Notch Spread": MultiFX10Info(30),
    "DC Offset": MultiFX10Info(31),
    "BP Spread": MultiFX10Info(32),
    "Phaser Static": MultiFX10Info(33),
    "Flanger Static": MultiFX10Info(34),
    "Soft Clipper": MultiFX10Info(35),
    "Compressor": MultiFX10Info(36),
}
MULTIFX10_EFFECTS_LOOKUP = {k: v.index for k, v in MULTIFX10_INFO.items()}

MULTIFX10_FILTERS = [
    "BP2",
    "BP4",
    "BP Spread",
    "EQ",
    "Formant",
    "Growl Filter",
    "HP D/W",
    "HP2",
    "HP4",
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

MULTIFX10_DISTORTION = [
    "Distortion",
    "Foldback",
    "Glitch",
    "LoFi",
    "RingMod",
    "S/H",
    "Saturator",
    "Soft Clipper",
]

MULTIFX10_DELAY = [
    "Stereo Chorus",
    "Comb Filter",
    "Flanger Static",
    "Metal Comb",
    "Phaser Static",
]

MULTIFX10_DYNAMICS = [
    "Amp/Pan",
    "Compressor",
    "DC Offset",
    "Limiter",
    "Monofier",
]

MULTIFX10_ITEMS = [
    "Off",
    ("Filters", MULTIFX10_FILTERS),
    ("Distortion", MULTIFX10_DISTORTION),
    ("Delay", MULTIFX10_DELAY),
    ("Dynamics", MULTIFX10_DYNAMICS),
]

class MultiFX10:
    def __init__(
        self,
        mfx_index,
        mfx_count,
        a_port_k1,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_preset_mgr=None,
        a_knob_size=51,
        knob_kwargs={},
        fixed_height=False,
        fixed_width=False,
    ):
        self.mfx_index = mfx_index
        self.group_box = QGroupBox()
        self.group_box.contextMenuEvent = self.contextMenuEvent
        self.group_box.setObjectName("plugin_groupbox")
        self.group_box.setTitle(f'FX{mfx_index + 1}')
        self.layout = QGridLayout()
        self.layout.setContentsMargins(3, 3, 3, 3)
        #self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.group_box.setLayout(self.layout)
        self.knobs = []
        for f_i in range(10):
            f_knob = knob_control(
                a_knob_size,
                "",
                a_port_k1 + f_i,
                a_rel_callback,
                a_val_callback,
                0,
                1270,
                635,
                a_port_dict=a_port_dict,
                a_preset_mgr=a_preset_mgr,
                knob_kwargs=knob_kwargs,
                value_multiplier=0.1,
            )
            f_knob.add_to_grid_layout(self.layout, f_i + 10)
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
        self.route_combobox = combobox_control(
            64,
            "Route",
            a_port_k1 + 10,
            a_rel_callback,
            a_val_callback,
            [
                f'FX{x}' for x in range(mfx_index + 2, mfx_count + 1)
            ] + ["Out"],
            a_port_dict=a_port_dict,
            a_default_index=0,
            a_preset_mgr=a_preset_mgr,
        )
        self.route_combobox.add_to_grid_layout(self.layout, 0)
        self.fx_type = NestedComboboxControl(
            132,
            "Type",
            a_port_k1 + 11,
            a_rel_callback,
            a_val_callback,
            MULTIFX10_EFFECTS_LOOKUP,
            MULTIFX10_ITEMS,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            a_default_index=0,
        )
        self.fx_type.control.currentIndexChanged_connect(
            self.type_combobox_changed,
        )
        self.fx_type.add_to_grid_layout(self.layout, 1)
        # self.layout.addWidget(self.fx_type.name_label, 0, 0)
        # self.layout.addWidget(self.fx_type.control, 1, 0)

        self.dry_knob = knob_control(
            a_knob_size,
            "Dry",
            a_port_k1 + 12,
            a_rel_callback,
            a_val_callback,
            -400,
            120,
            -400,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            knob_kwargs=knob_kwargs,
            min_text='-inf',
            a_val_conversion=_shared.KC_TENTH,
        )
        self.dry_knob.hide()
        self.dry_knob.add_to_grid_layout(self.layout, 2)
        self.wet_knob = knob_control(
            a_knob_size,
            "Wet",
            a_port_k1 + 13,
            a_rel_callback,
            a_val_callback,
            -400,
            120,
            0,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            knob_kwargs=knob_kwargs,
            min_text='-inf',
            a_val_conversion=_shared.KC_TENTH,
        )
        self.wet_knob.hide()
        self.wet_knob.add_to_grid_layout(self.layout, 3)
        knob_kwargs['arc_type'] = ArcType.BIDIRECTIONAL
        self.pan_knob = knob_control(
            a_knob_size,
            "D/W Pan",
            a_port_k1 + 14,
            a_rel_callback,
            a_val_callback,
            -100,
            100,
            0,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            knob_kwargs=knob_kwargs,
            a_val_conversion=_shared.KC_DECIMAL,
        )
        knob_kwargs.pop('arc_type')
        self.pan_knob.hide()
        self.pan_knob.add_to_grid_layout(self.layout, 4)

    def wheel_event(self, a_event=None):
        pass

    def disable_mousewheel(self):
        """ Mousewheel events cause problems with
            per-audio-item-fx because they rely on the mouse release event.
        """
        for knob in self.knobs:
            knob.control.wheelEvent = self.wheel_event
        self.fx_type.control.wheelEvent = self.wheel_event

    def hide_knobs(self, index, dry_wet_pan=False):
        for i in range(index):
            self.knobs[i].control.show()

        for i in range(index, 10):
            self.knobs[i].control.hide()
            self.knobs[i].name_label.setText("")
            self.knobs[i].val_conversion = _shared.KC_NONE

        if dry_wet_pan:
            self.pan_knob.hide()
            self.dry_knob.hide()
            self.wet_knob.hide()
        else:
            self.pan_knob.show()
            self.dry_knob.show()
            self.wet_knob.show()

    def contextMenuEvent(self, a_event):
        f_menu = QMenu(self.group_box)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy_settings)
        f_cut_action = f_menu.addAction(_("Cut"))
        f_cut_action.triggered.connect(self.cut_settings)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste_settings)
        f_paste_and_copy_action = f_menu.addAction(_("Paste and Copy"))
        f_paste_and_copy_action.triggered.connect(self.paste_and_copy)
        f_menu.addAction(f_paste_and_copy_action)
        f_reset_action = f_menu.addAction(_("Reset"))
        f_reset_action.triggered.connect(self.reset_settings)
        f_menu.exec(QCursor.pos())

    def copy_settings(self):
        global MULTIFX10_CLIPBOARD
        MULTIFX10_CLIPBOARD = self.get_tuple()

    def paste_and_copy(self):
        """ Copy the existing setting and then paste,
            for rearranging effects
        """
        self.paste_settings(True)

    def paste_settings(self, a_copy=False):
        global MULTIFX10_CLIPBOARD
        if MULTIFX10_CLIPBOARD is None:
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("Nothing copied to clipboard"),
            )
        else:
            f_class = self.get_tuple()
            self.set_from_tuple(MULTIFX10_CLIPBOARD)
            self.update_all_values()
            if a_copy:
                MULTIFX10_CLIPBOARD = f_class

    def update_all_values(self):
        for f_knob in self.knobs:
            f_knob.control_value_changed(f_knob.get_value())
        self.fx_type.control_value_changed(self.fx_type.get_value())

    def cut_settings(self):
        self.copy_settings()
        self.reset_settings()

    def reset_settings(self):
        tpl = ((64,) * len(self.knobs)) + (0,)
        self.set_from_tuple(tpl)
        self.update_all_values()

    def set_from_tuple(self, tpl):
        for i in range(len(self.knobs)):
            self.knobs[i].set_value(tpl[i])
        self.fx_type.set_value(tpl[-1])

    def get_tuple(self) -> tuple:
        return (
            *(x.control.value() for x in self.knobs),
            self.fx_type.control.currentIndex(),
        )

    def type_combobox_changed(self, a_val):
        if a_val == 0: #Off
            self.hide_knobs(0, dry_wet_pan=True)
        elif a_val == 1: #LP2
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 2: #LP4
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 3: #HP2
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 4: #HP4
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 5: #BP2
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 6: #BP4
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 7: #Notch2
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 8: #Notch4
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 9: #EQ
            self.hide_knobs(3)
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
            self.hide_knobs(3)
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
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
        elif a_val == 12: #Amp/Panner
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-100.0, 100.0)
            self.knobs[1].set_min_max(-40.0, 24.0)
        elif a_val == 13: #Limiter
            self.hide_knobs(3)
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
            self.hide_knobs(3)
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
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
        elif a_val == 16: #Stereo Chorus
            self.hide_knobs(3)
            self.knobs[0].name_label.setText(_("Rate"))
            self.knobs[1].name_label.setText("Fine")
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(0.3, 6.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(0.1, 1.9)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 17: #Glitch
            self.hide_knobs(3)
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
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
        elif a_val == 19: #LoFi
            self.hide_knobs(1)
            self.knobs[0].name_label.setText(_("Bits"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(4.0, 16.0)
        elif a_val == 20: #Sample and Hold
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
        elif a_val == 21: #LP2-Dry/Wet
            self.hide_knobs(3)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 22: #HP2-Dry/Wet
            self.hide_knobs(3)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 23: #Monofier
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-100.0, 100.0)
            self.knobs[1].set_min_max(-30.0, 6.0)
        elif a_val == 24: #LP<-->HP
            self.hide_knobs(3)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(("LP/HP"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 25: #Growl Filter
            self.hide_knobs(3)
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
            self.hide_knobs(2)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
        elif a_val == 27: #Metal Comb
            self.hide_knobs(3)
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
            self.hide_knobs(3)
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 29: #Foldback Distortion
            self.hide_knobs(3)
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
            self.hide_knobs(3)
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
            self.hide_knobs(0)
        elif a_val == 32: # BP Spread
            self.hide_knobs(3)
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
            self.hide_knobs(3)
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
            self.hide_knobs(3)
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
            self.hide_knobs(3)
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Shape"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-12.0, 0.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(0.0, 2.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(-12.0, 12.0)
        elif a_val == 36:  # Compressor
            self.hide_knobs(6)
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Ratio"))
            self.knobs[2].name_label.setText(_("Knee"))
            self.knobs[3].name_label.setText(_("Attack"))
            self.knobs[4].name_label.setText(_("Release"))
            self.knobs[5].name_label.setText(_("Gain"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_min_max(-36.0, -6.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_min_max(1.0, 10.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_min_max(0.0, 12.0)
            self.knobs[3].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[3].set_min_max(0.0, 500.0)
            self.knobs[4].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[4].set_min_max(10.0, 500.0)
            self.knobs[5].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[5].set_min_max(-36.0, 36.0)
        else:
            raise NotImplementedError(f"Unknown FX uid: {a_val}")

        for knob in self.knobs:
            knob.set_value(knob.control.value())

