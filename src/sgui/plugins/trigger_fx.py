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


TRIGGERFX_INPUT0 = 0
TRIGGERFX_INPUT1 = 1
TRIGGERFX_OUTPUT0 = 2
TRIGGERFX_OUTPUT1 = 3
TRIGGERFX_FIRST_CONTROL_PORT = 4
TRIGGERFX_GATE_NOTE = 4
TRIGGERFX_GATE_MODE = 5
TRIGGERFX_GATE_WET = 6
TRIGGERFX_GATE_PITCH = 7
TRIGGERFX_GLITCH_ON = 8
TRIGGERFX_GLITCH_NOTE = 9
TRIGGERFX_GLITCH_TIME = 10
TRIGGERFX_GLITCH_PB = 11


TRIGGERFX_PORT_MAP = {
    "Gate Wet": TRIGGERFX_GATE_WET,
    "Glitch Time": TRIGGERFX_GLITCH_TIME
}

STYLESHEET = """
QWidget#plugin_window {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #339933, stop: 0.5 #33743f, stop: 1 #339833
    );
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
    color: #222222;
}

QLabel#plugin_name_label,
QLabel#plugin_value_label {
    background: none;
    color: #222222;
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

QLabel#logo {
    background: none;
}
"""


class triggerfx_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "TRIGGERFX"
        self.is_instrument = False

        self.preset_manager = None

        self.main_hlayout = QHBoxLayout()
        self.layout.addLayout(self.main_hlayout)
        left_screws = get_screws()
        self.main_hlayout.addLayout(left_screws)

        f_knob_size = DEFAULT_KNOB_SIZE
        knob_kwargs = {
            'arc_width_pct': 0.,
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-plastic-3.svg',
            ),
        }

        self.gate_gridlayout = QGridLayout()
        self.main_hlayout.addLayout(self.gate_gridlayout)
        self.main_hlayout.addLayout
        self.gate_on_checkbox = checkbox_control(
            "Gate",
            TRIGGERFX_GATE_MODE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            tooltip=(
                'Enable the MIDI triggered gate.  Audio will be muted except '
                'when the trigger note is being played.'
            ),
        )
        self.gate_on_checkbox.add_to_grid_layout(self.gate_gridlayout, 3)
        self.gate_note_selector = NoteSelectorWidget(
            TRIGGERFX_GATE_NOTE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            120,
            self.preset_manager,
            name_label="Trigger Note",
        )
        self.gate_note_selector.add_to_grid_layout(self.gate_gridlayout, 6)
        self.gate_wet_knob = knob_control(
            f_knob_size,
            _("Wet"),
            TRIGGERFX_GATE_WET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            0,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Dry/wet control, 1.0 for full wet sound, 0.0 for full '
                'dry sound'
            ),
        )
        self.gate_wet_knob.add_to_grid_layout(self.gate_gridlayout, 9)

        self.gate_pitch_knob = knob_control(
            f_knob_size,
            _("Pitch"),
            TRIGGERFX_GATE_PITCH,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            20,
            120,
            60,
            KC_PITCH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                "High values cause the gate to open and close very quickly, "
                "low values cause it to open and close more slowly"
            ),
        )
        self.gate_pitch_knob.add_to_grid_layout(self.gate_gridlayout, 12)

        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        pixmap = QPixmap(
            os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'triggerfx',
                'logo.svg',
            )
        )
        self.logo_label = QLabel("")
        self.logo_label.setObjectName("logo")
        self.logo_label.setPixmap(pixmap)
        self.main_hlayout.addWidget(self.logo_label)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.glitch_gridlayout = QGridLayout()
        self.main_hlayout.addLayout(self.glitch_gridlayout)

        self.glitch_on_checkbox = checkbox_control(
            "Glitch",
            TRIGGERFX_GLITCH_ON,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            tooltip=(
                'Enable/disable glitch.  Plays the audio input on short '
                'repeat when the trigger note is played'
            ),
        )
        self.glitch_on_checkbox.add_to_grid_layout(self.glitch_gridlayout, 3)
        self.glitch_note_selector = NoteSelectorWidget(
            TRIGGERFX_GLITCH_NOTE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            119,
            self.preset_manager,
            name_label="Trigger Note",
        )
        self.glitch_note_selector.add_to_grid_layout(self.glitch_gridlayout, 6)
        self.glitch_time_knob = knob_control(
            f_knob_size,
            _("Time"),
            TRIGGERFX_GLITCH_TIME,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            1,
            25,
            10,
            KC_TIME_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='The length of the repeat in seconds',
        )
        self.glitch_time_knob.add_to_grid_layout(self.glitch_gridlayout, 9)
        self.glitch_pb_knob = knob_control(
            f_knob_size,
            _("Pitchbend"),
            TRIGGERFX_GLITCH_PB,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            36,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'How much pitchbend affects pitch, in semitones, while the '
                'trigger note is pressed'
            ),
        )
        self.glitch_pb_knob.add_to_grid_layout(self.glitch_gridlayout, 12)
        right_screws = get_screws()
        self.main_hlayout.addLayout(right_screws)

        self.open_plugin_file()
        self.set_midi_learn(TRIGGERFX_PORT_MAP)

