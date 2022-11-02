from . import _shared
from .control import *
from sglib.lib.translate import _
from sgui.sgqt import *


class ramp_env_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_port_dict,
        a_time_port,
        a_amt_port,
        a_label=_("Ramp Env"),
        a_preset_mgr=None,
        a_curve_port=None,
        knob_kwargs={},
    ):
        self.groupbox = QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)
        self.layout.setContentsMargins(3, 3, 3, 3)

        if a_amt_port is not None:
            self.amt_knob = knob_control(
                a_size,
                _("Amt"),
                a_amt_port,
                a_rel_callback,
                a_val_callback,
                -36,
                36,
                0,
                _shared.KC_INTEGER,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    'The amount of modulation this envelope has on '
                    'the destination control'
                ),
            )
            self.amt_knob.add_to_grid_layout(self.layout, 0)
        self.time_knob = knob_control(
            a_size,
            _("Time"),
            a_time_port,
            a_rel_callback,
            a_val_callback,
            1,
            600,
            100,
            _shared.KC_TIME_DECIMAL,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip='How long this envelope takes to run',
        )
        self.time_knob.add_to_grid_layout(self.layout, 1)
        if a_curve_port is not None:
            self.curve_knob = knob_control(
                a_size,
                _("Curve"),
                a_curve_port,
                a_rel_callback,
                a_val_callback,
                0,
                100,
                50,
                _shared.KC_NONE,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
                tooltip='The curve of the envelope',
            )
            self.curve_knob.add_to_grid_layout(self.layout, 2)

