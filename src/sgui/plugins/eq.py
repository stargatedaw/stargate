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

STYLESHEET = """\
QWidget#plugin_groupbox,
QWidget#plugin_window,
QWidget#plugin_ui {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #a4a4a5, stop: 1 #6a6a6a
    );
    border: none;
}

QGroupBox#plugin_groupbox {
    border: 2px solid #222222;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top center */
    padding: 0 3px;
    background-color: #222222;
    border: 2px solid #333333;
    color: #cccccc;
}

QComboBox{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #828282, stop: 1 #6a6a6a
    );
    border: 1px solid #222222;
    border-radius: 6px;
    color: #cccccc;
}

QLabel#plugin_name_label{
    background: none;
    color: #222222;
}

QLabel#plugin_value_label{
    background: none;
    color: #222222;
}

QPushButton {
    background: #222222;
    border: 2px solid #333333;
    color: #cccccc;
}

QPushButton:hover {
    border: 2px solid #cccccc;
}

QTabBar::tab
{
    background-color: #17181d;
    border-bottom-style: none;
    border: 1px solid #444444;
    color: #cccccc;
    margin-right: -1px;
    padding-bottom: 2px;
    padding-left: 10px;
    padding-right: 10px;
    padding-top: 3px;
}


QTabWidget::tab-bar
{
    left: 5px;
}

QTabWidget::pane
{
    /*border: 1px solid #444;*/
    border-top: 2px solid #C2C7CB;
    top: 1px;
}

QTabBar::tab:last
{
    /* the last selected tab has nothing to overlap with on the right */
    margin-right: 0;
}

QTabBar::tab:first:!selected
{
    /* the last selected tab has nothing to overlap with on the right */
    margin-left: 0px;
}

QTabBar::tab:!selected
{
    background-color: #17181d;
    border-bottom-style: solid;
    color: #cccccc;
}

QTabBar::tab:!selected:hover,
QTabBar::tab:selected
{
    background-color: #aaaaaa;
    color: #1e1e1e;
    margin-bottom: 0px;
}

"""

class sgeq_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "SGEQ"
        self.is_instrument = False

        self.preset_manager = None
        self.spectrum_enabled = None
        knob_kwargs = {
            'arc_width_pct': 0.,
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'va1',
                'knob.svg',
            ),
        }
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.eq_tab = QWidget()
        self.eq_layout = QVBoxLayout(self.eq_tab)
        self.tab_widget.addTab(self.eq_tab, _("EQ"))
        self.pre_tab = QWidget()
        self.pre_layout = QGridLayout(self.pre_tab)
        self.tab_widget.addTab(self.pre_tab, _("PreFX"))
        self.post_tab = QWidget()
        self.post_layout = QGridLayout(self.post_tab)
        self.tab_widget.addTab(self.post_tab, _("PostFX"))

        f_knob_size = 48

        self.eq6 = eq6_widget(
            SGEQ_EQ1_FREQ,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            a_size=f_knob_size,
            a_vlayout=False,
            knob_kwargs=knob_kwargs,
        )

        self.eq_layout.addWidget(self.eq6.widget)

        self.spectrum_enabled = null_control(
            SGEQ_SPECTRUM_ENABLED,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            self.port_dict,
        )

        port = 23
        port = self._populate_fx_layout(
            port,
            self.pre_layout,
            knob_kwargs,
            f_knob_size,
        )
        assert port == 47, port
        self._populate_fx_layout(
            port,
            self.post_layout,
            knob_kwargs,
            f_knob_size,
        )

        self.open_plugin_file()
        self.set_midi_learn(SGEQ_PORT_MAP)
        self.enable_spectrum(True)

    def _populate_fx_layout(
        self,
        port,
        layout,
        knob_kwargs,
        f_knob_size,
    ):
        f_column = 0
        f_row = 0
        for f_i in range(6):
            f_effect = multifx_single(
                "FX{}".format(f_i),
                port,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict,
                self.preset_manager,
                a_knob_size=f_knob_size,
                knob_kwargs=knob_kwargs,
            )
            self.effects.append(f_effect)
            layout.addWidget(f_effect.group_box, f_row, f_column)
            f_column += 1
            if f_column > 1:
                f_column = 0
                f_row += 1
            port += 4

        return port

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

