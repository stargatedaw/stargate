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

SFADER_VOL_SLIDER = 0

SFADER_PORT_MAP = {
    "Volume Slider": SFADER_VOL_SLIDER,
}

class sfader_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "SFADER"
        self.is_instrument = False
        self.volume_gridlayout = QGridLayout()
        self.layout.addLayout(self.volume_gridlayout, 1)
        self.volume_slider = slider_control(
            QtCore.Qt.Orientation.Vertical if self.is_mixer
                else QtCore.Qt.Orientation.Horizontal,
            "Vol", SFADER_VOL_SLIDER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -5000, 0, 0, KC_DECIMAL, self.port_dict)
        if self.is_mixer:
            self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)
            self.volume_slider.control.setSizePolicy(
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        else:
            self.volume_slider.add_to_grid_layout(
                self.volume_gridlayout, 0, a_alignment=None)
        self.volume_slider.value_label.setMinimumWidth(91)
        self.open_plugin_file()
        self.set_midi_learn(SFADER_PORT_MAP)

    def plugin_rel_callback(self, a_val1=None, a_val2=None):
        self.save_plugin_file()



