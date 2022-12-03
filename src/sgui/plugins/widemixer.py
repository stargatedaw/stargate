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

from sgui.util import Separator
from sgui.widgets import *
from sglib.lib.translate import _

WIDEMIXER_VOL_SLIDER = 0
WIDEMIXER_GAIN = 1
WIDEMIXER_PAN = 2
WIDEMIXER_LAW = 3
WIDEMIXER_INVERT_MODE = 4  # neither left right both
WIDEMIXER_STEREO_MODE = 5  # left right stereo swap
WIDEMIXER_BASS_MONO_ON = 6
WIDEMIXER_BASS_MONO = 7  # freq
WIDEMIXER_BASS_MONO_SOLO = 8
# Mid/Side, invert the phases and play only the stereo parts,
# or only the mono parts
WIDEMIXER_STEREO_EMPHASIS = 9
WIDEMIXER_DC_OFFSET = 10
WIDEMIXER_MUTE = 11
WIDEMIXER_BASS_MONO_LOW = 12
WIDEMIXER_BASS_MONO_HIGH = 13

WIDEMIXER_PORT_MAP = {
    "Volume": WIDEMIXER_VOL_SLIDER,
    "Pan": WIDEMIXER_PAN,
}
MUTE_TOOLTIP = "Mute all output of this mixer channel"
DC_OFFSET_TOOLTIP = """\
DC offset filter.
Removes extremely low frequencies, improves headroom to prevent clipping
and perceived loudness.
"""

class WideMixerPluginUI(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(self, *args, **kwargs)
        self._plugin_name = "WIDEMIXER"
        self.is_instrument = False
        f_knob_size = 42

        self.gain_knob = knob_control(
            f_knob_size,
            _("Gain"),
            WIDEMIXER_GAIN,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -3600,
            3600,
            0,
            KC_DECIMAL,
            self.port_dict,
            None,
            knob_kwargs={
                'arc_type': ArcType.BIDIRECTIONAL,
            },
            tooltip=(
                'Gain, in decibels.  Use this for fine control of volume, '
                'use the slider for automation'
            ),
        )

        self.pan_law_knob = knob_control(
            f_knob_size,
            _("Law"),
            WIDEMIXER_LAW,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -600,
            0,
            -300,
            KC_DECIMAL,
            self.port_dict,
            None,
            tooltip=(
                'Pan law.  This is the volume when panned at center '
                'Sound loses power when only coming from one speaker, '
                'pan law compensates by reducing center volume'
            ),
        )

        self.stereo_mode = combobox_control(
            105,
            _("Stereo Mode"),
            WIDEMIXER_STEREO_MODE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            ["Stereo", "Left", "Right", "Swap"],
            self.port_dict,
            a_default_index=0,
            tooltip=(
                'Stereo mode. stereo: both channels with no change, '
                'left: left channel only, right: right channel only, '
                'swap: swap left and right channels'
            ),
        )
        self.invert_mode = combobox_control(
            105,
            _("Invert Mode"),
            WIDEMIXER_INVERT_MODE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            ["Neither", "Left", "Right", "Both"],
            self.port_dict,
            a_default_index=0,
            tooltip=(
                'Phase invert one or more channels.  Note that if a stereo '
                'sound that is effectively mono is played with an inverted '
                'channel, the channels will effectively cancel each other out'
            ),
        )
        self.bass_mono_on = checkbox_control(
            "",
            WIDEMIXER_BASS_MONO_ON,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            tooltip='Enable or disable converting stereo bass to mono',
        )
        self.bass_mono_on.control.setObjectName("button_power_small")
        self.bass_mono_solo = checkbox_control(
            "",
            WIDEMIXER_BASS_MONO_SOLO,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            tooltip=(
                'Solo the bass frequencies.  Useful for tuning the frequency '
                'and volume while mixing your project'
            )
        )
        self.bass_mono_solo.control.setObjectName("solo_checkbox")
        self.bass_mono_knob = knob_control(
            f_knob_size,
            _("Freq") if self.is_mixer else _("Bass Mono"),
            WIDEMIXER_BASS_MONO,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            50,
            500,
            250,
            KC_INTEGER,
            self.port_dict,
            None,
            tooltip=(
                'The cutoff frequency to separate bass and higher frequencies'
            ),
        )
        self.bass_mono_low = knob_control(
            f_knob_size,
            _("Low"),
            WIDEMIXER_BASS_MONO_LOW,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -240,
            240,
            0,
            KC_TENTH,
            self.port_dict,
            None,
            tooltip='The volume gain of the low frequencies in decibels',
        )
        self.bass_mono_high = knob_control(
            f_knob_size,
            _("High"),
            WIDEMIXER_BASS_MONO_HIGH,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -240,
            240,
            0,
            KC_TENTH,
            self.port_dict,
            None,
            tooltip='The volume gain of the high frequencies in decibels',
        )
        self.mid_side_knob = knob_control(
            f_knob_size,
            _("M/S"),
            WIDEMIXER_STEREO_EMPHASIS,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_DECIMAL,
            self.port_dict,
            None,
            tooltip=(
                'Mid/side crossfade.  0.0 is normal sound, -1.0 is pure '
                'mono parts of the sound, 1.0 is pure stereo parts '
                'of the sound'
            ),
        )
        self.dc_offset = checkbox_control(
            "",
            WIDEMIXER_DC_OFFSET,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            tooltip=DC_OFFSET_TOOLTIP,
        )
        self.dc_offset.control.setObjectName("dc_checkbox")
        self.mute = checkbox_control(
            "",
            WIDEMIXER_MUTE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            tooltip=MUTE_TOOLTIP,
        )
        self.mute.control.setObjectName("mute_checkbox")

        if self.is_mixer:
            self.pan_slider = slider_control(
                QtCore.Qt.Orientation.Horizontal,
                _("Pan"),
                WIDEMIXER_PAN,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                -100,
                100,
                0,
                KC_DECIMAL,
                self.port_dict,
                None,
                tooltip='Pan the audio left or right',
            )
            self.pan_slider.control.setObjectName("pan_slider")
            self.volume_slider = slider_control(
                QtCore.Qt.Orientation.Vertical,
                "Vol",
                WIDEMIXER_VOL_SLIDER,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                -5000,
                0,
                0,
                KC_DECIMAL,
                self.port_dict,
                tooltip='The volume of the audio',
            )
            self.tab_widget = ComboTabWidget()
            self.layout.addWidget(self.tab_widget)
            self.in_tab = QWidget()
            self.tab_widget.addTab(self.in_tab, _("In"))
            self.in_vlayout = QVBoxLayout(self.in_tab)
            self.in_layout = QGridLayout()
            self.in_vlayout.addLayout(self.in_layout)
            in_out_sep = Separator('h')
            self.in_vlayout.addWidget(in_out_sep)

            self.out_tab = QWidget()
            self.tab_widget.addTab(self.out_tab, _("Out"))
            self.out_vlayout = QVBoxLayout(self.out_tab)
            self.out_vlayout.addWidget(self.pan_slider.control)
            self.out_layout = QGridLayout()
            self.out_vlayout.addLayout(self.out_layout)
            self.volume_gridlayout = QGridLayout()
            self.out_vlayout.addLayout(self.volume_gridlayout)

            self.gain_knob.add_to_grid_layout(self.out_layout, 0)
            self.pan_law_knob.add_to_grid_layout(self.out_layout, 1)
            self.dc_offset.add_to_grid_layout(self.out_layout, 0, a_row=1)
            self.mute.add_to_grid_layout(self.out_layout, 1, a_row=1)

            self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)
            self.volume_slider.control.setSizePolicy(
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )

            self.stereo_mode.add_to_grid_layout(
                self.in_layout,
                0,
                a_row=0
            )
            self.invert_mode.add_to_grid_layout(
                self.in_layout,
                0,
                a_row=1,
            )
            self.mid_side_knob.add_to_grid_layout(
                self.in_layout,
                0,
                a_row=2,
            )
            bass_mono_label = QLabel(_("Bass Mono"))
            bass_mono_label.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter,
            )
            self.in_vlayout.addWidget(bass_mono_label)
            bass_mono_hlayout = QHBoxLayout()
            self.in_vlayout.addLayout(bass_mono_hlayout)
            bass_mono_gridlayout = QGridLayout()
            bass_mono_hlayout.addLayout(bass_mono_gridlayout)
            bass_mono_vlayout = QVBoxLayout()
            bass_mono_hlayout.addLayout(bass_mono_vlayout)
            self.bass_mono_knob.add_to_grid_layout(bass_mono_gridlayout, 0)
            bass_mono_vlayout.addWidget(self.bass_mono_on.control)
            bass_mono_vlayout.addWidget(self.bass_mono_solo.control)
            bm_hi_lo_layout = QGridLayout()
            self.in_vlayout.addLayout(bm_hi_lo_layout)
            self.bass_mono_low.add_to_grid_layout(bm_hi_lo_layout, 0)
            self.bass_mono_high.add_to_grid_layout(bm_hi_lo_layout, 1)

            self.in_vlayout.addItem(
                QSpacerItem(1, 1, vPolicy=QSizePolicy.Policy.Expanding),
            )

        else:
            self.pan_knob = knob_control(
                f_knob_size,
                _("Pan"),
                WIDEMIXER_PAN,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                -100,
                100,
                0,
                KC_DECIMAL,
                self.port_dict,
                None,
                knob_kwargs={
                    'arc_type': ArcType.BIDIRECTIONAL,
                },
                tooltip='Pan the audio left or right',
            )
            self.volume_knob = knob_control(
                f_knob_size,
                _("Vol"),
                WIDEMIXER_VOL_SLIDER,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                -5000,
                0,
                0,
                KC_DECIMAL,
                self.port_dict,
                None,
                tooltip='The volume of the audio',
            )
            self.hlayout = QHBoxLayout()
            self.hlayout.addItem(
                QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
            )
            self.layout.addLayout(self.hlayout)

            self.out_layout = QGridLayout()
            self.hlayout.addLayout(self.out_layout)
            in_out_sep = Separator('v')
            self.hlayout.addWidget(in_out_sep)
            self.in_layout = QGridLayout()
            self.hlayout.addLayout(self.in_layout)
            bass_mono_sep = Separator('v')
            self.hlayout.addWidget(bass_mono_sep)
            self.bass_mono_layout = QGridLayout()
            self.hlayout.addLayout(self.bass_mono_layout)


            self.gain_knob.add_to_grid_layout(self.out_layout, 0)
            self.volume_knob.add_to_grid_layout(self.out_layout, 1)
            self.pan_knob.add_to_grid_layout(self.out_layout, 2)
            self.pan_law_knob.add_to_grid_layout(self.out_layout, 3)
            self.dc_offset.add_to_grid_layout(self.out_layout, 4)
            self.mute.add_to_grid_layout(self.out_layout, 5)

            self.stereo_mode.add_to_grid_layout(self.in_layout, 6)
            self.mid_side_knob.add_to_grid_layout(
                self.in_layout,
                7,
            )
            self.invert_mode.add_to_grid_layout(self.in_layout, 8)
            self.bass_mono_on.add_to_grid_layout(self.bass_mono_layout, 9)
            self.bass_mono_knob.add_to_grid_layout(self.bass_mono_layout, 10)
            self.bass_mono_solo.add_to_grid_layout(self.bass_mono_layout, 11)
            self.bass_mono_low.add_to_grid_layout(self.bass_mono_layout, 12)
            self.bass_mono_high.add_to_grid_layout(self.bass_mono_layout, 13)

            self.hlayout.addItem(
                QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
            )
        self.open_plugin_file()
        self.set_midi_learn(WIDEMIXER_PORT_MAP)

    def plugin_rel_callback(self, a_val1=None, a_val2=None):
        self.save_plugin_file()
