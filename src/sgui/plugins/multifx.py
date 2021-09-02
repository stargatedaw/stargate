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


MULTIFX_FIRST_CONTROL_PORT = 4
MULTIFX_FX0_KNOB0 = 4
MULTIFX_FX0_KNOB1 = 5
MULTIFX_FX0_KNOB2 = 6
MULTIFX_FX0_COMBOBOX = 7
MULTIFX_FX1_KNOB0 = 8
MULTIFX_FX1_KNOB1 = 9
MULTIFX_FX1_KNOB2 = 10
MULTIFX_FX1_COMBOBOX = 11
MULTIFX_FX2_KNOB0 = 12
MULTIFX_FX2_KNOB1 = 13
MULTIFX_FX2_KNOB2 = 14
MULTIFX_FX2_COMBOBOX = 15
MULTIFX_FX3_KNOB0 = 16
MULTIFX_FX3_KNOB1 = 17
MULTIFX_FX3_KNOB2 = 18
MULTIFX_FX3_COMBOBOX = 19
MULTIFX_FX4_KNOB0 = 20
MULTIFX_FX4_KNOB1 = 21
MULTIFX_FX4_KNOB2 = 22
MULTIFX_FX4_COMBOBOX = 23
MULTIFX_FX5_KNOB0 = 24
MULTIFX_FX5_KNOB1 = 25
MULTIFX_FX5_KNOB2 = 26
MULTIFX_FX5_COMBOBOX = 27
MULTIFX_FX6_KNOB0 = 28
MULTIFX_FX6_KNOB1 = 29
MULTIFX_FX6_KNOB2 = 30
MULTIFX_FX6_COMBOBOX = 31
MULTIFX_FX7_KNOB0 = 32
MULTIFX_FX7_KNOB1 = 33
MULTIFX_FX7_KNOB2 = 34
MULTIFX_FX7_COMBOBOX = 35



MULTIFX_PORT_MAP = {
    "FX0 Knob0": MULTIFX_FX0_KNOB0,
    "FX0 Knob1": MULTIFX_FX0_KNOB1,
    "FX0 Knob2": MULTIFX_FX0_KNOB2,
    "FX1 Knob0": MULTIFX_FX1_KNOB0,
    "FX1 Knob1": MULTIFX_FX1_KNOB1,
    "FX1 Knob2": MULTIFX_FX1_KNOB2,
    "FX2 Knob0": MULTIFX_FX2_KNOB0,
    "FX2 Knob1": MULTIFX_FX2_KNOB1,
    "FX2 Knob2": MULTIFX_FX2_KNOB2,
    "FX3 Knob0": MULTIFX_FX3_KNOB0,
    "FX3 Knob1": MULTIFX_FX3_KNOB1,
    "FX3 Knob2": MULTIFX_FX3_KNOB2,
    "FX4 Knob0": MULTIFX_FX4_KNOB0,
    "FX4 Knob1": MULTIFX_FX4_KNOB1,
    "FX4 Knob2": MULTIFX_FX4_KNOB2,
    "FX5 Knob0": MULTIFX_FX5_KNOB0,
    "FX5 Knob1": MULTIFX_FX5_KNOB1,
    "FX5 Knob2": MULTIFX_FX5_KNOB2,
    "FX6 Knob0": MULTIFX_FX6_KNOB0,
    "FX6 Knob1": MULTIFX_FX6_KNOB1,
    "FX6 Knob2": MULTIFX_FX6_KNOB2,
    "FX7 Knob0": MULTIFX_FX7_KNOB0,
    "FX7 Knob1": MULTIFX_FX7_KNOB1,
    "FX7 Knob2": MULTIFX_FX7_KNOB2,
}



class multifx_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "MULTIFX"
        self.is_instrument = False

        self.preset_manager = preset_manager_widget(
            self.get_plugin_name())
        self.presets_hlayout = QHBoxLayout()
        self.presets_hlayout.addWidget(self.preset_manager.group_box)
        self.presets_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.layout.addLayout(self.presets_hlayout)
        self.spectrum_enabled = None

        self.fx_tab = QWidget()
        self.layout.addWidget(self.fx_tab)
        self.fx_layout = QGridLayout()
        self.fx_hlayout = QHBoxLayout(self.fx_tab)
        self.fx_hlayout.addLayout(self.fx_layout)

        f_knob_size = 48

        f_port = 4
        f_column = 0
        f_row = 0
        for f_i in range(8):
            f_effect = multifx_single(
                "FX{}".format(f_i), f_port,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
            self.effects.append(f_effect)
            self.fx_layout.addWidget(f_effect.group_box, f_row, f_column)
            f_column += 1
            if f_column > 1:
                f_column = 0
                f_row += 1
            f_port += 4

        self.open_plugin_file()
        self.set_midi_learn(MULTIFX_PORT_MAP)
