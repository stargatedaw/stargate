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
from .util import get_screws

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

STYLESHEET = """
QWidget#plugin_window {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #191919, stop: 1 #1a1a1a
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/vocoder/logo.svg);
    background-position: left;
    background-repeat: no-repeat;
    border: none;
}

QLabel#plugin_name_label,
QLabel#plugin_value_label {
    background: none;
    color: #555555;
}

"""


class sg_vocoder_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs
        )
        knob_kwargs = {
            'arc_width_pct': 12.,
            'arc_brush': QColor('#f9f9f9'),
            'fg_svg': None,
            'bg_svg': None,
        }
        self._plugin_name = "SG Vocoder"
        self.is_instrument = False
        f_knob_size = DEFAULT_KNOB_SIZE
        self.widget.setMinimumHeight(120)

        self.hlayout = QHBoxLayout()
        self.layout.addLayout(self.hlayout)
        left_screws = get_screws()
        self.hlayout.addLayout(left_screws)
        self.hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        self.groupbox_gridlayout = QGridLayout()
        self.hlayout.addLayout(self.groupbox_gridlayout)

        self.hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        right_screws = get_screws()
        self.hlayout.addLayout(right_screws)

        self.wet_knob = knob_control(
            f_knob_size,
            _("Wet"),
            SG_VOCODER_WET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -500,
            0,
            0,
            KC_TENTH,
            self.port_dict,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'How much wet (vocoded) sound to allow through, in decibels'
            ),
        )
        self.wet_knob.add_to_grid_layout(self.groupbox_gridlayout, 3)

        self.modulator_knob = knob_control(
            f_knob_size,
            _("Modulator"),
            SG_VOCODER_MODULATOR,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -500,
            0,
            -500,
            KC_TENTH,
            self.port_dict,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'How much of the modulator (sidechain) sound to mix in '
                'with the vocoded sound, in decibels'
            )
        )
        self.modulator_knob.add_to_grid_layout(self.groupbox_gridlayout, 9)

        self.carrier_knob = knob_control(
            f_knob_size,
            _("Carrier"),
            SG_VOCODER_CARRIER,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -500,
            0,
            -500,
            KC_TENTH,
            self.port_dict,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'How much of the dry carrier sound to mix in '
                'with the vocoded sound, in decibels'
            )
        )
        self.carrier_knob.add_to_grid_layout(self.groupbox_gridlayout, 6)

        # self.hlayout.addWidget(QLabel(SG_VOCODER_TEXT))

        self.open_plugin_file()
        self.set_midi_learn(SG_VOCODER_PORT_MAP)

    def raise_widget(self):
        AbstractPluginUI.raise_widget(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


