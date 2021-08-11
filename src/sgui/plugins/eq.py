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


SGEQ_FIRST_CONTROL_PORT = 4
SGEQ_EQ1_FREQ = 4
SGEQ_EQ1_RES = 5
SGEQ_EQ1_GAIN = 6
SGEQ_EQ2_FREQ = 7
SGEQ_EQ2_RES = 8
SGEQ_EQ2_GAIN = 9
SGEQ_EQ3_FREQ = 10
SGEQ_EQ3_RES = 11
SGEQ_EQ3_GAIN = 12
SGEQ_EQ4_FREQ = 13
SGEQ_EQ4_RES = 14
SGEQ_EQ4_GAIN = 15
SGEQ_EQ5_FREQ = 16
SGEQ_EQ5_RES = 17
SGEQ_EQ5_GAIN = 18
SGEQ_EQ6_FREQ = 19
SGEQ_EQ6_RES = 20
SGEQ_EQ6_GAIN = 21
SGEQ_SPECTRUM_ENABLED = 22

SGEQ_PORT_MAP = {}


class sgeq_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "SGEQ"
        self.is_instrument = False

        self.preset_manager = None
        self.spectrum_enabled = None

        self.layout.setSizeConstraint(
            QLayout.SizeConstraint.SetFixedSize,
        )

        f_knob_size = 48

        self.eq6 = eq6_widget(
            SGEQ_EQ1_FREQ,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager,
            a_size=f_knob_size, a_vlayout=False)

        self.layout.addWidget(self.eq6.widget)

        self.spectrum_enabled = null_control(
            SGEQ_SPECTRUM_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(SGEQ_PORT_MAP)
        self.enable_spectrum(True)

    def open_plugin_file(self):
        AbstractPluginUI.open_plugin_file(self)
        self.eq6.update_viewer()

    def save_plugin_file(self):
        # Don't allow the spectrum analyzer to run at startup
        self.spectrum_enabled.set_value(0)
        AbstractPluginUI.save_plugin_file(self)

    def widget_close(self):
        self.enable_spectrum(False)
        AbstractPluginUI.widget_close(self)

    def widget_show(self):
        self.enable_spectrum(True)

    def enable_spectrum(self, a_enabled):
        if a_enabled:
            self.plugin_val_callback(SGEQ_SPECTRUM_ENABLED, 1.0)
        else:
            self.plugin_val_callback(SGEQ_SPECTRUM_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "spectrum":
            self.eq6.set_spectrum(a_value)
        else:
            AbstractPluginUI.ui_message(a_name, a_value)

