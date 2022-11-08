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

NABU_FX_COUNT = 12

NABU_FIRST_CONTROL_PORT = 4
NABU_FIRST_FREQ_SPLITTER_PORT = NABU_FIRST_CONTROL_PORT + (NABU_FX_COUNT * 15)
NABU_UI_MSG_ENABLED_PORT = 194

ROUTE_TOOLTIP = """\
If effect is on, but not routed to by splitter or another active effect, it
will use audio input.  Use for parallel processing.  If routed to an effect
that is off, will be routed to output
"""

def _port_map():
    port_map = {}
    port = NABU_FIRST_CONTROL_PORT
    for i in range(NABU_FX_COUNT):
        for j in range(10):
            port_map[f"FX{i + 1:02} Knob{j + 1:02}"] = port
            port += 1
        port_map[f"FX{i + 1:02} Dry"] = port + 2
        port_map[f"FX{i + 1:02} Wet"] = port + 3
        port_map[f"FX{i + 1:02} D/W Pan"] = port + 4
        port += 5
    return port_map

NABU_PORT_MAP = _port_map()

STYLESHEET = """
QWidget {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #151412, stop: 0.5 #141614, stop: 1 #151515
    );
    border: none;
}

QGroupBox#plugin_groupbox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #222222, stop: 0.5 #272727, stop: 1 #242523
    );
    border: none;
    border-radius: 6px;
    color: #cccccc;
}

QGroupBox::title {
    background: #333333;
    subcontrol-origin: margin;
    subcontrol-position: top center; /* position at the top center */
    padding: 0 3px;
    border: none;
    border-radius: 2px;
}

QLabel#plugin_name_label,
QLabel#plugin_value_label {
    background: none;
    color: #cccccc;
}

QComboBox,
QPushButton#nested_combobox
{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #727273, stop: 1 #6a6a6a
    );
    border: 1px solid #222222;
    border-radius: 2px;
    color: #222222;
}

QAbstractItemView
{
    background-color: #222222;
    border: 2px solid #aaaaaa;
    selection-background-color: #cccccc;
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

QMenu,
QMenu::item {
    background-color: #222222;
	color: #cccccc;
}

QMenu::separator
{
    height: 2px;
    background-color: #cccccc;
}
"""


class NabuPluginUI(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "NABU"
        self.is_instrument = False
        f_knob_size = 48
        knob_kwargs = {
            'arc_width_pct': 20.,
            'arc_bg_brush': QColor("#5a5a5a"),
            'arc_brush': QColor("#5555cc"),
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-metal-3.svg',
            ),
        }

        self.preset_manager = preset_manager_widget(
            self.get_plugin_name(),
        )
        self.presets_hlayout = QHBoxLayout()
        self.presets_hlayout.addWidget(self.preset_manager.group_box)
        self.presets_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.layout.addLayout(self.presets_hlayout)
        self.ui_msg_enabled = null_control(
            NABU_UI_MSG_ENABLED_PORT,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            self.port_dict,
        )
        self.freq_splitter = FreqSplitter(
            f_knob_size,
            64,
            NABU_FIRST_FREQ_SPLITTER_PORT,
            [f'FX{x + 1}' for x in range(12)] + ["Out"],
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            knob_kwargs,
        )
        self.freq_splitter.layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
            1,
            15,
        )
        self.freq_splitter.layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
            1,
            100,
        )
        self.layout.addWidget(self.freq_splitter.widget)
        self.spectrum_enabled = None

        self.fx_scrollarea = QScrollArea()
        self.fx_scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
        )
        self.fx_scrollarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.fx_scrollarea.setWidgetResizable(True)
        self.layout.addWidget(self.fx_scrollarea)
        self.fx_scrollarea_widget = QWidget()
        self.fx_layout = QVBoxLayout()
        self.fx_scrollarea_widget.setLayout(self.fx_layout)
        self.fx_scrollarea.setFixedHeight(500)
        self.fx_scrollarea.setWidget(self.fx_scrollarea_widget)

        self.peak_meters = []
        peak_gradient = QLinearGradient(0., 0., 0., 100.)
        peak_gradient.setColorAt(0.0, QColor("#cc2222"))
        peak_gradient.setColorAt(0.09, QColor("#cc2222"))
        peak_gradient.setColorAt(0.1, QColor("#22cc22"))
        peak_gradient.setColorAt(1.0, QColor("#22cc22"))

        f_port = 4
        for i in range(NABU_FX_COUNT):
            f_effect = MultiFX10(
                i,
                NABU_FX_COUNT,
                f_port,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict,
                self.preset_manager,
                a_knob_size=f_knob_size,
                knob_kwargs=knob_kwargs,
                fixed_height=True,
            )
            f_effect.route_combobox.control.setToolTip(ROUTE_TOOLTIP)
            peak_meters = (
                peak_meter(16, False, brush=peak_gradient),
                peak_meter(16, False, brush=peak_gradient),
            )
            self.peak_meters.append(peak_meters)
            f_effect.layout.addWidget(peak_meters[0].widget, 0, 50, 3, 1)
            f_effect.layout.addWidget(peak_meters[1].widget, 0, 51, 3, 1)
            #f_effect.layout.addWidget(
            self.effects.append(f_effect)
            self.fx_layout.addWidget(f_effect.group_box)
            f_port += 15

        self.open_plugin_file()
        self.set_midi_learn(NABU_PORT_MAP)
        self.enable_ui_msg(True)

    def widget_close(self):
        self.enable_ui_msg(False)
        AbstractPluginUI.widget_close(self)

    def widget_show(self):
        self.enable_ui_msg(True)

    def enable_ui_msg(self, a_enabled):
        if a_enabled:
            self.plugin_val_callback(
                NABU_UI_MSG_ENABLED_PORT,
                1.0,
            )
        else:
            self.plugin_val_callback(
                NABU_UI_MSG_ENABLED_PORT,
                0.0,
            )

    def ui_message(self, a_name, a_value):
        if a_name == "gain":
            for msg in a_value.split('|'):
                values = msg.split(':')
                index = int(values[0])
                in_peak, out_peak = self.peak_meters[index]
                in_peak.set_value(values[1:3])
                out_peak.set_value(values[3:5])
        else:
            AbstractPluginUI.ui_message(a_name, a_value)

    def save_plugin_file(self):
        # Don't allow the peak meter to run at startup
        self.ui_msg_enabled.set_value(0)
        AbstractPluginUI.save_plugin_file(self)

