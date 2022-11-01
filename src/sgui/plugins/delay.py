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

STYLESHEET = """\
QWidget,
QMenu,
QMenu::item {
    background: #222222;
    color: #cccccc;
}

QWidget#plugin_window{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #5d1011, stop: 0.5 #711819, stop: 1 #5d1011
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/delay/logo.svg);
    background-position: left;
    background-repeat: no-repeat;
    border: none;
}

QLabel#plugin_name_label,
QLabel#plugin_value_label {
    background: none;
    color: #cccccc;
}
"""

class sgdelay_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "SGDELAY"
        self.is_instrument = False

        knob_kwargs={
            'arc_width_pct': 0.,
            'bg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'gold-knob-bg.svg',
            ),
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'gold-knob-fg.svg',
            ),
        }

        self.main_hlayout = QHBoxLayout()
        left_screws = get_screws()
        self.main_hlayout.addLayout(left_screws)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.layout.addLayout(self.main_hlayout)

        f_knob_size = DEFAULT_LARGE_KNOB_SIZE
        self.preset_manager = None

        self.delay_gridlayout = QGridLayout()
        self.main_hlayout.addLayout(self.delay_gridlayout)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        right_screws = get_screws()
        self.main_hlayout.addLayout(right_screws)

        self.delay_time_knob = knob_control(
            f_knob_size,
            _("Time"),
            SGDELAY_DELAY_TIME,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            10,
            100,
            50,
            KC_TIME_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Delay time in seconds.  The amount of time between echoes'
            ),
        )
        self.delay_time_knob.add_to_grid_layout(self.delay_gridlayout, 0)
        self.feedback = knob_control(
            f_knob_size,
            _("Fdbk"),
            SGDELAY_FEEDBACK,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -200,
            0,
            -120,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Delay feedback in decibels.  How long to echo, how \n'
                'many echoes'
            ),
        )
        self.feedback.add_to_grid_layout(self.delay_gridlayout, 1)
        self.dry_knob = knob_control(
            f_knob_size,
            _("Dry"),
            SGDELAY_DRY,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -300,
            0,
            0,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Dry volume in decibels.  The volume of the input',
        )
        self.dry_knob.add_to_grid_layout(self.delay_gridlayout, 2)
        self.wet_knob = knob_control(
            f_knob_size,
            _("Wet"),
            SGDELAY_WET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -300,
            0,
            -120,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Wet volume in decibels.  The volume of the pure echoes',
        )
        self.wet_knob.add_to_grid_layout(self.delay_gridlayout, 3)
        self.duck_knob = knob_control(
            f_knob_size,
            _("Duck"),
            SGDELAY_DUCK,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -40,
            0,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Smaller values cause the echoes to be reduced in volume\n'
                'when the input signal is louder.  Use to prevent \n'
                'muddy sound, or only to hear echoes during quiet parts'
            ),
        )
        self.duck_knob.add_to_grid_layout(self.delay_gridlayout, 4)
        self.cutoff_knob = knob_control(
            f_knob_size,
            _("Cutoff"),
            SGDELAY_CUTOFF,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            40,
            118,
            90,
            KC_PITCH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Lowpass filter cutoff.  Higher values result in brighter\n'
                'sounding echoes'
            ),
        )
        self.cutoff_knob.add_to_grid_layout(self.delay_gridlayout, 5)
        self.stereo_knob = knob_control(
            f_knob_size,
            _("Stereo"),
            SGDELAY_STEREO,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            100,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Stereo width.  High values result in a left/right \n'
                '"ping-pong" style delay, low values echo in the\n'
                'center of the stereo field'
            ),
        )
        self.stereo_knob.add_to_grid_layout(self.delay_gridlayout, 6)

        self.open_plugin_file()
        self.set_midi_learn(SGDELAY_PORT_MAP)

    def open_plugin_file(self):
        AbstractPluginUI.open_plugin_file(self)

    def save_plugin_file(self):
        AbstractPluginUI.save_plugin_file(self)

    def ui_message(self, a_name, a_value):
        AbstractPluginUI.ui_message(a_name, a_value)


