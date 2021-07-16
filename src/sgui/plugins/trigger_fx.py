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



class triggerfx_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "TRIGGERFX"
        self.is_instrument = False

        self.preset_manager = None
        self.layout.setSizeConstraint(
            QLayout.SizeConstraint.SetFixedSize,
        )

        self.delay_hlayout = QHBoxLayout()
        self.layout.addLayout(self.delay_hlayout)

        f_knob_size = DEFAULT_KNOB_SIZE

        self.delay_hlayout.addWidget(QLabel(_("Gate")))
        self.gate_gridlayout = QGridLayout()
        self.delay_hlayout.addLayout(self.gate_gridlayout)
        self.delay_hlayout.addLayout
        self.gate_on_checkbox = checkbox_control(
            "On", TRIGGERFX_GATE_MODE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager)
        self.gate_on_checkbox.add_to_grid_layout(self.gate_gridlayout, 3)
        self.gate_note_selector = note_selector_widget(
            TRIGGERFX_GATE_NOTE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, 120, self.preset_manager)
        self.gate_note_selector.add_to_grid_layout(self.gate_gridlayout, 6)
        self.gate_wet_knob = knob_control(
            f_knob_size, _("Wet"), TRIGGERFX_GATE_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.gate_wet_knob.add_to_grid_layout(self.gate_gridlayout, 9)

        self.gate_pitch_knob = knob_control(
            f_knob_size, _("Pitch"), TRIGGERFX_GATE_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            20, 120, 60, KC_PITCH, self.port_dict, self.preset_manager)
        self.gate_pitch_knob.add_to_grid_layout(self.gate_gridlayout, 12)

        self.delay_hlayout.addWidget(QLabel(_("Glitch")))
        self.glitch_gridlayout = QGridLayout()
        self.delay_hlayout.addLayout(self.glitch_gridlayout)

        self.glitch_on_checkbox = checkbox_control(
            "On", TRIGGERFX_GLITCH_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager)
        self.glitch_on_checkbox.add_to_grid_layout(self.glitch_gridlayout, 3)
        self.glitch_note_selector = note_selector_widget(
            TRIGGERFX_GLITCH_NOTE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, 119, self.preset_manager)
        self.glitch_note_selector.add_to_grid_layout(self.glitch_gridlayout, 6)
        self.glitch_time_knob = knob_control(
            f_knob_size, _("Time"), TRIGGERFX_GLITCH_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            1, 25, 10, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.glitch_time_knob.add_to_grid_layout(self.glitch_gridlayout, 9)
        self.glitch_pb_knob = knob_control(
            f_knob_size, _("Pitchbend"), TRIGGERFX_GLITCH_PB,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.glitch_pb_knob.add_to_grid_layout(self.glitch_gridlayout, 12)

        f_note_triggered_label = QLabel(_(
            _("The effects are triggered when you play their \n"
            "selected note.  Usually you will want to change the note\n"
            "range on any instrument plugins on the same track to not\n"
            "include the selected note for these effects.")))
        self.delay_hlayout.addWidget(f_note_triggered_label)

        self.open_plugin_file()
        self.set_midi_learn(TRIGGERFX_PORT_MAP)

