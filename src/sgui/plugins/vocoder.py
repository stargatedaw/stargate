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

SG_VOCODER_WET = 0
SG_VOCODER_MODULATOR = 1
SG_VOCODER_CARRIER = 2

SG_VOCODER_PORT_MAP = {
    "Wet":SG_VOCODER_WET,
    "Modulator":SG_VOCODER_MODULATOR,
    "Carrier":SG_VOCODER_CARRIER,
}

SG_VOCODER_TEXT = _(
"""Route the carrier signal to the plugin's main input,
and route the modulator signal to the track's
sidechain input.""")


class sg_vocoder_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "SG Vocoder"
        self.is_instrument = False
        f_knob_size = DEFAULT_KNOB_SIZE
        self.widget.setMinimumHeight(120)

        self.hlayout = QHBoxLayout()
        self.layout.addLayout(self.hlayout)
        self.groupbox_gridlayout = QGridLayout()
        self.hlayout.addLayout(self.groupbox_gridlayout)

        self.wet_knob = knob_control(
            f_knob_size, _("Wet"), SG_VOCODER_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, 0, KC_TENTH, self.port_dict)
        self.wet_knob.add_to_grid_layout(self.groupbox_gridlayout, 3)

        self.modulator_knob = knob_control(
            f_knob_size, _("Modulator"), SG_VOCODER_MODULATOR,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, -500, KC_TENTH, self.port_dict)
        self.modulator_knob.add_to_grid_layout(self.groupbox_gridlayout, 9)

        self.carrier_knob = knob_control(
            f_knob_size, _("Carrier"), SG_VOCODER_CARRIER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, -500, KC_TENTH, self.port_dict)
        self.carrier_knob.add_to_grid_layout(self.groupbox_gridlayout, 6)

        self.hlayout.addWidget(QLabel(SG_VOCODER_TEXT))

        self.open_plugin_file()
        self.set_midi_learn(SG_VOCODER_PORT_MAP)

    def raise_widget(self):
        AbstractPluginUI.raise_widget(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


