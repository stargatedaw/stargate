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

STYLESHEET = """\
QWidget {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0.5, y2: 1,
        stop: 0 #141414, stop: 0.5 #1a1b1c, stop: 1 #141513
    );
    border: none;
}

QGroupBox#plugin_groupbox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0.25, y2: 1,
        stop: 0 #1b1b58, stop: 0.5 #1c1c5c, stop: 1 #1b1c59
    );
    border: none;
    border-radius: 9px;
    color: #cccccc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
    background-color: none;
    border: none;
}

QLabel {
    background: none;
    color: #cccccc;
}

QComboBox,
QPushButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #828282, stop: 1 #6a6a6a
    );
    border: 1px solid #222222;
    border-radius: 3px;
    color: #222222;
}

QAbstractItemView {
    background-color: #222222;
    border: 2px solid #aaaaaa;
    selection-background-color: #cccccc;
}

QComboBox::drop-down {
    border-bottom-right-radius: 3px;
    border-left-color: #222222;
    border-left-style: solid; /* just a single line */
    border-left-width: 0px;
    border-top-right-radius: 3px; /* same radius as the QComboBox */
    color: #cccccc;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
}

QComboBox::down-arrow {
    image: url({{ PLUGIN_ASSETS_DIR }}/drop-down.svg);
}

QWidget#left_logo {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #141458, stop: 1 #161650
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/multifx/logo-left.svg);
    background-position: center;
    background-repeat: no-repeat;
    border: none;
}

QWidget#right_logo {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #141458, stop: 1 #161650
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/logo-right.svg);
    background-position: center;
    background-repeat: no-repeat;
    border: none;
}

QMenu,
QMenu::item {
    background-color: #222222;
	color: #cccccc;
}

QMenu::separator {
    height: 2px;
    background-color: #cccccc;
}
"""


class multifx_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "MULTIFX"
        self.is_instrument = False
        knob_kwargs = {
            'arc_width_pct': 6.,
            'arc_space': 6,
            'arc_bg_brush': QColor("#5a5a5a"),
            'arc_brush': QColor("#cccccc"),
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-metal-3.svg',
            ),
        }

        self.preset_manager = preset_manager_widget(
            self.get_plugin_name())
        self.presets_hlayout = QHBoxLayout()
        self.presets_hlayout.addWidget(self.preset_manager.group_box)
        self.presets_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.spectrum_enabled = None

        self.main_hlayout = QHBoxLayout()
        self.layout.addLayout(self.main_hlayout)
        left_screws = get_screws()
        left_logo = QWidget()
        left_logo.setObjectName("left_logo")
        left_logo.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum,
        )
        left_logo.setLayout(left_screws)
        self.main_hlayout.addWidget(left_logo)

        self.main_vlayout = QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)
        self.main_vlayout.addLayout(self.presets_hlayout)

        right_screws = get_screws()
        right_logo = QWidget()
        right_logo.setObjectName("right_logo")
        right_logo.setLayout(right_screws)
        right_logo.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum,
        )
        self.main_hlayout.addWidget(right_logo)

        self.fx_layout = QGridLayout()
        self.main_vlayout.addLayout(self.fx_layout)

        f_knob_size = 48

        f_port = 4
        f_column = 0
        f_row = 0
        for i in range(8):
            f_effect = MultiFXSingle(
                f"FX{i}",
                f_port,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict,
                self.preset_manager,
                a_knob_size=f_knob_size,
                knob_kwargs=knob_kwargs,
                fixed_height=True,
            )
            self.effects.append(f_effect)
            self.fx_layout.addWidget(f_effect.group_box, f_row, f_column)
            f_column += 1
            if f_column > 1:
                f_column = 0
                f_row += 1
            f_port += 4

        self.open_plugin_file()
        self.set_midi_learn(MULTIFX_PORT_MAP)

