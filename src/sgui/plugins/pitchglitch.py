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
from sglib.lib import util
from .util import get_screws

import copy


PITCHGLITCH_MODE = 4
PITCHGLITCH_PITCHBEND = 5
PITCHGLITCH_DRY_WET = 6
PITCHGLITCH_VEL_MIN = 7
PITCHGLITCH_VEL_MAX = 8
PITCHGLITCH_PAN = 9
PITCHGLITCH_PITCH = 10
PITCHGLITCH_GLIDE = 11


PITCHGLITCH_PORT_MAP = {
    "Wet": PITCHGLITCH_DRY_WET,
#    "Pan": PITCHGLITCH_PAN,
}

STYLESHEET = """
QWidget#plugin_window {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0.5,
        stop: 0 #191919, stop: 1 #171717
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/pitchglitch/logo.svg);
    background-position: left;
    background-repeat: no-repeat;
    border: none;
}

QLineEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #828282, stop: 1 #6a6a6a
    );
    border: 1px solid #222222;
    border-radius: 6px;
    color: #cccccc;
}

QLabel#plugin_name_label,
QLabel#plugin_value_label {
    background: none;
    color: #cccccc;
}

QComboBox::drop-down
{
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

QComboBox::down-arrow
{
    image: url({{ PLUGIN_ASSETS_DIR }}/drop-down.svg);
}

QCheckBox,
QRadioButton
{
    background: none;
    color: #cccccc;
    margin: 3px;
    padding: 0px;
}

QCheckBox::indicator,
QRadioButton::indicator
{
    background-color: #222222;
    border-radius: 6px;
    border: 1px solid #cccccc;
    color: #cccccc;
    height: 18px;
    margin-left: 6px;
    width: 18px;
}

QCheckBox::indicator:checked,
QRadioButton::indicator:checked
{
    background-color: qradialgradient(
        cx: 0.5, cy: 0.5,
        fx: 0.5, fy: 0.5,
        radius: 1.0,
        stop: 0.25 #cccccc,
        stop: 0.3 #222222
    );
}

QPushButton:hover
{
    border: 2px solid #cccccc;
}

QRadioButton::indicator:hover,
QCheckBox::indicator:hover
{
    border: 1px solid #ffffff;
}

QWidget#note_selector {
    background: none;
}
"""


class PitchGlitchUI(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self.widget.setFixedHeight(100)
        self._plugin_name = "PITCHGLITCH"
        self.is_instrument = False

        self.preset_manager = None

        self.main_hlayout = QHBoxLayout()
        self.layout.addLayout(self.main_hlayout)
        left_screws = get_screws()
        self.main_hlayout.addLayout(left_screws)

        f_knob_size = 36 # DEFAULT_KNOB_SIZE
        knob_kwargs = {
            'arc_width_pct': 0.,
            #'arc_width_pct': 6.,
            #'arc_space': 4.,
            #'arc_brush': QColor('#d3544e'),
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'pitchglitch',
                'knob-fg.svg',
            ),
            'bg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'pitchglitch',
                'knob-bg.svg',
            ),
        }

        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.glitch_gridlayout = QGridLayout()
        self.main_hlayout.addLayout(self.glitch_gridlayout)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        pitch_knob_kwargs = copy.deepcopy(knob_kwargs)
        pitch_knob_kwargs['arc_type'] = ArcType.BIDIRECTIONAL
        self.pitch_knob = knob_control(
            f_knob_size,
            _("Pitch"),
            PITCHGLITCH_PITCH,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -36,
            36,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=pitch_knob_kwargs,
            tooltip=(
                'Pitch offset, in semitones.  Play glitches at a different '
                'pitch than the incoming MIDI notes'
            ),
        )
        self.pitch_knob.add_to_grid_layout(self.glitch_gridlayout, 3)

        self.pitchbend_knob = knob_control(
            f_knob_size,
            _("Pbnd"),
            PITCHGLITCH_PITCHBEND,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            36,
            12,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'The maximum amount of pitchbend, in semitones, to apply to '
                'the glitch sound when the pitchbend wheel is fully up or down'
            ),
        )
        self.pitchbend_knob.add_to_grid_layout(self.glitch_gridlayout, 6)

        self.glide_knob = knob_control(
            f_knob_size,
            _("Glide"),
            PITCHGLITCH_GLIDE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            200,
            0,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'The amount of time, in seconds, to glide between note pitches'
            ),
        )
        self.glide_knob.add_to_grid_layout(self.glitch_gridlayout, 9)


        self.wet_knob = knob_control(
            f_knob_size,
            _("Wet"),
            PITCHGLITCH_DRY_WET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            100,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Dry/wet control.  Fully to the left plays the sound without '
                'glitch effect, fully to the right plays with full glitch and '
                'no dry signal while notes are playing'
            ),
        )
        self.wet_knob.add_to_grid_layout(self.glitch_gridlayout, 12)

        right_screws = get_screws()
        self.main_hlayout.addLayout(right_screws)

        self.open_plugin_file()
        self.set_midi_learn(PITCHGLITCH_PORT_MAP)

