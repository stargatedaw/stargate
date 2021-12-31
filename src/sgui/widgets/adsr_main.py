from . import _shared
from .control import *
from sglib import math as sg_math
from sglib.lib.translate import _
from sgui.sgqt import *


ADSR_CLIPBOARD = {}

class ADSRMainWidget:
    def __init__(
        self,
        a_size,
        a_sustain_in_db,
        attack_port,
        attack_pmn_start_port,
        attack_pmn_end_port,
        decay_port,
        decay_pmn_start_port,
        decay_pmn_end_port,
        sustain_port,
        sustain_pmn_start_port,
        sustain_pmn_end_port,
        release_port,
        release_pmn_start_port,
        release_pmn_end_port,
        a_label,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_preset_mgr=None,
        a_attack_default=10,
        a_prefx_port=None,
        a_knob_type=_shared.KC_TIME_DECIMAL,
        a_delay_port=None,
        a_hold_port=None,
        a_lin_port=None,
        a_lin_default=1,
        knob_kwargs={},
    ):
        self.clipboard_dict = {}
        self.groupbox = QGroupBox(a_label)
        self.groupbox.contextMenuEvent = self.context_menu_event
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)
        self.layout.setContentsMargins(3, 3, 3, 3)

        if a_delay_port is not None:
            self.delay_knob = knob_control(
                a_size,
                _("Delay"),
                a_delay_port,
                a_rel_callback,
                a_val_callback,
                0,
                200,
                0,
                _shared.KC_TIME_DECIMAL,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
            )
            self.delay_knob.add_to_grid_layout(self.layout, 0)
            self.clipboard_dict["delay"] = self.delay_knob
        self.attack_knobs = []
        for name, port in (
            ('Attack', attack_port),
            ('Att. Start', attack_pmn_start_port),
            ('Att. End', attack_pmn_end_port),
        ):
            knob = knob_control(
                a_size,
                _(name),
                port,
                a_rel_callback,
                a_val_callback,
                0,
                200,
                a_attack_default,
                a_knob_type,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
            )
            self.attack_knobs.append(knob)
        self.attack_knob = MultiplexedControl(
            self.attack_knobs,
        )

        if a_hold_port is not None:
            self.hold_knob = knob_control(
                a_size,
                _("Hold"),
                a_hold_port,
                a_rel_callback,
                a_val_callback,
                0,
                200,
                0,
                _shared.KC_TIME_DECIMAL,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
            )
            self.hold_knob.add_to_grid_layout(self.layout, 3)
            self.clipboard_dict["hold"] = self.hold_knob
        self.decay_knobs = []
        for name, port in (
            ("Decay", decay_port),
            ("Dec. Start", decay_pmn_start_port),
            ("Dec. End", decay_pmn_end_port),
        ):
            knob = knob_control(
                a_size,
                _(name),
                port,
                a_rel_callback,
                a_val_callback,
                10,
                200,
                50,
                a_knob_type,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
            )
            self.decay_knobs.append(knob)
        self.decay_knob = MultiplexedControl(
            self.decay_knobs,
        )
        self.sustain_knobs = []
        for name, port in (
            ("Sustain", sustain_port),
            ("Sus. Start", sustain_pmn_start_port),
            ("Sus. End", sustain_pmn_end_port),
        ):
            if a_sustain_in_db:
                knob = knob_control(
                    a_size,
                    _(name),
                    port,
                    a_rel_callback,
                    a_val_callback,
                    -30,
                    0,
                    0,
                    _shared.KC_INTEGER,
                    a_port_dict,
                    a_preset_mgr,
                    knob_kwargs=knob_kwargs,
                )
                self.clipboard_dict["sustain_db"] = self.sustain_knob
            else:
                knob = knob_control(
                    a_size,
                    _(name),
                    port,
                    a_rel_callback,
                    a_val_callback,
                    0,
                    100,
                    100,
                    _shared.KC_DECIMAL,
                    a_port_dict,
                    a_preset_mgr,
                    knob_kwargs=knob_kwargs,
                )
                self.clipboard_dict["sustain"] = self.sustain_knob
            self.sustain_knobs.append(knob)
        self.sustain_knob = MultiplexedControl(
            self.sustain_knobs,
        )
        self.release_knobs = []
        for name, port in (
            ("Release", release_port),
            ("Rel. Start", release_pmn_start_port),
            ("Rel. End", release_pmn_end_port),
        ):
            knob = knob_control(
                a_size,
                _(name),
                port,
                a_rel_callback,
                a_val_callback,
                10,
                400,
                50,
                a_knob_type,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
            )
            self.release_knobs.append(knob)
        self.release_knob = MultiplexedControl(
            self.release_knobs,
        )
        self.attack_knob.add_to_grid_layout(self.layout, 2)
        self.decay_knob.add_to_grid_layout(self.layout, 4)
        self.sustain_knob.add_to_grid_layout(self.layout, 6)
        self.release_knob.add_to_grid_layout(self.layout, 8)
        self.clipboard_dict["attack"] = self.attack_knob
        self.clipboard_dict["decay"] = self.decay_knob
        self.clipboard_dict["release"] = self.release_knob
        if a_prefx_port is not None:
            self.prefx_checkbox = checkbox_control(
                "PreFX",
                a_prefx_port,
                a_rel_callback,
                a_val_callback,
                a_port_dict,
                a_preset_mgr,
            )
            self.prefx_checkbox.add_to_grid_layout(self.layout, 10)
        if a_lin_port is not None:
            assert a_lin_default in (0, 1)
            self.lin_checkbox = checkbox_control(
                "Lin.", a_lin_port, a_rel_callback, a_val_callback,
                a_port_dict, a_preset_mgr, a_lin_default)
            self.lin_checkbox.control.setToolTip(
                _("Use a linear curve instead of a logarithmic decibel \n"
                "curve, use this when there are artifacts in the \n"
                "release tail")
            )
            self.lin_checkbox.add_to_grid_layout(self.layout, 12)

    def context_menu_event(self, a_event):
        f_menu = QMenu(self.groupbox)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste)
        f_menu.exec(QCursor.pos())

    def copy(self):
        global ADSR_CLIPBOARD
        ADSR_CLIPBOARD = dict([(k, v.get_value())
            for k, v in self.clipboard_dict.items()])

    def paste(self):
        if not ADSR_CLIPBOARD:
            return
        for k, v in self.clipboard_dict.items():
            if k in ADSR_CLIPBOARD:
                v.set_value(ADSR_CLIPBOARD[k], True)
            elif k == 'sustain' and 'sustain_db' in ADSR_CLIPBOARD:
                v.set_value(
                    int(
                        sg_math.db_to_lin(
                            ADSR_CLIPBOARD['sustain_db'],
                        ) * 100
                    ),
                    True,
                )
            elif k == 'sustain_db' and 'sustain' in ADSR_CLIPBOARD:
                v.set_value(
                    int(
                        sg_math.lin_to_db(
                            ADSR_CLIPBOARD['sustain'] * 0.01,
                        ),
                    ),
                    True,
                )
            else:
                LOG.warning(
                    f'{k} not in clipboard: {ADSR_CLIPBOARD}, not applying'
                )

