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


SG_COMP_THRESHOLD = 0
SG_COMP_RATIO = 1
SG_COMP_KNEE = 2
SG_COMP_ATTACK = 3
SG_COMP_RELEASE = 4
SG_COMP_GAIN = 5
SG_COMP_MODE = 6
SG_COMP_RMS_TIME = 7
SG_COMP_UI_MSG_ENABLED = 8


SG_COMP_PORT_MAP = {}

STYLESHEET = """\
QWidget#plugin_window{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #a4a4a5, stop: 1 #6a6a6a
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
    color: #222222;
}
"""

class sg_comp_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs
        )
        knob_kwargs = {
            'arc_width_pct': 0.,
            'fg_svg': os.path.join(
                util.PLUGIN_ASSETS_DIR,
                'knob-plastic-2.svg',
            ),
        }
        self._plugin_name = "SG Compressor"
        self.is_instrument = False

        self.preset_manager = None

        self.main_hlayout = QHBoxLayout()
        left_screws = get_screws()
        self.main_hlayout.addLayout(left_screws)
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.layout.addLayout(self.main_hlayout)

        f_knob_size = DEFAULT_LARGE_KNOB_SIZE

        self.groupbox_gridlayout = QGridLayout()
        self.main_hlayout.addLayout(self.groupbox_gridlayout)

        self.thresh_knob = knob_control(
            f_knob_size,
            _("Thresh"),
            SG_COMP_THRESHOLD,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -360,
            -60,
            -240,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.thresh_knob.add_to_grid_layout(self.groupbox_gridlayout, 3)

        self.ratio_knob = knob_control(
            f_knob_size,
            _("Ratio"),
            SG_COMP_RATIO,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            10,
            100,
            20,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.ratio_knob.add_to_grid_layout(self.groupbox_gridlayout, 7)

        self.knee_knob = knob_control(
            f_knob_size,
            _("Knee"),
            SG_COMP_KNEE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            120,
            0,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.knee_knob.add_to_grid_layout(self.groupbox_gridlayout, 15)

        self.attack_knob = knob_control(
            f_knob_size,
            _("Attack"),
            SG_COMP_ATTACK,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            500,
            50,
            KC_MILLISECOND,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.attack_knob.add_to_grid_layout(self.groupbox_gridlayout, 21)

        self.release_knob = knob_control(
            f_knob_size,
            _("Release"),
            SG_COMP_RELEASE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            10,
            500,
            100,
            KC_MILLISECOND,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.release_knob.add_to_grid_layout(self.groupbox_gridlayout, 22)

        self.gain_knob = knob_control(
            f_knob_size,
            _("Gain"),
            SG_COMP_GAIN,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -360,
            360,
            0,
            KC_TENTH,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.gain_knob.add_to_grid_layout(self.groupbox_gridlayout, 30)

        self.mono_combobox = combobox_control(
            90,
            _("Mode"),
            SG_COMP_MODE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            [_("Peak"), _("RMS")],
            self.port_dict,
            0,
            self.preset_manager,
        )
        self.mono_combobox.add_to_grid_layout(self.groupbox_gridlayout, 36)

        self.rms_time_knob = knob_control(
            f_knob_size,
            _("RMS Time"),
            SG_COMP_RMS_TIME,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            1,
            5,
            2,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
        )
        self.rms_time_knob.add_to_grid_layout(self.groupbox_gridlayout, 37)

        peak_gradient = QLinearGradient(0., 0., 0., 100.)
        peak_gradient.setColorAt(0.0, QColor("#cc2222"))
        peak_gradient.setColorAt(0.3, QColor("#cc2222"))
        peak_gradient.setColorAt(0.6, QColor("#8877bb"))
        peak_gradient.setColorAt(1.0, QColor("#7777cc"))
        self.peak_meter = peak_meter(
            16,
            False,
            invert=True,
            brush=peak_gradient,
        )
        self.main_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.main_hlayout.addWidget(self.peak_meter.widget)
        right_screws = get_screws()
        self.main_hlayout.addLayout(right_screws)

        self.ui_msg_enabled = null_control(
            SG_COMP_UI_MSG_ENABLED,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0, self.port_dict,
        )

        self.open_plugin_file()
        self.set_midi_learn(SG_COMP_PORT_MAP)
        self.enable_ui_msg(True)

    def widget_close(self):
        self.enable_ui_msg(False)
        AbstractPluginUI.widget_close(self)

    def widget_show(self):
        self.enable_ui_msg(True)

    def enable_ui_msg(self, a_enabled):
        if a_enabled:
            self.plugin_val_callback(
                SG_COMP_UI_MSG_ENABLED,
                1.0,
            )
        else:
            self.plugin_val_callback(
                SG_COMP_UI_MSG_ENABLED,
                0.0,
            )

    def ui_message(self, a_name, a_value):
        if a_name == "gain":
            self.peak_meter.set_value([a_value] * 2)
        else:
            AbstractPluginUI.ui_message(a_name, a_value)

    def save_plugin_file(self):
        # Don't allow the peak meter to run at startup
        self.ui_msg_enabled.set_value(0)
        AbstractPluginUI.save_plugin_file(self)

