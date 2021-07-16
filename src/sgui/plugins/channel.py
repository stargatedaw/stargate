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

SGCHNL_VOL_SLIDER = 0
SGCHNL_GAIN = 1
SGCHNL_PAN = 2
SGCHNL_LAW = 3

SGCHNL_PORT_MAP = {
    "Volume": SGCHNL_VOL_SLIDER,
    "Pan": SGCHNL_PAN,
}

class sgchnl_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "SGCHNL"
        self.is_instrument = False
        f_knob_size = 42
        self.gain_gridlayout = QGridLayout()
        if self.is_mixer:
            self.layout.addLayout(self.gain_gridlayout)
        else:
            self.hlayout = QHBoxLayout()
            self.layout.addLayout(self.hlayout)
            self.hlayout.addLayout(self.gain_gridlayout)
        self.gain_knob = knob_control(
            f_knob_size, _("Gain"), SGCHNL_GAIN,
            self.plugin_rel_callback, self.plugin_val_callback,
            -2400, 2400, 0, KC_DECIMAL, self.port_dict, None)
        self.gain_knob.add_to_grid_layout(self.gain_gridlayout, 0)
        self.gain_knob.value_label.setMinimumWidth(55)

        self.pan_knob = knob_control(
            f_knob_size, _("Pan"), SGCHNL_PAN,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict, None)
        self.pan_knob.add_to_grid_layout(self.gain_gridlayout, 1)
        self.pan_law_knob = knob_control(
            f_knob_size, _("Law"), SGCHNL_LAW,
            self.plugin_rel_callback, self.plugin_val_callback,
            -600, 0, -300, KC_DECIMAL, self.port_dict, None)
        self.pan_law_knob.add_to_grid_layout(self.gain_gridlayout, 2)

        self.volume_gridlayout = QGridLayout()
        self.layout.addLayout(self.volume_gridlayout)
        self.volume_slider = slider_control(
            QtCore.Qt.Orientation.Vertical if self.is_mixer
                else QtCore.Qt.Orientation.Horizontal,
            "Vol", SGCHNL_VOL_SLIDER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -5000, 0, 0, KC_DECIMAL, self.port_dict)
        if self.is_mixer:
            self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)
            self.volume_slider.control.setSizePolicy(
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        else:
            self.volume_slider_layout = QGridLayout()
            self.volume_slider_layout.setSizeConstraint(QLayout.SetMaximumSize)
            self.hlayout.addLayout(self.volume_slider_layout, 1)
            self.volume_slider.add_to_grid_layout(
                self.volume_slider_layout, 0, a_alignment=None)
        self.volume_slider.value_label.setMinimumWidth(180)
        self.open_plugin_file()
        self.set_midi_learn(SGCHNL_PORT_MAP)

    def plugin_rel_callback(self, a_val1=None, a_val2=None):
        self.save_plugin_file()
