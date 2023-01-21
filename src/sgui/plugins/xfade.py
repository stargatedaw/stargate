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

XFADE_SLIDER = 0
XFADE_MIDPOINT = 1

XFADE_PORT_MAP = {
    "X-Fade": XFADE_SLIDER,
}

STYLESHEET = """
QWidget#plugin_window {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #05ceb6, stop: 1 #069682
    );
}

QLabel#plugin_name_label,
QLabel#plugin_value_label {
    background: none;
    color: #222222;
}
QSlider
{
    background: transparent;
    border: none;
}

QSlider::groove:horizontal
{
    background: white;
    border-radius: 4px;
    border: 1px solid #bbb;
    height: 4px;
}

QSlider::sub-page:horizontal
{
    background: #222222;
    border-radius: 4px;
    border: 1px solid #777;
    height: 4px;
}

QSlider::add-page:horizontal
{
    background: #222222;
    border-radius: 4px;
    border: 1px solid #777;
    height: 4px;
}

QSlider::handle:horizontal
{
    border: 2px solid transparent;
    image: url({{ PLUGIN_ASSETS_DIR }}/slider-1-h.svg);
    margin-bottom: -30px;
    margin-top: -30px;
}

QLabel#logo {
    background: none;
}
"""

class xfade_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self.widget.setFixedHeight(100)
        self._plugin_name = "XFADE"
        self.is_instrument = False
        f_knob_size = DEFAULT_KNOB_SIZE

        self.hlayout = QHBoxLayout()
        self.layout.addLayout(self.hlayout)
        knob_kwargs = {
            'arc_width_pct': 0.,
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-plastic-3.svg',
            ),
        }
        left_screws = get_screws()
        self.hlayout.addLayout(left_screws)

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
            tooltip=(
                'Crossfade between the regular audio input and the sidechain '
                'input'
            ),
        )
        self.volume_slider.control.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.hlayout.addWidget(self.volume_slider.control)
        self.volume_slider.value_label.setFixedWidth(42)
        self.hlayout.addWidget(self.volume_slider.value_label)
        self.midpoint_knob = knob_control(
            f_knob_size,
            _("Mid-Point"),
            XFADE_MIDPOINT,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -600,
            0,
            -300,
            KC_DECIMAL,
            self.port_dict,
            None,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'The volume gain at the midpoint of the slider.  Used to '
                'prevent a spike in volume when both sounds are playing'
            )
        )
        self.midpoint_knob.add_to_grid_layout(self.volume_gridlayout, 1)
        self.midpoint_knob.value_label.setMinimumWidth(60)

        pixmap = QPixmap(
            os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'xfade',
                'logo.svg',
            )
        )
        self.logo_label = QLabel("")
        self.logo_label.setObjectName("logo")
        self.logo_label.setPixmap(pixmap)
        self.hlayout.addWidget(self.logo_label)
        right_screws = get_screws()
        self.hlayout.addLayout(right_screws)

        self.open_plugin_file()
        self.set_midi_learn(XFADE_PORT_MAP)

    def raise_widget(self):
        AbstractPluginUI.raise_widget(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


