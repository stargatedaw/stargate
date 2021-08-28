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
import os

VA1_OUTPUT0 = 0
VA1_OUTPUT1 = 1
VA1_FIRST_CONTROL_PORT = 2
VA1_ATTACK = 2
VA1_DECAY = 3
VA1_SUSTAIN = 4
VA1_RELEASE = 5
VA1_TIMBRE = 6
VA1_RES = 7
VA1_DIST = 8
VA1_FILTER_ATTACK = 9
VA1_FILTER_DECAY = 10
VA1_FILTER_SUSTAIN = 11
VA1_FILTER_RELEASE = 12
VA1_NOISE_AMP = 13
VA1_FILTER_ENV_AMT = 14
VA1_DIST_WET = 15
VA1_OSC1_TYPE = 16
VA1_OSC1_PITCH = 17
VA1_OSC1_TUNE = 18
VA1_OSC1_VOLUME = 19
VA1_OSC2_TYPE = 20
VA1_OSC2_PITCH = 21
VA1_OSC2_TUNE = 22
VA1_OSC2_VOLUME = 23
VA1_MAIN_VOLUME = 24
VA1_UNISON_VOICES1 = 25
VA1_UNISON_SPREAD1 = 26
VA1_MAIN_GLIDE = 27
VA1_MAIN_PITCHBEND_AMT = 28
VA1_PITCH_ENV_TIME = 29
VA1_PITCH_ENV_AMT = 30
VA1_LFO_FREQ = 31
VA1_LFO_TYPE = 32
VA1_LFO_AMP = 33
VA1_LFO_PITCH = 34
VA1_LFO_FILTER = 35
VA1_OSC_HARD_SYNC = 36
VA1_RAMP_CURVE = 37
VA1_FILTER_KEYTRK = 38
VA1_MONO_MODE = 39
VA1_LFO_PHASE = 40
VA1_LFO_PITCH_FINE = 41
VA1_ADSR_PREFX = 42
VA1_MIN_NOTE = 43
VA1_MAX_NOTE = 44
VA1_MAIN_PITCH = 45
VA1_UNISON_VOICES2 = 46
VA1_UNISON_SPREAD2 = 47
VA1_NOISE_TYPE = 48
VA1_FILTER_TYPE = 49
VA1_FILTER_VELOCITY = 50
VA1_DIST_OUTGAIN = 51
VA1_OSC1_PB = 52
VA1_OSC2_PB = 53
VA1_DIST_TYPE = 54
VA1_ADSR_LIN_MAIN = 55


VA1_PORT_MAP = {
    "Attack": "2",
    "Decay": "3",
    "Sustain": "4",
    "Release": "5",
    "Filter Cutoff": "6",
    "Res": "7",
    "Dist": "8",
    "Attack Filter": "9",
    "Decay Filter": "10",
    "Sustain Filter": "11",
    "Release Filter": "12",
    "Noise Amp": "13",
    "Filter Env Amt": "14",
    "Dist Wet": "15",
    "Main Glide": "27",
    "Pitch Env Time": "29",
    "Pitch Env Amt": "30",
    "LFO Freq": "31",
    "LFO Amp": "33",
    "LFO Pitch": "34",
    "LFO Pitch Fine": VA1_LFO_PITCH_FINE,
    "LFO Filter": "35"
}

STYLESHEET = """\
QWidget {
    background: none;
    color: #cccccc;
}

QPushButton,
QWidget#plugin_window {
    background: #1c1c1c;
}

QGroupBox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #6a1111, stop: 0.5 #5f1c1c, stop: 1 #6a1111
    );
    border: 2px solid #cccccc;
    color: #cccccc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* position at the top center */
    padding: 0 3px;
    background-color: #6a1111;
    border: 2px solid #cccccc;
}

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

"""


class VA1PluginUI(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "VA1"
        self.is_instrument = True
        f_osc_types = [
            _("Off"),
            _("Saw"),
            _("Square"),
            _("H-Square"),
            _("Q-Square"),
            _("Triangle"),
            _("Sine")
        ]
        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]
        self.preset_manager = preset_manager_widget(
            self.get_plugin_name())
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.layout.addLayout(self.main_layout)
        self.layout.setSizeConstraint(
            QLayout.SizeConstraint.SetFixedSize,
        )
        self.hlayout0 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout0)
        self.hlayout0.addWidget(self.preset_manager.group_box)
        self.hlayout0.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        f_knob_size = 42
        knob_kwargs = {
            'arc_width_pct': 0.0,
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-va1.svg',
            ),
        }

        self.hlayout1 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout1)
        self.osc1 = osc_widget(
            f_knob_size,
            VA1_OSC1_PITCH,
            VA1_OSC1_TUNE,
            VA1_OSC1_VOLUME,
            VA1_OSC1_TYPE,
            f_osc_types,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            _("Oscillator 1"),
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            a_default_type=1,
            a_uni_voices_port=VA1_UNISON_VOICES1,
            a_uni_spread_port=VA1_UNISON_SPREAD1,
            a_pb_port=VA1_OSC1_PB,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout1.addWidget(self.osc1.group_box)
        self.osc2 = osc_widget(
            f_knob_size,
            VA1_OSC2_PITCH,
            VA1_OSC2_TUNE,
            VA1_OSC2_VOLUME,
            VA1_OSC2_TYPE,
            f_osc_types,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            _("Oscillator 2"),
            self.port_dict,
            self.preset_manager,
            a_uni_voices_port=VA1_UNISON_VOICES2,
            a_uni_spread_port=VA1_UNISON_SPREAD2,
            a_pb_port=VA1_OSC2_PB,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout1.addWidget(self.osc2.group_box)
        self.hlayout2 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout2)
        self.adsr_amp = adsr_widget(
            f_knob_size,
            True,
            VA1_ATTACK,
            VA1_DECAY,
            VA1_SUSTAIN,
            VA1_RELEASE,
            _("ADSR Amp"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_prefx_port=VA1_ADSR_PREFX,
            a_knob_type=KC_LOG_TIME,
            a_lin_port=VA1_ADSR_LIN_MAIN,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout2.addWidget(self.adsr_amp.groupbox)
        self.adsr_filter = adsr_widget(
            f_knob_size,
            False,
            VA1_FILTER_ATTACK,
            VA1_FILTER_DECAY,
            VA1_FILTER_SUSTAIN,
            VA1_FILTER_RELEASE,
            _("ADSR Filter"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout2.addWidget(self.adsr_filter.groupbox)
        self.pitch_env = ramp_env_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            VA1_PITCH_ENV_TIME,
            VA1_PITCH_ENV_AMT,
            _("Pitch Env"),
            self.preset_manager,
            VA1_RAMP_CURVE,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout2.addWidget(self.pitch_env.groupbox)

        self.hlayout3 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout3)
        self.dist_widget = MultiDistWidget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            VA1_DIST,
            VA1_DIST_WET,
            VA1_DIST_OUTGAIN,
            VA1_DIST_TYPE,
            a_preset_mgr=self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout3.addWidget(self.dist_widget.groupbox_dist)

        self.filter = filter_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            VA1_TIMBRE,
            VA1_RES,
            a_preset_mgr=self.preset_manager,
            a_type_port=VA1_FILTER_TYPE,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout3.addWidget(self.filter.groupbox)
        self.filter_env_amt = knob_control(
            f_knob_size,
            _("Env Amt"),
            VA1_FILTER_ENV_AMT,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.filter_env_amt.add_to_grid_layout(self.filter.layout, 10)
        self.filter_keytrk = knob_control(
            f_knob_size,
            _("KeyTrk"),
            VA1_FILTER_KEYTRK,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            0,
            KC_NONE,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.filter_keytrk.add_to_grid_layout(self.filter.layout, 11)
        self.filter_velocity = knob_control(
            f_knob_size,
            _("Vel."),
            VA1_FILTER_VELOCITY,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            0,
            KC_NONE,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.filter_velocity.add_to_grid_layout(self.filter.layout, 12)

        self.hard_sync = checkbox_control(
            "Sync",
            VA1_OSC_HARD_SYNC,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
        )
        self.hard_sync.control.setToolTip(
            _("Setting this hard sync's Osc1 to Osc2. Usually you "
            "would want to pitchbend Osc2 up if this is enabled."))
        self.osc2.grid_layout.addWidget(
            self.hard_sync.control,
            1,
            30,
            QtCore.Qt.AlignmentFlag.AlignCenter,
        )

        self.groupbox_noise = QGroupBox(_("Noise"))
        self.groupbox_noise.setObjectName("plugin_groupbox")
        self.noise_layout = QGridLayout(self.groupbox_noise)
        self.noise_layout.setContentsMargins(3, 3, 3, 3)
        self.hlayout3.addWidget(self.groupbox_noise)
        self.noise_amp = knob_control(
            f_knob_size,
            _("Vol"),
            VA1_NOISE_AMP,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -60,
            0,
            -30,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.noise_amp.add_to_grid_layout(self.noise_layout, 0)

        self.noise_type = combobox_control(
            87,
            _("Type"),
            VA1_NOISE_TYPE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            [_("Off"), _("White"), _("Pink")],
            self.port_dict,
            a_preset_mgr=self.preset_manager,
        )
        self.noise_type.control.setMaximumWidth(87)
        self.noise_type.add_to_grid_layout(self.noise_layout, 1)

        self.hlayout4 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout4)
        self.main = main_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            VA1_MAIN_VOLUME,
            VA1_MAIN_GLIDE,
            VA1_MAIN_PITCHBEND_AMT,
            self.port_dict,
            _("Main"),
            None,
            None,
            self.preset_manager,
            a_poly_port=VA1_MONO_MODE,
            a_min_note_port=VA1_MIN_NOTE,
            a_max_note_port=VA1_MAX_NOTE,
            a_pitch_port=VA1_MAIN_PITCH,
            a_pb_min=0,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout4.addWidget(self.main.group_box)

        self.lfo = lfo_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            VA1_LFO_FREQ,
            VA1_LFO_TYPE,
            f_lfo_types,
            _("LFO"),
            self.preset_manager,
            VA1_LFO_PHASE,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout4.addWidget(self.lfo.groupbox)

        self.lfo_amp = knob_control(
            f_knob_size,
            _("Amp"),
            VA1_LFO_AMP,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -24,
            24,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_amp.add_to_grid_layout(self.lfo.layout, 7)
        self.lfo_pitch = knob_control(
            f_knob_size,
            _("Pitch"),
            VA1_LFO_PITCH,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -36,
            36,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 8)

        self.lfo_pitch_fine = knob_control(
            f_knob_size,
            _("Fine"),
            VA1_LFO_PITCH_FINE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 9)

        self.lfo_cutoff = knob_control(
            f_knob_size,
            _("Filter"),
            VA1_LFO_FILTER,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -48,
            48,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_cutoff.add_to_grid_layout(self.lfo.layout, 10)

        self.open_plugin_file()
        self.set_midi_learn(VA1_PORT_MAP)

