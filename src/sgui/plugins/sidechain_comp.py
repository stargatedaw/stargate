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


SCC_THRESHOLD = 0
SCC_RATIO = 1
SCC_ATTACK = 2
SCC_RELEASE = 3
SCC_WET = 4
SCC_UI_MSG_ENABLED = 5


SCC_PORT_MAP = {
    "Wet": SCC_WET
}

STYLESHEET = """\
QWidget#plugin_window{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #2a2a2a, stop: 0.5 #3a3a3f, stop: 1 #2a2a2a
    );
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
    background-color: #999999;
    background-image: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #999999, stop: 0.5 #777777, stop 1.0 #999999
    );
    border: 2px solid #222222;
    border-radius: 6px;
    color: #222222;
}

QLabel#plugin_value_label{
    background: none;
    color: #cccccc;
}
"""

class scc_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "Sidechain Comp."
        self.is_instrument = False

        knob_kwargs = {
            'arc_width_pct': 0.,
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-plastic-2-light.svg',
            ),
        }
        self.preset_manager = None
        self.main_hlayout = QHBoxLayout()
        left_screws = get_screws()
        self.main_hlayout.addLayout(left_screws)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.layout.addLayout(self.main_hlayout)

        f_knob_size = DEFAULT_LARGE_KNOB_SIZE

        self.reverb_groupbox_gridlayout = QGridLayout()
        self.main_hlayout.addLayout(self.reverb_groupbox_gridlayout)

        self.thresh_knob = knob_control(
            f_knob_size,
            _("Thresh"),
            SCC_THRESHOLD,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -36,
            -6,
            -24,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.thresh_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 3)

        self.ratio_knob = knob_control(
            f_knob_size,
            _("Ratio"),
            SCC_RATIO,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            1,
            100,
            20,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.ratio_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 7)

        self.attack_knob = knob_control(
            f_knob_size,
            _("Attack"),
            SCC_ATTACK,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            20,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.attack_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 15)

        self.release_knob = knob_control(
            f_knob_size,
            _("Release"),
            SCC_RELEASE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            20,
            300,
            50,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.release_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 18)

        self.wet_knob = knob_control(
            f_knob_size,
            _("Wet"),
            SCC_WET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            100,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.wet_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 21)

        self.peak_meter = peak_meter(16, False)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.main_hlayout.addWidget(self.peak_meter.widget)
        right_screws = get_screws()
        self.main_hlayout.addLayout(right_screws)

        self.ui_msg_enabled = null_control(
            SCC_UI_MSG_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(SCC_PORT_MAP)
        self.enable_ui_msg(True)

    def widget_close(self):
        self.enable_ui_msg(False)
        AbstractPluginUI.widget_close(self)

    def widget_show(self):
        self.enable_ui_msg(True)

    def enable_ui_msg(self, a_enabled):
        if a_enabled:
            self.plugin_val_callback(SCC_UI_MSG_ENABLED, 1.0)
        else:
            self.plugin_val_callback(SCC_UI_MSG_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "gain":
            self.peak_meter.set_value([a_value] * 2)
        else:
            AbstractPluginUI.ui_message(a_name, a_value)

    def save_plugin_file(self):
        # Don't allow the peak meter to run at startup
        self.ui_msg_enabled.set_value(0)
        AbstractPluginUI.save_plugin_file(self)


