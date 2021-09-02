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

XFADE_SLIDER = 0
XFADE_MIDPOINT = 1

XFADE_PORT_MAP = {
    "X-Fade": XFADE_SLIDER,
}

XFADE_TOOLTIP = _("""\
Connect one or more tracks to the regular input of this track, and one or
more tracks to the sidechain input of this track, then use the fader to
crossfade between them.
""")

class xfade_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "XFADE"
        self.is_instrument = False
        f_knob_size = DEFAULT_KNOB_SIZE

        self.hlayout = QHBoxLayout()
        self.layout.addLayout(self.hlayout)

        self.volume_gridlayout = QGridLayout()
        self.hlayout.addLayout(self.volume_gridlayout)
        self.volume_slider = slider_control(
            QtCore.Qt.Orientation.Horizontal,
            "X-Fade",
            XFADE_SLIDER,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_DECIMAL,
            self.port_dict,
        )
        self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)
        self.volume_slider.control.setMinimumWidth(300)
        self.volume_slider.value_label.setMinimumWidth(60)
        self.midpoint_knob = knob_control(
            f_knob_size, _("Mid-Point"), XFADE_MIDPOINT,
            self.plugin_rel_callback, self.plugin_val_callback,
            -600, 0, -300, KC_DECIMAL, self.port_dict, None)
        self.midpoint_knob.add_to_grid_layout(self.volume_gridlayout, 1)
        self.midpoint_knob.value_label.setMinimumWidth(60)

        self.hlayout.addWidget(QLabel(XFADE_TOOLTIP))

        self.open_plugin_file()
        self.set_midi_learn(XFADE_PORT_MAP)

    def raise_widget(self):
        AbstractPluginUI.raise_widget(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


