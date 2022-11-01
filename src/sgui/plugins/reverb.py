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


SREVERB_REVERB_TIME = 0
SREVERB_REVERB_WET = 1
SREVERB_REVERB_COLOR = 2
SREVERB_REVERB_DRY = 3
SREVERB_REVERB_PRE_DELAY = 4
SREVERB_REVERB_HP = 5
SREVERB_WET_PAN = 6
SREVERB_DRY_PAN = 7


SREVERB_PORT_MAP = {
    "Wet": SREVERB_REVERB_WET,
    "Dry": SREVERB_REVERB_DRY,
    "LP": SREVERB_REVERB_COLOR,
    "HP": SREVERB_REVERB_HP,
    "Dry Pan": SREVERB_DRY_PAN,
    "Wet Pan": SREVERB_WET_PAN,
}

STYLESHEET = """\
QWidget#transparent {
    background: none;
}

QWidget#plugin_window {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #E1EF87, stop: 0.33 #ADC038,
        stop: 0.75 #D6E387, stop: 1 #C9E755
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/reverb/logo.svg);
    background-position: left;
    background-repeat: no-repeat;
    border: none;
}

QComboBox,
QPushButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #828282, stop: 1 #6a6a6a
    );
    border: 1px solid #222222;
    border-radius: 6px;
    color: #cccccc;
}

QLabel#plugin_value_label,
QLabel#plugin_name_label
{
    background-color: none;
    border: none;
    color: #222222;
}

"""

class ReverbPluginUI(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs
        )
        self._plugin_name = "SREVERB"
        self.is_instrument = False

        self.preset_manager = preset_manager_widget(
            self.get_plugin_name(),
        )
        self.main_hlayout = QHBoxLayout()
        left_screws = get_screws()
        self.main_hlayout.addLayout(left_screws)
        self.layout.addLayout(self.main_hlayout)

        f_knob_size = 75

        self.main_vlayout = QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)

        self.preset_manager.group_box.setObjectName('transparent')
        self.preset_manager.bank_label.setObjectName('plugin_name_label')
        self.preset_manager.presets_label.setObjectName('plugin_name_label')
        self.hlayout0 = QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout0)

        self.hlayout0.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.hlayout0.addWidget(self.preset_manager.group_box)
        self.reverb_groupbox_gridlayout = QGridLayout()
        self.main_vlayout.addLayout(self.reverb_groupbox_gridlayout)
        self.reverb_groupbox_gridlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
            1,
            0,
        )
        self.reverb_groupbox_gridlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
            1,
            30,
        )
        right_screws = get_screws()
        self.main_hlayout.addLayout(right_screws)

        knob_gradient = QLinearGradient(0., 0., f_knob_size, 0.)
        knob_gradient.setColorAt(0., QColor("#0000cc"))
        knob_gradient.setColorAt(1., QColor("#cc0000"))

        knob_kwargs = {
            'arc_width_pct': 20.,
            'fg_svg': None,
            'arc_brush': knob_gradient,
            'arc_bg_brush': QColor("#5a5a5a"),
        }
        self.reverb_time_knob = knob_control(
            f_knob_size,
            _("Size"),
            SREVERB_REVERB_TIME,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            50,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Higher values result in longer reverb tails',
        )
        self.reverb_time_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            3,
        )

        self.reverb_dry_knob = knob_control(
            f_knob_size,
            _("Dry"),
            SREVERB_REVERB_DRY,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -500,
            0,
            0,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Dry volume.  The volume of the input signal',
        )
        self.reverb_dry_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            9,
        )

        self.reverb_wet_knob = knob_control(
            f_knob_size,
            _("Wet"),
            SREVERB_REVERB_WET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -500,
            0,
            -120,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Wet volume.  The volume of the pure reverb sound',
        )
        self.reverb_wet_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            10,
        )

        self.reverb_hp_knob = knob_control(
            f_knob_size,
            _("HP"),
            SREVERB_REVERB_HP,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            20,
            96,
            50,
            KC_PITCH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Highpass filter frequency in hertz.  Highe values \n'
                'reduce muddiness and rumbling in the wet sound.'
            ),
        )
        self.reverb_hp_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            15,
        )

        self.reverb_lp_knob = knob_control(
            f_knob_size,
            _("LP"),
            SREVERB_REVERB_COLOR,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            48,
            120,
            90,
            KC_PITCH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Lowpass filter frequency in hertz.  Lower values result\n'
                'in a soft reverb, high values result in a bright reverb'
            ),
        )
        self.reverb_lp_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            16,
        )

        self.reverb_predelay_knob = knob_control(
            f_knob_size,
            _("PreDelay"),
            SREVERB_REVERB_PRE_DELAY,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            1000,
            10,
            KC_MILLISECOND,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Pre-delay in milliseconds.  The wet signal will be delayed\n'
                'by this much time'
            ),
        )
        self.reverb_predelay_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            21,
        )
        knob_kwargs['arc_type'] = ArcType.BIDIRECTIONAL
        self.dry_pan_knob = knob_control(
            f_knob_size,
            _("Dry Pan"),
            SREVERB_DRY_PAN,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Pan the dry signal left or right',
        )
        self.dry_pan_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            23,
        )
        self.wet_pan_knob = knob_control(
            f_knob_size,
            _("Wet Pan"),
            SREVERB_WET_PAN,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Pan the wet signal left or right',
        )
        self.wet_pan_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout,
            24,
        )

        knob_kwargs.pop('arc_type')

        self.open_plugin_file()
        self.set_midi_learn(SREVERB_PORT_MAP)

    def open_plugin_file(self):
        AbstractPluginUI.open_plugin_file(self)

    def save_plugin_file(self):
        # Don't allow the spectrum analyzer to run at startup
        AbstractPluginUI.save_plugin_file(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


