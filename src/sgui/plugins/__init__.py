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

import sys

from sglib.constants import MIDI_CHANNELS
from sglib.math import clip_value
from sgui import shared, widgets
from sgui.daw import shared as daw_shared
from sgui.widgets.nested_combobox import NestedComboBox
from sglib.models.stargate import *
from sglib.models.track_plugin import track_plugin
from sglib.lib import strings as sg_strings
from sglib.lib.translate import _
from sglib.log import LOG
from sgui import shared as glbl_shared
from sgui.plugins import (
    channel,
    compressor,
    delay,
    eq,
    fm1,
    limiter,
    multifx,
    nabu,
    pitchglitch,
    reverb,
    sampler1,
    sidechain_comp,
    simple_fader,
    trigger_fx,
    va1,
    vocoder,
    widemixer,
    xfade,
)
from sgui.sgqt import *
from sglib.constants import (
    PLUGINS_PER_TRACK,
    SENDS_PER_TRACK,
    TOTAL_PLUGINS_PER_TRACK,
)


PLUGIN_INSTRUMENT_COUNT = 3  # For inserting the split line into the menu

PLUGIN_NAMES = [
    "Sampler1",
    "VA1",
    "FM1",
    "SG Channel",
    "SG Compressor",
    "SG Delay",
    "SG EQ",
    "SG Limiter",
    "SG Vocoder",
    "MultiFX",
    "Sidechain Comp.",
    "Simple Fader",
    "SG Reverb",
    "TriggerFX",
    "X-Fade",
    'Wide Mixer',
    'Nabu',
    'Pitch Glitch',
]

PLUGIN_UIDS = {
    "None": (0, 'No plugin, remove any existing plugin from this slot'),
    "Sampler1": (
        1,
        (
            'A full-featured sampler suitable for sampled instruments or '
            'drums.  Can load SFZ format instruments'
        ),
    ),
    "VA1":  (
        2,
        'A classic virtual analog synthesizer using subtractive synthesis',
    ),
    "FM1": (
        3,
        'An FM, wavetable and additive synthesizer with modular effects and '
        'other advanced features',
    ),
    "MultiFX": (
        4,
        'A modular effects processor with over 30 different types of effects',
    ),
    "SG Delay": (
        5,
        'A stereo delay effect, capable of normal or "ping-pong" delay',
    ),
    "SG EQ": (
        6,
        'A 6 band EQ with pre-effects, post-effects and a spectrum analyzer',
    ),
    "Simple Fader": (
        7,
        'A simple volume fader',
    ),
    "SG Reverb": (
        8,
        'A classic digital reverb effect',
    ),
    "TriggerFX": (
        9,
        (
            'MIDI triggered gate and glitch effect.  Set a trigger note for '
            'each effect, then set your synthesizer plugin to not respond to '
            'that note, then use those notes to trigger the effect'
        ),
    ),
    "Sidechain Comp.": (
        10,
        (
            'A sidechain compressor.  Use the routing matrix or audio item '
            'editor to send a kick drum to the sidechain channel, then play '
            'a pad or bass sound through the main channel for the classic '
            'offbeat pumping sound'
        ),
    ),
    "SG Channel": (
        11,
        'Classic mixer channel plugin with volume fader, gain and pan',
    ),
    "X-Fade": (
        12,
        (
            'Cross-fader plugin.  Crossfade between the main channel and '
            'sidechain channel of a track using a slider'
        ),
    ),
    "SG Compressor": (
        13,
        'Classic compressor plugin',
    ),
    "SG Vocoder": (
        14,
        'Analog style vocoder plugin.  Send vocals to the sidechain channel '
        'using the routing matrix or audio item editor, and synthesizer '
        'sounds to the main channel for classic vocoder sounds'
    ),
    "SG Limiter": (
        15,
        (
            'A classic hard-limiter plugin to keep audio from exceeding '
            'a given volume level'
        ),
    ),
    'Wide Mixer': (
        16,
        (
            'An advanced stereo mixer plugin that includes mid/side '
            'processing, mono-bass, panning and more'
        ),
    ),
    'Nabu': (
        17,
        (
            'Advanced modular effects processor with over 30 effects '
            'that includes multi-band processing and effect routing for '
            'parallel processing of effect chains'
        ),
    ),
    'Pitch Glitch': (
        18,
        (
            'MIDI note triggered, pitched glitch effect'
        ),
    ),
}

PLUGINS_SYNTH = ["VA1", "FM1"]
PLUGINS_SAMPLER = ["Sampler1",]
PLUGINS_EFFECTS = ["MultiFX", 'Nabu', "SG Delay", "SG EQ", "SG Reverb"]
PLUGINS_MIDI_TRIGGERED = ["TriggerFX", 'Pitch Glitch']
PLUGINS_DYNAMICS = ["SG Compressor", "SG Limiter"]
PLUGINS_SIDECHAIN = ["Sidechain Comp.", "X-Fade", "SG Vocoder",]
PLUGINS_MIXER = ["Simple Fader", "SG Channel", 'Wide Mixer']

MAIN_PLUGIN_NAMES = [
    "None",
    ("Synth", PLUGINS_SYNTH),
    ("Sampler", PLUGINS_SAMPLER),
    ("Effects", PLUGINS_EFFECTS),
    ("MIDI Triggered FX", PLUGINS_MIDI_TRIGGERED),
    ("Dynamics", PLUGINS_DYNAMICS),
    ("Sidechain", PLUGINS_SIDECHAIN),
    ("Mixer", PLUGINS_MIXER),
]

WAVE_EDITOR_PLUGIN_NAMES = [
    "None",
    ("Effects", PLUGINS_EFFECTS),
    ("Dynamics", PLUGINS_DYNAMICS),
    ("Mixer", PLUGINS_MIXER)
]

MIXER_PLUGIN_NAMES = [
    "None",
    ("Mixer", PLUGINS_MIXER),
]
PLUGIN_UIDS_REVERSE = {v[0]:k for k, v in PLUGIN_UIDS.items()}
CC_NAMES = {x:[] for x in PLUGIN_NAMES}
CONTROLLER_PORT_NAME_DICT = {x:{} for x in PLUGIN_NAMES}
CONTROLLER_PORT_NUM_DICT = {x:{} for x in PLUGIN_NAMES}

PLUGIN_UI_TYPES = {
    1: sampler1.sampler1_plugin_ui,
    2: va1.VA1PluginUI,
    3: fm1.fm1_plugin_ui,
    4: multifx.multifx_plugin_ui,
    5: delay.sgdelay_plugin_ui,
    6: eq.sgeq_plugin_ui,
    7: simple_fader.sfader_plugin_ui,
    8: reverb.ReverbPluginUI,
    9: trigger_fx.triggerfx_plugin_ui,
    10: sidechain_comp.scc_plugin_ui,
    11: channel.SgChnlPluginUI,
    12: xfade.xfade_plugin_ui,
    13: compressor.sg_comp_plugin_ui,
    14: vocoder.sg_vocoder_plugin_ui,
    15: limiter.LimiterPluginUI,
    16: widemixer.WideMixerPluginUI,
    17: nabu.NabuPluginUI,
    18: pitchglitch.PitchGlitchUI,
}

PORTMAP_DICT = {
    "Sampler1": sampler1.SAMPLER1_PORT_MAP,
    "FM1": fm1.FM1_PORT_MAP,
    "VA1": va1.VA1_PORT_MAP,
    "MultiFX": multifx.MULTIFX_PORT_MAP,
    "SG Channel": channel.SGCHNL_PORT_MAP,
    "SG Compressor": compressor.SG_COMP_PORT_MAP,
    "SG Delay": delay.SGDELAY_PORT_MAP,
    "SG EQ": eq.SGEQ_PORT_MAP,
    "Simple Fader": simple_fader.SFADER_PORT_MAP,
    "SG Reverb": reverb.SREVERB_PORT_MAP,
    "TriggerFX": trigger_fx.TRIGGERFX_PORT_MAP,
    "Sidechain Comp.": sidechain_comp.SCC_PORT_MAP,
    "X-Fade": xfade.XFADE_PORT_MAP,
    "SG Vocoder": vocoder.SG_VOCODER_PORT_MAP,
    "SG Limiter": limiter.SG_LIM_PORT_MAP,
    "Wide Mixer": widemixer.WIDEMIXER_PORT_MAP,
    'Nabu': nabu.NABU_PORT_MAP,
}

def get_plugin_uid_by_name(a_name):
    return PLUGIN_UIDS[str(a_name)][0]

class controller_map_item:
    def __init__(self, a_name, a_port):
        self.name = str(a_name)
        self.port = int(a_port)

def load_controller_maps():
    for k, v in PORTMAP_DICT.items():
        for k2, v2 in v.items():
            f_map = controller_map_item(k2, v2)
            CONTROLLER_PORT_NAME_DICT[k][k2] = f_map
            CONTROLLER_PORT_NUM_DICT[k][int(v2)] = f_map
            CC_NAMES[k].append(k2)
        CC_NAMES[k].sort()

load_controller_maps()

class SgPluginUiDict:
    def __init__(self, a_project, a_ipc):
        """ a_project:    AbstractProject
            a_ipc:        AbstractIPC
        """
        self.ui_dict = {}
        self.midi_learn_control = None
        self.ctrl_update_callback = a_ipc.update_plugin_control
        self.project = a_project
        self.plugin_pool_dir = a_project.plugin_pool_folder
        self.configure_callback = a_ipc.configure_plugin
        self.midi_learn_osc_callback = a_ipc.midi_learn
        self.load_cc_map_callback = a_ipc.load_cc_map

    def __contains__(self, a_plugin_uid):
        return a_plugin_uid in self.ui_dict

    def __getitem__(self, a_plugin_uid):
        return self.ui_dict[a_plugin_uid]

    def open_plugin_ui(
        self,
        a_plugin_uid,
        a_plugin_type,
        a_is_mixer=False,
    ):
        if not a_plugin_uid in self.ui_dict:
            f_plugin = PLUGIN_UI_TYPES[a_plugin_type](
                self.ctrl_update_callback,
                self.project,
                a_plugin_uid,
                self.configure_callback,
                self.plugin_pool_dir,
                self.midi_learn_callback,
                self.load_cc_map_callback,
                a_is_mixer,
            )
            self.ui_dict[a_plugin_uid] = f_plugin
            return f_plugin
        else:
            retval = self.ui_dict[a_plugin_uid]
            retval.widget_show()  # Always enable UI messages
            return retval


    def midi_learn_callback(self, a_plugin, a_control):
        self.midi_learn_control = (a_plugin, a_control)
        self.midi_learn_osc_callback()

    def close_plugin_ui(self, a_track_num):
        f_track_num = int(a_track_num)
        if f_track_num in self.ui_dict:
            self.ui_dict[f_track_num].widget.close()
            self.ui_dict.pop(f_track_num)

    def hide_plugin_ui(self, a_track_num):
        f_track_num = int(a_track_num)
        if f_track_num in self.ui_dict:
            f_widget = self.ui_dict[f_track_num].widget
            f_widget.hide()

    def close_all_plugin_windows(self):
        for v in list(self.ui_dict.values()):
            v.is_quitting = True
            v.widget.close()
        self.ui_dict = {}

    def save_all_plugin_state(self):
        for v in list(self.ui_dict.values()):
            v.save_plugin_file()

PLUGIN_SETTINGS_COPY_OBJ = None
PLUGIN_SETTINGS_IS_CUT = False


class AbstractPluginSettings:
    def __init__(
        self,
        a_set_plugin_func,
        a_index,
        a_track_num,
        a_save_callback,
        a_qcbox=False,
        a_is_mixer=False,
    ):
        self.is_mixer = a_is_mixer
        self.plugin_ui = None
        self.set_plugin_func = a_set_plugin_func
        self.vlayout = QVBoxLayout()
        self.suppress_osc = False
        self.save_callback = a_save_callback
        self.plugin_uid = -1
        self.track_num = a_track_num
        self.index = a_index
        self.plugin_index = None

        self.qcbox = a_qcbox
        if a_qcbox:
            self.plugin_combobox = QComboBox()
        else:
            self.plugin_combobox = NestedComboBox(PLUGIN_UIDS)
            self.plugin_combobox.currentIndexChanged_connect(
                self.on_plugin_combobox_change,
            )
        self.plugin_combobox.setMinimumWidth(150)
        self.plugin_combobox.wheelEvent = self.wheel_event

        self.plugin_combobox.addItems(self.plugin_list)

        if a_qcbox:
            self.plugin_combobox.currentIndexChanged.connect(
                self.on_plugin_combobox_change,
            )

        self.power_checkbox = QCheckBox()
        self.power_checkbox.setObjectName("button_power")
        self.power_checkbox.setChecked(True)
        self.power_checkbox.setToolTip('Enable or disable this plugin')

        if self.is_mixer:
            self.vlayout.addWidget(self.plugin_combobox)
            self.vlayout.setAlignment(
                self.plugin_combobox,
                QtCore.Qt.AlignmentFlag.AlignTop,
            )
            self.spacer = QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
            self.vlayout.addItem(self.spacer)
        else:
            self.controls_widget = QWidget()
            self.controls_widget.setFixedWidth(1200)
            self.controls_widget.setObjectName("plugin_rack")
            self.layout = QHBoxLayout(self.controls_widget)
            self.layout.setContentsMargins(3, 3, 3, 3)
            self.plugin_label = QLabel(f"Plugin {a_index + 1: <2}")
            self.layout.addWidget(self.plugin_label)
            self.vlayout.addWidget(self.controls_widget)
            self.layout.addWidget(self.plugin_combobox)
            self.power_checkbox.clicked.connect(self.on_power_changed)
            self.layout.addWidget(self.power_checkbox)

    def get_midi_channel(self):
        return 0

    def reset_routing(self, index):
        pass

    def clear(self):
        self.set_value(track_plugin(self.index, 0, -1))
        self.on_plugin_change()

    def copy(self):
        global PLUGIN_SETTINGS_COPY_OBJ
        PLUGIN_SETTINGS_COPY_OBJ = self.get_value()

    def cut(self):
        global PLUGIN_SETTINGS_IS_CUT
        PLUGIN_SETTINGS_IS_CUT = True
        self.copy()
        shared.PLUGIN_UI_DICT.hide_plugin_ui(self.plugin_uid)
        self.plugin_combobox.setCurrentIndex(0)

    def paste(self):
        if PLUGIN_SETTINGS_COPY_OBJ is None:
            return
        self.set_value(PLUGIN_SETTINGS_COPY_OBJ)
        global PLUGIN_SETTINGS_IS_CUT
        if PLUGIN_SETTINGS_IS_CUT:
            PLUGIN_SETTINGS_IS_CUT = False
        else:
            self.plugin_uid = constants.PROJECT.get_next_plugin_uid()
            constants.PROJECT.copy_plugin(
                PLUGIN_SETTINGS_COPY_OBJ.plugin_uid, self.plugin_uid)
        self.on_plugin_change()

    def set_value(self, a_val: track_plugin):
        self.suppress_osc = True

        if self.qcbox:
            f_name = PLUGIN_UIDS_REVERSE[a_val.plugin_index]
            index = self.plugin_combobox.findText(f_name)
            self.plugin_combobox.setCurrentIndex(index)
        else:
            self.plugin_combobox.setCurrentIndex(a_val.plugin_index)

        self.plugin_index = a_val.plugin_index

        self.plugin_uid = a_val.plugin_uid
        self.power_checkbox.setChecked(a_val.power == 1)
        self.on_show_ui()
        self.suppress_osc = False

    def get_value(self):
        return track_plugin(
            self.index,
            get_plugin_uid_by_name(
                self.plugin_combobox.currentText(),
            ),
            self.plugin_uid,
            a_power=1 if self.power_checkbox.isChecked() else 0,
        )

    def on_plugin_combobox_change(self, a_val=None):
        if self.suppress_osc:
            return
        glbl_shared.APP.setOverrideCursor(
            QtCore.Qt.CursorShape.WaitCursor,
        )
        self.on_plugin_change(a_val)
        glbl_shared.APP.restoreOverrideCursor()

    def on_plugin_change(self, a_val=None, a_save=True, ipc=True):
        if self.suppress_osc:
            return
        f_index = get_plugin_uid_by_name(self.plugin_combobox.currentText())
        if f_index == 0:
            if self.plugin_ui:
                self.vlayout.removeWidget(self.plugin_ui.widget)
                self.plugin_ui = None
            glbl_shared.PLUGIN_UI_DICT.close_plugin_ui(self.plugin_uid)
            self.plugin_uid = -1
        elif self.plugin_uid == -1 or self.plugin_index != f_index:
            if self.plugin_uid > -1:
                glbl_shared.PLUGIN_UI_DICT.close_plugin_ui(self.plugin_uid)
            self.plugin_uid = constants.PROJECT.get_next_plugin_uid()
            self.plugin_index = f_index
        if a_save:
            self.save_callback()
        if ipc:
            self.set_plugin_func(self.track_num)
        self.on_show_ui()

    def on_power_changed(self, a_val=None):
        f_index = get_plugin_uid_by_name(self.plugin_combobox.currentText())
        if f_index:
            self.save_callback()
            self.set_plugin_func(self.track_num)

    def wheel_event(self, a_event=None):
        pass

    def on_show_ui(self):
        plugin_name = str(self.plugin_combobox.currentText())
        if not plugin_name:
            return
        f_index = get_plugin_uid_by_name(self.plugin_combobox.currentText())
        if f_index == 0 or self.plugin_uid == -1:
            if self.is_mixer:
                self.vlayout.addItem(self.spacer)
            return
        if self.plugin_ui:
            LOG.info(
                f"{self.track_num} removing {self.plugin_ui.widget}"
            )
            self.vlayout.removeWidget(self.plugin_ui.widget)
        self.plugin_ui = glbl_shared.PLUGIN_UI_DICT.open_plugin_ui(
            self.plugin_uid,
            f_index,
            a_is_mixer=self.is_mixer,
        )
        if self.is_mixer:
            self.plugin_ui.widget.setFixedWidth(120)
            self.vlayout.removeItem(self.spacer)
        else:
            self.plugin_ui.widget.setFixedWidth(1200)
        self.vlayout.addWidget(self.plugin_ui.widget)

    def _save_and_update(self):
        if self.suppress_osc:
            return
        self.save_callback()
        self.set_plugin_func(self.track_num)

AUDIO_INPUT_TOOLTIP = """\
If enabled, this plugin can receive audio input.  Note that it will only
receive input if no other plugin routes to it.
"""

class PluginSettingsMain(AbstractPluginSettings):
    def __init__(
        self,
        a_set_plugin_func,
        a_index,
        a_track_num,
        a_save_callback,
    ):
        self.plugin_list = MAIN_PLUGIN_NAMES

        self.menu_button = QPushButton(_("Menu"))
        self.menu = QMenu()
        self.menu_button.setMenu(self.menu)
        f_copy_action = self.menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy)
        f_paste_action = self.menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste)
        self.menu.addSeparator()
        f_cut_action = self.menu.addAction(_("Cut"))
        f_cut_action.triggered.connect(self.cut)
        self.menu.addSeparator()
        f_clear_action = self.menu.addAction(_("Clear"))
        f_clear_action.triggered.connect(self.clear)

        AbstractPluginSettings.__init__(
            self,
            a_set_plugin_func,
            a_index,
            a_track_num,
            a_save_callback,
            a_qcbox=False,
        )

        self.midi_channel_combobox = QComboBox()
        self.midi_channel_combobox.setMinimumWidth(48)
        self.midi_channel_combobox.addItems(MIDI_CHANNELS)
        self.midi_channel_combobox.currentIndexChanged.connect(
            self._save_and_update,
        )
        self.midi_channel_combobox.setToolTip(
            'Select the MIDI channel that this plugin will listen for '
            'note, CC and pitchbend events on.'
        )
        self.layout.insertWidget(
            self.layout.count() - 1,
            QLabel('MIDI Channel'),
        )
        self.layout.insertWidget(
            self.layout.count() - 1,
            self.midi_channel_combobox,
        )

        self.route_combobox = QComboBox()
        self.route_combobox.addItems(
            [str(x) for x in range(a_index + 2, 11)] + ["Output"]
        )
        self.route_combobox.currentIndexChanged.connect(self._save_and_update)
        self.route_combobox.setMinimumWidth(90)
        self.route_combobox.setToolTip(
            'Choose which plugin slot to route to.  Use this for '
            'layering instruments, parallel processing and other '
            'creative uses'
        )
        self.layout.insertWidget(
            self.layout.count() - 1,
            QLabel(_("Route")),
        )
        self.layout.insertWidget(
            self.layout.count() - 1,
            self.route_combobox,
        )

        self.audio_input_checkbox = QCheckBox(_("Audio Input"))
        self.audio_input_checkbox.setChecked(True)
        self.audio_input_checkbox.stateChanged.connect(self._save_and_update)
        self.audio_input_checkbox.setToolTip(AUDIO_INPUT_TOOLTIP)
        self.layout.insertWidget(
            self.layout.count() - 1,
            self.audio_input_checkbox,
        )

        self.layout.insertSpacerItem(
            self.layout.count() - 1,
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        self.hide_checkbox = QCheckBox()
        self.hide_checkbox.setObjectName("button_hide")
        self.hide_checkbox.setToolTip(_("Hide the plugin"))
        self.layout.addWidget(self.hide_checkbox)
        self.hide_checkbox.setEnabled(False)
        self.hide_checkbox.stateChanged.connect(self.hide_checkbox_changed)

    def get_midi_channel(self):
        return self.midi_channel_combobox.currentIndex()

    def reset_routing(self, index):
        self.plugin_label.setText(f"Plugin {index + 1: <2}")
        self.audio_input_checkbox.setChecked(True)
        suppress_osc = self.suppress_osc
        self.suppress_osc = True
        self.route_combobox.clear()
        self.route_combobox.addItems(
            [str(x) for x in range(index + 2, 11)] + ["Output"]
        )
        self.route_combobox.setCurrentIndex(0)
        self.suppress_osc = suppress_osc

    def set_value(self, value: track_plugin):
        AbstractPluginSettings.set_value(self, value)
        self.suppress_osc = True
        self.route_combobox.setCurrentIndex(value.route)
        self.midi_channel_combobox.setCurrentIndex(value.midi_channel)
        self.audio_input_checkbox.setChecked(bool(value.audio_input))
        self.suppress_osc = False

    def on_show_ui(self):
        AbstractPluginSettings.on_show_ui(self)
        if self.plugin_ui:
            self.hide_checkbox.setEnabled(True)
        else:
            self.hide_checkbox.setChecked(False)
            self.hide_checkbox.setEnabled(False)

    def hide_checkbox_changed(self, a_val=None):
        if self.plugin_ui:
            self.plugin_ui.widget.setHidden(self.hide_checkbox.isChecked())

    def on_plugin_combobox_change(self, a_val=None):
        AbstractPluginSettings.on_plugin_combobox_change(self, a_val)
        if a_val:
            constants.DAW_PROJECT.check_output(self.track_num)

    def get_value(self):
        return track_plugin(
            self.index,
            get_plugin_uid_by_name(
                self.plugin_combobox.currentText(),
            ),
            self.plugin_uid,
            a_power=1 if self.power_checkbox.isChecked() else 0,
            route=self.route_combobox.currentIndex(),
            audio_input=1 if self.audio_input_checkbox.isChecked() else 0,
            midi_channel=self.midi_channel_combobox.currentIndex(),
        )


class PluginSettingsMixer(AbstractPluginSettings):
    def __init__(
        self,
        a_set_plugin_func,
        a_index,
        a_track_num,
        a_save_callback,
    ):
        self.plugin_list = ["None"] + PLUGINS_MIXER  # MIXER_PLUGIN_NAMES
        AbstractPluginSettings.__init__(
            self,
            a_set_plugin_func,
            a_index,
            a_track_num,
            a_save_callback,
            a_qcbox=True,
            a_is_mixer=True,
        )
        self.plugin_combobox.setToolTip(
            'Select a mixer plugin.  The mixer channels are simply a type '
            'of plugin, there are several to choose from'
        )
        self.index += PLUGINS_PER_TRACK
        self.vlayout.setParent(None)
        self.plugin_combobox.setMinimumWidth(120)


class PluginSettingsWaveEditor(AbstractPluginSettings):
    def __init__(
        self,
        a_set_plugin_func,
        a_index,
        a_track_num,
        a_save_callback,
    ):
        self.plugin_list = WAVE_EDITOR_PLUGIN_NAMES
        AbstractPluginSettings.__init__(
            self,
            a_set_plugin_func,
            a_index,
            a_track_num,
            a_save_callback,
            a_qcbox=False,
        )
        self.layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )


class PluginRackTab:
    def __init__(self):
        self.widget = QWidget(shared.MAIN_WINDOW)
        self.vlayout = QVBoxLayout(self.widget)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout = QHBoxLayout()
        self.menu_layout.setContentsMargins(3, 0, 3, 0)
        self.vlayout.addLayout(self.menu_layout)
        self.menu_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.track_combobox = QComboBox()
        self.track_combobox.setMinimumWidth(300)
        self.track_combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.menu_layout.addWidget(QLabel(_("Track")))
        self.menu_layout.addWidget(self.track_combobox)

        self.channel_combobox = QComboBox()
        self.channel_combobox.setMinimumWidth(48)
        self.channel_combobox.addItems(MIDI_CHANNELS)
        self.channel_combobox.setToolTip(
            'The MIDI channel when using your QWERTY keyboard for MIDI input. '
            "The top row of letters, q through ], will play notes on this "
            "rack on this MIDI channel"
        )
        self.menu_layout.addItem(QSpacerItem(60, 1))
        self.menu_layout.addWidget(QLabel(_("QWERTY:")))
        self.menu_layout.addWidget(QLabel(_("MIDI Channel")))
        self.menu_layout.addWidget(self.channel_combobox)

        self.octave_spinbox = QSpinBox()
        self.octave_spinbox.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.octave_spinbox.setRange(-2, 7)
        self.octave_spinbox.setValue(2)
        self.octave_spinbox.setToolTip(_(
            "Sets the octave when using your QWERTY keyboard for MIDI input. "
            "The top row of letters, q through ], will play notes on this "
            "rack at this octave"
        ))
        self.menu_layout.addWidget(QLabel(_("Octave")))
        self.menu_layout.addWidget(self.octave_spinbox)

        self.plugins_button = QPushButton(_("Menu"))
        self.plugins_menu = QMenu(self.widget)
        self.plugins_button.setMenu(self.plugins_menu)

        self.plugins_order_action = QAction(
            _("Reorder Plugins..."),
            self.plugins_menu,
        )
        self.plugins_menu.addAction(self.plugins_order_action)
        self.plugins_order_action.setToolTip(
            'Open a dialog to reorder the plugins in the selected track.  '
            'This will reset plugin routing, you will need to change plugin '
            'Route again if you want non-sequential routing'
        )
        self.plugins_order_action.triggered.connect(self.set_plugin_order)

        self.menu_layout.addItem(QSpacerItem(60, 1))
        self.menu_layout.addWidget(self.plugins_button)

        self.menu_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        self.stacked_widget = QStackedWidget()
        self.vlayout.addWidget(self.stacked_widget)
        self.enabled = True
        self.plugin_racks = {}
        self.last_rack_num = None

    def midi_channel(self):
        return self.channel_combobox.currentIndex()

    def octave(self):
        return self.octave_spinbox.value() + 2

    def rack_index(self):
        return self.track_combobox.currentIndex()

    def set_index(self, index: int):
        self.track_combobox.setCurrentIndex(index)

    def set_plugin_order(self):
        index = self.track_combobox.currentIndex()
        rack = self.plugin_racks[index]
        rack.set_plugin_order()

    def initialize(self, a_project):
        self.PROJECT = a_project
        self.track_combobox.currentIndexChanged.connect(self.track_changed)
        self.track_combobox.setCurrentIndex(0)

    def tab_selected(self, a_is_selected):
        """ Call this when the parent tab widget switches to/from this tab """
        if a_is_selected:
            self.track_changed()
        else:
            self.close_rack(self.track_combobox.currentIndex())

    def show_rack(self, a_rack_num):
        rack = self.plugin_racks[a_rack_num]
        for plugin in rack.plugins:
            if plugin.plugin_ui:
                plugin.plugin_ui.widget_show()

    def close_rack(self, a_rack_num):
        if a_rack_num not in self.plugin_racks:
            LOG.info("{} not in self.plugins_racks".format(a_rack_num))
            return
        rack = self.plugin_racks[a_rack_num]
        for plugin in rack.plugins:
            if plugin.plugin_ui:
                plugin.plugin_ui.widget_close()

    def track_changed(self, a_val=None):
        if not self.enabled:
            return
        glbl_shared.APP.setOverrideCursor(
            QtCore.Qt.CursorShape.WaitCursor,
        )
        f_index = self.track_combobox.currentIndex()
        if (
            self.last_rack_num is not None
            and
            self.last_rack_num != f_index
        ):
            self.close_rack(self.last_rack_num)
        self.last_rack_num = f_index
        self.stacked_widget.setHidden(True)
        self.widget.update()
        self.widget.setUpdatesEnabled(False)
        if f_index not in self.plugin_racks:
            f_rack = PluginRack(self.PROJECT, f_index)
            self.plugin_racks[f_index] = f_rack
            self.stacked_widget.addWidget(self.plugin_racks[f_index].widget)
        self.show_rack(f_index)
        self.stacked_widget.setCurrentWidget(
            self.plugin_racks[f_index].widget,
        )
        self.stacked_widget.setHidden(False)
        self.widget.setUpdatesEnabled(True)
        self.widget.update()
        glbl_shared.APP.restoreOverrideCursor()

    def set_track_names(self, a_list):
        self.enabled = False
        index = self.track_combobox.currentIndex()
        self.track_combobox.clear()
        self.track_combobox.addItems(a_list)
        self.track_combobox.setCurrentIndex(index)
        self.enabled = True

    def set_track_order(self, a_dict, track_names):
        f_index = self.track_combobox.currentIndex()
        f_new_index = a_dict[f_index]
        self.set_track_names(track_names)
        self.enabled = False
        self.plugin_racks = {
            y: self.plugin_racks[x]
            for x, y in a_dict.items()
            if x in self.plugin_racks
        }
        for k, v in self.plugin_racks.items():
            LOG.info(f"track {v.track_number}: {k}")
            v.track_number = k
            for plugin in v.plugins:
                LOG.info(f"plugin {plugin.track_num}: {k}")
                plugin.track_num = k
        self.track_combobox.setCurrentIndex(f_new_index)
        self.enabled = True


class PluginRack:
    def __init__(
        self,
        a_project,
        a_track_number,
        a_type=PluginSettingsMain,
    ):
        self.track_number = int(a_track_number)
        self.PROJECT = a_project
        self.plugins = [
            a_type(
                self.PROJECT.ipc().set_plugin,
                x,
                a_track_number,
                self.save_callback,
            )
            for x in range(PLUGINS_PER_TRACK)
        ]
        self.widget = QWidget()
        self.vlayout = QVBoxLayout(self.widget)
        self.vlayout.setContentsMargins(0, 0, 0, 0)

        self.scrollarea = QScrollArea()
        self.scrollarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self.scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
        )
        self.vlayout.addWidget(self.scrollarea)
        self.scrollarea.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("plugin_ui")
        self.scroll_hlayout = QHBoxLayout(self.scroll_widget)
        self.scroll_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.rack_widget = QWidget()
        self.rack_widget.setObjectName('rack_background')
        self.scroll_vlayout = QVBoxLayout(self.rack_widget)
        self.scroll_hlayout.addWidget(self.rack_widget)
        self.scroll_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.scrollarea.setWidget(self.scroll_widget)
        for plugin in self.plugins[:PLUGINS_PER_TRACK]:
            self.scroll_vlayout.addLayout(plugin.vlayout)
        self.open_plugins()
        self.scroll_vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )

    def get_plugin_uids(self, channel=None):
        return [
            (x.plugin_uid, x.get_midi_channel())
            for x in self.plugins
            if (
                channel is None
                or
                x.get_midi_channel() == channel
            ) and x.plugin_uid != -1
        ]

    def set_plugin_order(self):
        f_labels = [
            "{} : {}".format(f_i, x.plugin_combobox.currentText())
            for f_i, x in zip(range(1, 11), self.plugins)
        ]
        f_result = widgets.ordered_table_dialog(
            f_labels,
            self.plugins,
            30,
            200,
            shared.MAIN_WINDOW,
        )
        if f_result:
            for f_i, f_plugin in zip(range(len(f_result)), f_result):
                f_plugin.index = f_i
                f_plugin.reset_routing(f_i)
                f_plugin.on_plugin_change(a_save=False, ipc=False)
            LOG.info(f"{self.plugins} {f_result}")
            self.plugins[0:len(f_result)] = f_result
            LOG.info(f"{self.plugins} {f_result}")
            self.save_callback()
            f_plugin.set_plugin_func(self.track_number)
            self.widget.setUpdatesEnabled(False)
            for plugin in self.plugins:
                self.scroll_vlayout.removeItem(plugin.vlayout)
            for plugin in self.plugins:
                self.scroll_vlayout.addLayout(plugin.vlayout)
            self.widget.setUpdatesEnabled(True)
            self.widget.update()

    def open_plugins(self):
        self.widget.setUpdatesEnabled(False)
        f_plugins = self.PROJECT.get_track_plugins(self.track_number)
        if f_plugins:
            for f_plugin in f_plugins.plugins[:PLUGINS_PER_TRACK]:
                if f_plugin.index not in range(len(self.plugins)):
                    LOG.warning(
                        f"{self.track_number}:{f_plugin.index}:{self.plugins}"
                    )
                else:
                    self.plugins[f_plugin.index].set_value(f_plugin)
        self.widget.setUpdatesEnabled(True)
        self.widget.update()

    def save_callback(self):
        f_result = self.PROJECT.get_track_plugins(self.track_number)
        f_result.plugins[:PLUGINS_PER_TRACK] = [
            x.get_value() for x in self.plugins
        ]
        self.PROJECT.save_track_plugins(self.track_number, f_result)
        self.PROJECT.commit(
            "Update track plugins for track {}".format(self.track_number),
        )


class MixerChannel:
    def __init__(self, a_name, a_track_num):
        self.PROJECT = None
        self.track_number = a_track_num
        self.widget = QWidget()
        self.vlayout = QVBoxLayout(self.widget)
        self.sends = {}
        self.outputs = {}
        self.output_labels = {}
        self.name_label = QPushButton(a_name)
        self.menu = QMenu()

        action = QAction("Open in plugin rack", self.menu)
        action.setToolTip('Open this track in the plugin rack')
        self.menu.addAction(action)
        action.triggered.connect(self.open_rack)

        self.name_label.setMenu(self.menu)
        self.vlayout.addWidget(
            self.name_label,
            -1,
            QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self.grid_layout = QGridLayout()
        self.vlayout.addLayout(self.grid_layout, 1)
        self.peak_meter = widgets.peak_meter(20, True)
        self.grid_layout.addWidget(self.peak_meter.widget, 0, 0, 2, 1)

    def open_rack(self):
        daw_shared.open_rack(self.track_number)

    def save_callback(self):
        f_result = self.PROJECT.get_track_plugins(self.track_number)

        for index, plugin in (
            (k + PLUGINS_PER_TRACK, v.get_value())
            for k, v in self.sends.items()
        ):
            f_result.plugins[index] = plugin
        self.PROJECT.save_track_plugins(self.track_number, f_result)
        self.PROJECT.commit(
            "Update mixer plugins for track {}".format(self.track_number))

    def set_name(self, a_name, a_dict, routing_graph):
        """ Set the track name label and the send labels

            @a_name: The name of this track
            @a_dict: A dictionary of {track_number: track_name, ...} for
                     all tracks
            @routing_graph: The routing graph for the project
        """
        if not self.output_labels:
            return # not loaded yet

        self.name_label.setText(a_name)
        for k in self.outputs:
            if self.outputs[k] == -1:
                self.output_labels[k].setText("")
            else:
                track_index = self.outputs[k]
                name = a_dict[track_index]
                send = routing_graph.graph[self.track_number][k]
                if send.conn_type == 1:
                    name += ": SC"
                self.output_labels[k].setText(name)

    def get_plugin_uids(self, channel=None):
        return [
            (x.plugin_uid, x.get_midi_channel())
            for x in self.sends.values()
        ]

    def add_plugin(self, a_index):
        plugin = PluginSettingsMixer(
            self.PROJECT.ipc().set_plugin,
            a_index,
            self.track_number,
            self.save_callback,
        )
        self.sends[a_index] = plugin
        self.outputs[a_index] = -1
        f_label = QLabel("")
        self.output_labels[a_index] = f_label
        self.grid_layout.addWidget(f_label, 0, a_index + 1)
        self.grid_layout.addLayout(plugin.vlayout, 1, a_index + 1)

    def change_send_visibility(self, a_index, a_hidden):
        """ Show or hide a track send

            @a_index:  int, the send index
            @a_hidden: bool, True to hide, False to show
        """
        plugin_ui = self.sends[a_index].plugin_ui
        self.sends[a_index].plugin_combobox.setHidden(a_hidden)
        if plugin_ui:
            plugin_ui.widget.setHidden(a_hidden)
        self.output_labels[a_index].setHidden(a_hidden)

    def set_plugin(self, a_graph_dict, a_plugin_dict):
        """ Update the routes and plugins

            @a_graph_dict:  A RoutingGraph.graph[
                                track_number] node:
                            {send_index: TrackSend, ...}
            @a_plugin_dict: A dictionary of {track_index:
                            {plugin_index: track_plugin}}
        """
        self.outputs = {
            k: v.output
            for k, v in a_graph_dict.items()
            if v.conn_type != 2
        }
        for i in range(len(self.sends)):
            hidden = not (i in self.outputs and self.outputs[i] != -1)
            plugin_index = i + PLUGINS_PER_TRACK
            if plugin_index in a_plugin_dict:
                self.sends[i].set_value(a_plugin_dict[plugin_index])
            else:
                LOG.warning(
                    f"{plugin_index} not in {a_plugin_dict}"
                )
            self.change_send_visibility(i, hidden)

    def set_project(self, a_project):
        """ Load the project

            @a_project: A instance of a class inheriting AbstractProject
        """
        assert not self.PROJECT, "self.PROJECT is already set"
        self.PROJECT = a_project
        for i in range(SENDS_PER_TRACK):
            self.add_plugin(i)

class MixerWidget:
    def __init__(self, a_track_count):
        self.widget = QScrollArea()
        self.widget.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_widget.setObjectName("plugin_ui")
        self.widget.setWidget(self.main_widget)
        self.tracks = {}
        self.grid_layout = QGridLayout(self.main_widget)
        self.track_count = a_track_count
        for f_i in range(a_track_count):
            f_channel = MixerChannel(
                "Main" if f_i == 0 else "track{}".format(f_i), f_i)
            self.tracks[f_i] = f_channel
            self.grid_layout.addWidget(f_channel.widget, 0, f_i)

    def set_project(self, a_project):
        self.PROJECT = a_project
        for f_i in range(1, self.track_count):
            self.tracks[f_i].set_project(a_project)

    def update_sends(self, a_graph, a_plugins):
        """ Update the mixer, show channels for active routings
            and hide inactive routings

            @a_graph:   A RoutingGraph
            @a_plugins: A dict of {track_index:
                        {plugin_index: track_plugin, ...}, ...}
        """
        self.widget.setUpdatesEnabled(False)
        for i in range(1, len(self.tracks)):
            graph_dict = a_graph.graph[i] if i in a_graph.graph else {}
            if i in a_plugins:
                self.tracks[i].set_plugin(graph_dict, a_plugins[i])
        self.widget.setUpdatesEnabled(True)
        self.widget.update()

    def update_track_names(self, a_track_names_dict, routing_graph):
        for k, v in a_track_names_dict.items():
            self.tracks[k].set_name(
                v,
                a_track_names_dict,
                routing_graph,
            )

    def clear(self):
        for v in self.tracks.values():
            v.clear()

