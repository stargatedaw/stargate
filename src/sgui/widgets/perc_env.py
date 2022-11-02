from . import _shared
from .control import *
from sglib.lib.translate import _
from sgui.sgqt import *


class perc_env_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_port_dict,
        a_time1_port,
        a_pitch1_port,
        a_time2_port,
        a_pitch2_port,
        a_on_port,
        a_label=_("Perc Env"),
        a_preset_mgr=None,
        knob_kwargs={},
    ):
        self.groupbox = QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)
        self.layout.setContentsMargins(3, 3, 3, 3)

        self.time1_knob = knob_control(
            a_size,
            _("Time1"),
            a_time1_port,
            a_rel_callback,
            a_val_callback,
            2,
            40,
            10,
            _shared.KC_INTEGER,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'The time in milliseconds that the envelope moves from Pitch1 '
                'to Pitch2'
            ),
        )
        self.time1_knob.add_to_grid_layout(self.layout, 0)

        self.pitch1_knob = knob_control(
            a_size,
            _("Pitch1"),
            a_pitch1_port,
            a_rel_callback,
            a_val_callback,
            42,
            120,
            66,
            _shared.KC_PITCH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip='The starting frequency of the envelope',
        )
        self.pitch1_knob.add_to_grid_layout(self.layout, 1)

        self.time2_knob = knob_control(
            a_size,
            _("Time2"),
            a_time2_port,
            a_rel_callback,
            a_val_callback,
            20,
            400,
            100,
            _shared.KC_INTEGER,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'The time in milliseconds that the envelope moves from Pitch2 '
                'to the pitch of the note that was played on the keyboard'
            ),
        )
        self.time2_knob.add_to_grid_layout(self.layout, 2)

        self.pitch2_knob = knob_control(
            a_size,
            _("Pitch2"),
            a_pitch2_port,
            a_rel_callback,
            a_val_callback,
            33,
            63,
            48,
            _shared.KC_PITCH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip='The middle frequency of the envelope',
        )
        self.pitch2_knob.add_to_grid_layout(self.layout, 3)

        self.on_switch = checkbox_control(
            _("On"),
            a_on_port,
            a_rel_callback,
            a_val_callback,
            a_port_dict,
            a_preset_mgr,
            tooltip=(
                "Enable/disable the percussion envelope from modifying pitch"
            ),
        )
        self.on_switch.add_to_grid_layout(self.layout, 4)


