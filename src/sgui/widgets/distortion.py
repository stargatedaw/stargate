from . import _shared
from .control import *
from sglib.lib.translate import _
from sgui.sgqt import *


class MultiDistWidget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_port_dict,
        a_gain_port,
        a_dw_port,
        a_out_port,
        a_type_port,
        a_label=_("Distortion"),
        a_preset_mgr=None,
    ):
        self.groupbox_dist = QGroupBox(a_label)
        self.groupbox_dist.setObjectName("plugin_groupbox")
        self.groupbox_dist_layout = QGridLayout(self.groupbox_dist)

        self.dist = knob_control(
            a_size, _("Gain"), a_gain_port, a_rel_callback, a_val_callback,
            0, 48, 15, _shared.KC_INTEGER, a_port_dict, a_preset_mgr)
        self.dist.add_to_grid_layout(self.groupbox_dist_layout, 0)
        self.dist_wet = knob_control(
            a_size, _("Wet"), a_dw_port, a_rel_callback, a_val_callback,
            0, 100, 0, _shared.KC_NONE, a_port_dict, a_preset_mgr)
        self.dist_wet.add_to_grid_layout(self.groupbox_dist_layout, 1)
        self.dist_out_gain = knob_control(
            a_size, _("Out"), a_out_port, a_rel_callback, a_val_callback,
            -1800, 0, 0, _shared.KC_DECIMAL, a_port_dict, a_preset_mgr)
        self.dist_out_gain.add_to_grid_layout(self.groupbox_dist_layout, 2)
        self.type_combobox = combobox_control(
            75, _("Type"), a_type_port, a_rel_callback, a_val_callback,
            [_("Off"), _("Clip"), _("Fold")], a_port_dict, 0, a_preset_mgr)
        self.type_combobox.add_to_grid_layout(self.groupbox_dist_layout, 3)


