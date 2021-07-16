# -*- coding: utf-8 -*-
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

from sgui.widgets import *
from sglib.lib.translate import _


SGDELAY_DELAY_TIME = 0
SGDELAY_FEEDBACK = 1
SGDELAY_DRY = 2
SGDELAY_WET = 3
SGDELAY_DUCK = 4
SGDELAY_CUTOFF = 5
SGDELAY_STEREO = 6


SGDELAY_PORT_MAP = {
    "Delay Feedback": SGDELAY_FEEDBACK,
    "Delay Dry": SGDELAY_DRY,
    "Delay Wet": SGDELAY_WET,
    "Delay Duck": SGDELAY_DUCK,
    "Delay LP Cutoff": SGDELAY_CUTOFF,
}


class sgdelay_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "SGDELAY"
        self.is_instrument = False

        self.layout.setSizeConstraint(
            QLayout.SizeConstraint.SetFixedSize,
        )

        self.delay_hlayout = QHBoxLayout()
        self.layout.addLayout(self.delay_hlayout)

        f_knob_size = DEFAULT_KNOB_SIZE
        self.preset_manager = None

        self.delay_gridlayout = QGridLayout()
        self.delay_hlayout.addLayout(self.delay_gridlayout)

        self.delay_time_knob = knob_control(
            f_knob_size, _("Time"), SGDELAY_DELAY_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            10, 100, 50, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.delay_time_knob.add_to_grid_layout(self.delay_gridlayout, 0)
        self.feedback = knob_control(
            f_knob_size, _("Fdbk"), SGDELAY_FEEDBACK,
            self.plugin_rel_callback, self.plugin_val_callback,
            -200, 0, -120, KC_TENTH, self.port_dict, self.preset_manager)
        self.feedback.add_to_grid_layout(self.delay_gridlayout, 1)
        self.dry_knob = knob_control(
            f_knob_size, _("Dry"), SGDELAY_DRY,
            self.plugin_rel_callback, self.plugin_val_callback,
            -300, 0, 0, KC_TENTH, self.port_dict, self.preset_manager)
        self.dry_knob.add_to_grid_layout(self.delay_gridlayout, 2)
        self.wet_knob = knob_control(
            f_knob_size, _("Wet"), SGDELAY_WET,
            self.plugin_rel_callback, self.plugin_val_callback, -300, 0, -120,
            KC_TENTH, self.port_dict, self.preset_manager)
        self.wet_knob.add_to_grid_layout(self.delay_gridlayout, 3)
        self.duck_knob = knob_control(
            f_knob_size, _("Duck"), SGDELAY_DUCK,
            self.plugin_rel_callback, self.plugin_val_callback,
            -40, 0, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.duck_knob.add_to_grid_layout(self.delay_gridlayout, 4)
        self.cutoff_knob = knob_control(
            f_knob_size, _("Cutoff"), SGDELAY_CUTOFF,
            self.plugin_rel_callback, self.plugin_val_callback,
            40, 118, 90, KC_PITCH, self.port_dict, self.preset_manager)
        self.cutoff_knob.add_to_grid_layout(self.delay_gridlayout, 5)
        self.stereo_knob = knob_control(
            f_knob_size, _("Stereo"), SGDELAY_STEREO,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.stereo_knob.add_to_grid_layout(self.delay_gridlayout, 6)

        self.open_plugin_file()
        self.set_midi_learn(SGDELAY_PORT_MAP)

    def open_plugin_file(self):
        AbstractPluginUI.open_plugin_file(self)

    def save_plugin_file(self):
        AbstractPluginUI.save_plugin_file(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


