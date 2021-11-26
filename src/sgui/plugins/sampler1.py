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

from sglib import constants
from sglib.math import clip_value, pitch_to_hz
from sglib.models.plugin_file import plugin_file
from sglib.lib import (
    sfz,
    util,
)
from sgui.widgets import *
from sglib.lib.translate import _
from sgui import shared as glbl_shared

import time
import os
import shutil

SAMPLER1_MAX_SAMPLE_COUNT = 100

#Total number of LFOs, ADSRs, other envelopes, etc...
#Used for the PolyFX mod matrix
SAMPLER1_MODULATOR_COUNT = 4
#How many modular PolyFX
SAMPLER1_MODULAR_POLYFX_COUNT = 4
#How many ports per PolyFX, 3 knobs and a combobox
SAMPLER1_PORTS_PER_MOD_EFFECT = 4
#How many knobs per PolyFX, 3 knobs
SAMPLER1_CONTROLS_PER_MOD_EFFECT = 3
SAMPLER1_EFFECTS_GROUPS_COUNT = 1
#The number of mono_fx groups
SAMPLER1_MONO_FX_GROUPS_COUNT = SAMPLER1_MAX_SAMPLE_COUNT
SAMPLER1_MONO_FX_COUNT = 4

SAMPLER1_ATTACK = 3
SAMPLER1_DECAY = 4
SAMPLER1_SUSTAIN = 5
SAMPLER1_RELEASE = 6
SAMPLER1_FILTER_ATTACK = 7
SAMPLER1_FILTER_DECAY = 8
SAMPLER1_FILTER_SUSTAIN = 9
SAMPLER1_FILTER_RELEASE = 10
SAMPLER1_LFO_PITCH = 11
SAMPLER1_MAIN_VOLUME = 12
SAMPLER1_MAIN_GLIDE = 13
SAMPLER1_MAIN_PITCHBEND_AMT = 14
SAMPLER1_PITCH_ENV_TIME = 15
SAMPLER1_LFO_FREQ = 16
SAMPLER1_LFO_TYPE = 17
#From MultiFX
SAMPLER1_FX0_KNOB0 = 18
SAMPLER1_FX0_KNOB1 = 19
SAMPLER1_FX0_KNOB2 = 20
SAMPLER1_FX0_COMBOBOX = 21
SAMPLER1_FX1_KNOB0 = 22
SAMPLER1_FX1_KNOB1 = 23
SAMPLER1_FX1_KNOB2 = 24
SAMPLER1_FX1_COMBOBOX = 25
SAMPLER1_FX2_KNOB0 = 26
SAMPLER1_FX2_KNOB1 = 27
SAMPLER1_FX2_KNOB2 = 28
SAMPLER1_FX2_COMBOBOX = 29
SAMPLER1_FX3_KNOB0 = 30
SAMPLER1_FX3_KNOB1 = 31
SAMPLER1_FX3_KNOB2 = 32
SAMPLER1_FX3_COMBOBOX = 33
#PolyFX Mod Matrix
SAMPLER1_PFXMATRIX_FIRST_PORT = 34
SAMPLER1_PFXMATRIX_GRP0DST0SRC0CTRL0 = 34
SAMPLER1_PFXMATRIX_GRP0DST0SRC0CTRL1 = 35
SAMPLER1_PFXMATRIX_GRP0DST0SRC0CTRL2 = 36
SAMPLER1_PFXMATRIX_GRP0DST0SRC1CTRL0 = 37
SAMPLER1_PFXMATRIX_GRP0DST0SRC1CTRL1 = 38
SAMPLER1_PFXMATRIX_GRP0DST0SRC1CTRL2 = 39
SAMPLER1_PFXMATRIX_GRP0DST0SRC2CTRL0 = 40
SAMPLER1_PFXMATRIX_GRP0DST0SRC2CTRL1 = 41
SAMPLER1_PFXMATRIX_GRP0DST0SRC2CTRL2 = 42
SAMPLER1_PFXMATRIX_GRP0DST0SRC3CTRL0 = 43
SAMPLER1_PFXMATRIX_GRP0DST0SRC3CTRL1 = 44
SAMPLER1_PFXMATRIX_GRP0DST0SRC3CTRL2 = 45
SAMPLER1_PFXMATRIX_GRP0DST1SRC0CTRL0 = 46
SAMPLER1_PFXMATRIX_GRP0DST1SRC0CTRL1 = 47
SAMPLER1_PFXMATRIX_GRP0DST1SRC0CTRL2 = 48
SAMPLER1_PFXMATRIX_GRP0DST1SRC1CTRL0 = 49
SAMPLER1_PFXMATRIX_GRP0DST1SRC1CTRL1 = 50
SAMPLER1_PFXMATRIX_GRP0DST1SRC1CTRL2 = 51
SAMPLER1_PFXMATRIX_GRP0DST1SRC2CTRL0 = 52
SAMPLER1_PFXMATRIX_GRP0DST1SRC2CTRL1 = 53
SAMPLER1_PFXMATRIX_GRP0DST1SRC2CTRL2 = 54
SAMPLER1_PFXMATRIX_GRP0DST1SRC3CTRL0 = 55
SAMPLER1_PFXMATRIX_GRP0DST1SRC3CTRL1 = 56
SAMPLER1_PFXMATRIX_GRP0DST1SRC3CTRL2 = 57
SAMPLER1_PFXMATRIX_GRP0DST2SRC0CTRL0 = 58
SAMPLER1_PFXMATRIX_GRP0DST2SRC0CTRL1 = 59
SAMPLER1_PFXMATRIX_GRP0DST2SRC0CTRL2 = 60
SAMPLER1_PFXMATRIX_GRP0DST2SRC1CTRL0 = 61
SAMPLER1_PFXMATRIX_GRP0DST2SRC1CTRL1 = 62
SAMPLER1_PFXMATRIX_GRP0DST2SRC1CTRL2 = 63
SAMPLER1_PFXMATRIX_GRP0DST2SRC2CTRL0 = 64
SAMPLER1_PFXMATRIX_GRP0DST2SRC2CTRL1 = 65
SAMPLER1_PFXMATRIX_GRP0DST2SRC2CTRL2 = 66
SAMPLER1_PFXMATRIX_GRP0DST2SRC3CTRL0 = 67
SAMPLER1_PFXMATRIX_GRP0DST2SRC3CTRL1 = 68
SAMPLER1_PFXMATRIX_GRP0DST2SRC3CTRL2 = 69
SAMPLER1_PFXMATRIX_GRP0DST3SRC0CTRL0 = 70
SAMPLER1_PFXMATRIX_GRP0DST3SRC0CTRL1 = 71
SAMPLER1_PFXMATRIX_GRP0DST3SRC0CTRL2 = 72
SAMPLER1_PFXMATRIX_GRP0DST3SRC1CTRL0 = 73
SAMPLER1_PFXMATRIX_GRP0DST3SRC1CTRL1 = 74
SAMPLER1_PFXMATRIX_GRP0DST3SRC1CTRL2 = 75
SAMPLER1_PFXMATRIX_GRP0DST3SRC2CTRL0 = 76
SAMPLER1_PFXMATRIX_GRP0DST3SRC2CTRL1 = 77
SAMPLER1_PFXMATRIX_GRP0DST3SRC2CTRL2 = 78
SAMPLER1_PFXMATRIX_GRP0DST3SRC3CTRL0 = 79
SAMPLER1_PFXMATRIX_GRP0DST3SRC3CTRL1 = 80
SAMPLER1_PFXMATRIX_GRP0DST3SRC3CTRL2 = 81

SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL0 = 82
SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL1 = 83
SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL2 = 84
SAMPLER1_PFXMATRIX_GRP0DST1SRC4CTRL0 = 85
SAMPLER1_PFXMATRIX_GRP0DST1SRC4CTRL1 = 86
SAMPLER1_PFXMATRIX_GRP0DST1SRC4CTRL2 = 87
SAMPLER1_PFXMATRIX_GRP0DST2SRC4CTRL0 = 88
SAMPLER1_PFXMATRIX_GRP0DST2SRC4CTRL1 = 89
SAMPLER1_PFXMATRIX_GRP0DST2SRC4CTRL2 = 90
SAMPLER1_PFXMATRIX_GRP0DST3SRC4CTRL0 = 91
SAMPLER1_PFXMATRIX_GRP0DST3SRC4CTRL1 = 92
SAMPLER1_PFXMATRIX_GRP0DST3SRC4CTRL2 = 93

SAMPLER1_PFXMATRIX_GRP0DST0SRC5CTRL0 = 94
SAMPLER1_PFXMATRIX_GRP0DST0SRC5CTRL1 = 95
SAMPLER1_PFXMATRIX_GRP0DST0SRC5CTRL2 = 96
SAMPLER1_PFXMATRIX_GRP0DST1SRC5CTRL0 = 97
SAMPLER1_PFXMATRIX_GRP0DST1SRC5CTRL1 = 98
SAMPLER1_PFXMATRIX_GRP0DST1SRC5CTRL2 = 99
SAMPLER1_PFXMATRIX_GRP0DST2SRC5CTRL0 = 100
SAMPLER1_PFXMATRIX_GRP0DST2SRC5CTRL1 = 101
SAMPLER1_PFXMATRIX_GRP0DST2SRC5CTRL2 = 102
SAMPLER1_PFXMATRIX_GRP0DST3SRC5CTRL0 = 103
SAMPLER1_PFXMATRIX_GRP0DST3SRC5CTRL1 = 104
SAMPLER1_PFXMATRIX_GRP0DST3SRC5CTRL2 = 105

#End PolyFX Mod Matrix

# This is the last control port, + 1, for zero-based iteration
SAMPLER1_LAST_REGULAR_CONTROL_PORT = 106
# The first port to use when enumerating the ports for mod_matrix controls.
# All of the mod_matrix ports should be sequential,
# * any additional ports should prepend self port number
SAMPLER1_FIRST_SAMPLE_TABLE_PORT = 106
#The range of ports for sample pitch
SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MIN = SAMPLER1_FIRST_SAMPLE_TABLE_PORT
SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
#The range of ports for the low note to play a sample on
SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MIN = SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MAX
SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MAX = \
    (SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
#The range of ports for the high note to play a sample on
SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MIN = SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MAX
SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MAX = \
    (SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
#The range of ports for sample volume
SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MIN = SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MAX
SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_START_PORT_RANGE_MIN = SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MAX
SAMPLER1_SAMPLE_START_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_START_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_END_PORT_RANGE_MIN = SAMPLER1_SAMPLE_START_PORT_RANGE_MAX
SAMPLER1_SAMPLE_END_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_END_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MIN = SAMPLER1_SAMPLE_END_PORT_RANGE_MAX
SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MIN = SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MAX
SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MIN = SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MAX
SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_PITCH_PORT_RANGE_MIN = SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MAX
SAMPLER1_PITCH_PORT_RANGE_MAX = (SAMPLER1_PITCH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_TUNE_PORT_RANGE_MIN = SAMPLER1_PITCH_PORT_RANGE_MAX
SAMPLER1_TUNE_PORT_RANGE_MAX = (SAMPLER1_TUNE_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN = SAMPLER1_TUNE_PORT_RANGE_MAX
SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MAX = \
(SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MIN = SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MAX
SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MIN = SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MAX
SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MIN = SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MAX
SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MAX = \
    (SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
#MonoFX0
SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MIN = SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MAX
SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MIN = SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MAX
SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MIN = SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MAX
SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MIN = SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MAX
SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
#MonoFX1
SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MIN = SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MAX
SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MIN = SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MAX
SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MIN = SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MAX
SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MIN = SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MAX
SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
#MonoFX2
SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MIN = SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MAX
SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MIN = SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MAX
SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MIN = SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MAX
SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MIN = SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MAX
SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
#MonoFX3
SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MIN = SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MAX
SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MIN = SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MAX
SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MIN = SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MAX
SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MIN = SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MAX
SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MAX = \
    (SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
#Sample FX Group
SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN = SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MAX
SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MAX = \
(SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
#Noise amp
SAMPLER1_NOISE_AMP_MIN = SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MAX
SAMPLER1_NOISE_AMP_MAX = (SAMPLER1_NOISE_AMP_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
#Noise type
SAMPLER1_NOISE_TYPE_MIN = SAMPLER1_NOISE_AMP_MAX
SAMPLER1_NOISE_TYPE_MAX = (SAMPLER1_NOISE_TYPE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#sample fade-in
SAMPLER1_SAMPLE_FADE_IN_MIN = SAMPLER1_NOISE_TYPE_MAX
SAMPLER1_SAMPLE_FADE_IN_MAX = (SAMPLER1_SAMPLE_FADE_IN_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#sample fade-out
SAMPLER1_SAMPLE_FADE_OUT_MIN = SAMPLER1_SAMPLE_FADE_IN_MAX
SAMPLER1_SAMPLE_FADE_OUT_MAX = (SAMPLER1_SAMPLE_FADE_OUT_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

SAMPLER1_FIRST_EQ_PORT = SAMPLER1_SAMPLE_FADE_OUT_MAX

# Stacked as:
# 100 *
#     [freq, bw, gain] * 6

SAMPLER1_LAST_EQ_PORT = (SAMPLER1_FIRST_EQ_PORT + (18 * 100))

SAMPLER1_LFO_PITCH_FINE = SAMPLER1_LAST_EQ_PORT
SAMPLER1_MIN_NOTE = SAMPLER1_LFO_PITCH_FINE + 1
SAMPLER1_MAX_NOTE = SAMPLER1_MIN_NOTE + 1
SAMPLER1_MAIN_PITCH = SAMPLER1_MAX_NOTE + 1
SAMPLER1_ADSR_LIN_MAIN = SAMPLER1_MAIN_PITCH + 1


SAMPLER1_PORT_MAP = {
    "Main Attack": "3",
    "Main Decay": "4",
    "Main Sustain": "5",
    "Main Release": "6",
    "ADSR2 Attack": "7",
    "ADSR2 Decay": "8",
    "ADSR2 Sustain": "9",
    "ADSR2 Release": "10",
    "LFO Pitch": "11",
    "LFO Pitch Fine": SAMPLER1_LFO_PITCH_FINE,
    "Main Glide": "13",
    "Pitch Env Time": "15",
    "LFO Freq": "16",
    "FX0 Knob0": "18",
    "FX0 Knob1": "19",
    "FX0 Knob2": "20",
    "FX1 Knob0": "22",
    "FX1 Knob1": "23",
    "FX1 Knob2": "24",
    "FX2 Knob0": "26",
    "FX2 Knob1": "27",
    "FX2 Knob2": "28",
    "FX3 Knob0": "30",
    "FX3 Knob1": "31",
    "FX3 Knob2": "32",
}

_sampler1_port_mins = (
    SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MIN,
    SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MIN,
    SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MIN,
    SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MIN)

for f_fx in range(4):
    f_port_iter = _sampler1_port_mins[f_fx]
    for f_knob in range(3):
        for f_group in range(1, SAMPLER1_MAX_SAMPLE_COUNT + 1):
            f_group_str = str(f_group).zfill(3)
            f_label = "Mono FX{} Knob{} Group {}".format(
                f_fx, f_knob, f_group_str)
            SAMPLER1_PORT_MAP[f_label] = f_port_iter
            f_port_iter += 1


SMP_TB_RADIOBUTTON_INDEX = 0
SMP_TB_FILE_PATH_INDEX = 1
SMP_TB_NOTE_INDEX = 2
SMP_TB_LOW_NOTE_INDEX = 3
SMP_TB_HIGH_NOTE_INDEX = 4
SMP_TB_VOLUME_INDEX = 5
SMP_TB_VEL_SENS_INDEX = 6
SMP_TB_VEL_LOW_INDEX = 7
SMP_TB_VEL_HIGH_INDEX = 8
SMP_TB_PITCH_INDEX = 9
SMP_TB_TUNE_INDEX = 10
SMP_TB_INTERPOLATION_MODE_INDEX = 11

SAMPLER1_INSTRUMENT_CLIPBOARD = None

STYLESHEET = """\
QWidget {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: .5,
        stop: 0 #605f5f, stop: 1 #545255
    );
    border: none;
}

QGroupBox#plugin_groupbox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: .5,
        stop: 0 #605f5f, stop: 1 #545255
    );
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

QComboBox,
QLineEdit
{
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

QAbstractItemView
{
    background-color: #6a6a6a;
    border: 2px solid #828282;
    color: #cccccc;
    selection-background-color: #cccccc;
    selection-color: #333333;
}

QTableWidget
{
    alternate-background-color: #605f5f;
    background-color: #545255;
    color: #cccccc;
}

QLabel {
    background: none;
}

QLineEdit {
    background: 2px solid #6a6a6a;
    border: 2px solid #333333;
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

QCheckBox,
QRadioButton
{
    background-color: none;
    margin: 3px;
    padding: 0px;
}

QCheckBox::indicator,
QRadioButton::indicator
{
    background-color: #aaaaaa;
    border-radius: 6px;
    border: 1px solid #222222;
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
        stop: 0.25 #222222,
        stop: 0.3 #aaaaaa
    );
}

QRadioButton::indicator:hover,
QCheckBox::indicator:hover
{
    border: 1px solid #ffffff;
}

QHeaderView::section {
    background-color: #aaaaaa;
	color: #222222;
    border: 1px solid #222222;
    padding: 4px;
}

QScrollBar:horizontal
{
    background: #aaaaaa;
    border: 1px solid #222222;
    height: 15px;
    margin: 0px 16px 0 16px;
}

QScrollBar::add-line:horizontal,
QScrollBar::handle:horizontal,
QScrollBar::sub-line:horizontal
{
    background: #aaaaaa;
}

QScrollBar::add-line:vertical,
QScrollBar::handle:vertical,
QScrollBar::sub-line:vertical
{
    background: #aaaaaa;
}

QScrollBar::add-line:horizontal,
QScrollBar::add-line:vertical,
QScrollBar::handle:horizontal,
QScrollBar::handle:vertical,
QScrollBar::sub-line:horizontal,
QScrollBar::sub-line:vertical
{
    min-height: 20px;
}

QScrollBar::add-line:horizontal
{
    border: 1px solid #222222;
    subcontrol-origin: margin;
    subcontrol-position: right;
    width: 14px;
}

QScrollBar::sub-line:horizontal
{
    border: 1px solid #222222;
    subcontrol-origin: margin;
    subcontrol-position: left;
    width: 14px;
}

QScrollBar[hide="true"]::down-arrow:vertical,
QScrollBar[hide="true"]::left-arrow:horizontal,
QScrollBar[hide="true"]::right-arrow:horizontal,
QScrollBar[hide="true"]::up-arrow:vertical
{
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal
{
    background: #222222;
    border: 1px solid #222222;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical
{
    background: #222222;
    border: 1px solid #222222;
}

QScrollBar:vertical
{
    background: #666666;
    border: 1px solid #222222;
    margin: 16px 0 16px 0;
    width: 15px;
}

QScrollBar::handle:vertical
{
    min-height: 20px;
}

QScrollBar::add-line:vertical
{
    border: 1px solid #222222;
    height: 14px;
    subcontrol-origin: margin;
    subcontrol-position: bottom;
}

QScrollBar::sub-line:vertical
{
    border: 1px solid #222222;
    height: 14px;
    subcontrol-origin: margin;
    subcontrol-position: top;
}
"""

class sampler1_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )

        self.widget.setUpdatesEnabled(False)
        self.is_instrument = True
        knob_kwargs = {
            'arc_brush': QColor('#111111'),
            'arc_bg_brush': QColor("#4a4a4a"),
            'arc_width_pct': 12.0,
            'draw_line': True,
            'fg_svg': None,
        }

        self.selected_row_index = 0
        self.handle_control_updates = True
        self.suppress_selected_sample_changed = False

        self.interpolation_modes_list = [
            _("Pitched"), _("Percussion"), _("No Pitch")]

        f_sample_table_columns = [
            "", #Selected row
            _("Path"), #File path
            _("Sample Pitch"), #Sample base pitch
            _("Low Note"), #Low Note
            _("High Note"), #High Note
            _("Volume"), #Volume
            _("Vel. Sens."), #Velocity Sensitivity
            _("Low Vel."), #Low Velocity
            _("High Vel."), #High Velocity
            _("Pitch"), #Pitch
            _("Tune"), #Tune
            _("Mode"), #Interpolation Mode
            _("Noise Type"),
            _("Noise Amp"),
        ]

        self.noise_types_list = [_("Off"), _("White"), _("Pink")]

        self.sample_table = QTableWidget(
            SAMPLER1_MAX_SAMPLE_COUNT,
            len(f_sample_table_columns),
        )
        self.sample_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers,
        )
        self.sample_table.setFocusPolicy(
            QtCore.Qt.FocusPolicy.NoFocus,
        )
        self.sample_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )

        self.sample_table.setAlternatingRowColors(True)
        self.sample_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel,
        )
        self.sample_table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel,
        )
        self.sample_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )
        self.sample_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )

        glbl_shared.APP.processEvents()

        self.selected_radiobuttons = []
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_radiobutton = QRadioButton(self.sample_table)
            self.selected_radiobuttons.append(f_radiobutton)
            self.sample_table.setCellWidget(f_i, 0, f_radiobutton)
            f_radiobutton.clicked.connect(self.selectionChanged)

        self.sample_base_pitches = []
        f_port_start = SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_pitch = note_selector_widget(
                f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, 60)
            self.sample_table.setCellWidget(f_i, 2, f_sample_pitch.widget)
            self.sample_base_pitches.append(f_sample_pitch)

        self.sample_low_notes = []
        f_port_start = SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_low_pitch = note_selector_widget(
                f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, 0)
            self.sample_table.setCellWidget(f_i, 3, f_low_pitch.widget)
            self.sample_low_notes.append(f_low_pitch)

        self.sample_high_notes = []
        f_port_start = SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_high_pitch = note_selector_widget(
                f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, 120)
            self.sample_table.setCellWidget(f_i, 4, f_high_pitch.widget)
            self.sample_high_notes.append(f_high_pitch)

        glbl_shared.APP.processEvents()

        self.sample_vols = []
        f_port_start = SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_vol = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                -50.0, 36.0, 0.0, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 5, f_sample_vol.control)
            self.sample_vols.append(f_sample_vol)

        self.sample_vel_sens = []
        f_port_start = SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_vel_sens = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                0, 20, 10, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 6, f_vel_sens.control)
            self.sample_vel_sens.append(f_vel_sens)

        self.sample_low_vels = []
        f_port_start = SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_vel_low = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                1, 127, 1, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 7, f_vel_low.control)
            self.sample_low_vels.append(f_vel_low)

        self.sample_high_vels = []
        f_port_start = SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_vel_high = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                1, 128, 128, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 8, f_vel_high.control)
            self.sample_high_vels.append(f_vel_high)

        self.sample_pitches = []
        f_port_start = SAMPLER1_PITCH_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_pitch = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                -36, 36, 0, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 9, f_sample_pitch.control)
            self.sample_pitches.append(f_sample_pitch)

        self.sample_tunes = []
        f_port_start = SAMPLER1_TUNE_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_tune = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                -100, 100, 0, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 10, f_sample_tune.control)
            self.sample_tunes.append(f_sample_tune)

        self.sample_modes = []
        f_port_start = \
            SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_mode = combobox_control(
                120, None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.interpolation_modes_list, self.port_dict, 1)
            self.sample_table.setCellWidget(f_i, 11, f_sample_mode.control)
            self.sample_modes.append(f_sample_mode)

        self.noise_types = []
        f_port_start = SAMPLER1_NOISE_TYPE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_noise_type = combobox_control(
                75, None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.noise_types_list, self.port_dict, 0)
            self.sample_table.setCellWidget(f_i, 12, f_noise_type.control)
            self.noise_types.append(f_noise_type)

        self.noise_amps = []
        f_port_start = SAMPLER1_NOISE_AMP_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_noise_amp = spinbox_control(
                None, f_port_start + f_i,
                self.plugin_rel_callback, self.plugin_val_callback,
                -60, 0, -30, KC_NONE, self.port_dict)
            self.sample_table.setCellWidget(f_i, 13, f_noise_amp.control)
            self.noise_amps.append(f_noise_amp)

        self.sample_starts = []
        f_port_start = SAMPLER1_SAMPLE_START_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_start = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.sample_starts.append(f_sample_start)

        self.sample_ends = []
        f_port_start = SAMPLER1_SAMPLE_END_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_sample_end = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 1000, self.port_dict)
            self.sample_ends.append(f_sample_end)

        glbl_shared.APP.processEvents()

        self.loop_starts = []
        f_port_start = SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_loop_start = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.loop_starts.append(f_loop_start)

        self.loop_modes = []
        f_port_start = SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_loop_mode = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.loop_modes.append(f_loop_mode)

        self.loop_ends = []
        f_port_start = SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_loop_end = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 1000, self.port_dict)
            self.loop_ends.append(f_loop_end)

        self.fade_in_ends = []
        f_port_start = SAMPLER1_SAMPLE_FADE_IN_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_fade_in = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.fade_in_ends.append(f_fade_in)

        self.fade_out_starts = []
        f_port_start = SAMPLER1_SAMPLE_FADE_OUT_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_fade_out = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 1000, self.port_dict)
            self.fade_out_starts.append(f_fade_out)

        glbl_shared.APP.processEvents()

        #MonoFX0
        self.monofx0knob0_ctrls = []
        f_port_start = SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx0knob0_ctrls.append(f_ctrl)

        self.monofx0knob1_ctrls = []
        f_port_start = SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx0knob1_ctrls.append(f_ctrl)

        self.monofx0knob2_ctrls = []
        f_port_start = SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx0knob2_ctrls.append(f_ctrl)

        self.monofx0comboboxes = []
        f_port_start = SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.monofx0comboboxes.append(f_ctrl)
        #MonoFX1
        self.monofx1knob0_ctrls = []
        f_port_start = SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx1knob0_ctrls.append(f_ctrl)

        glbl_shared.APP.processEvents()

        self.monofx1knob1_ctrls = []
        f_port_start = SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx1knob1_ctrls.append(f_ctrl)

        self.monofx1knob2_ctrls = []
        f_port_start = SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx1knob2_ctrls.append(f_ctrl)

        self.monofx1comboboxes = []
        f_port_start = SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.monofx1comboboxes.append(f_ctrl)

        #MonoFX2
        self.monofx2knob0_ctrls = []
        f_port_start = SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx2knob0_ctrls.append(f_ctrl)

        self.monofx2knob1_ctrls = []
        f_port_start = SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx2knob1_ctrls.append(f_ctrl)

        self.monofx2knob2_ctrls = []
        f_port_start = SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx2knob2_ctrls.append(f_ctrl)

        self.monofx2comboboxes = []
        f_port_start = SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.monofx2comboboxes.append(f_ctrl)

        glbl_shared.APP.processEvents()

        #MonoFX3
        self.monofx3knob0_ctrls = []
        f_port_start = SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx3knob0_ctrls.append(f_ctrl)

        self.monofx3knob1_ctrls = []
        f_port_start = SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx3knob1_ctrls.append(f_ctrl)

        self.monofx3knob2_ctrls = []
        f_port_start = SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 64, self.port_dict)
            self.monofx3knob2_ctrls.append(f_ctrl)

        self.monofx3comboboxes = []
        f_port_start = SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_ctrl = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.monofx3comboboxes.append(f_ctrl)

        self.monofx_groups = []
        f_port_start = SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_monofx_group = null_control(
                f_port_start + f_i, self.plugin_rel_callback,
                self.plugin_val_callback, 0, self.port_dict)
            self.monofx_groups.append(f_monofx_group)

        self.monofx_null_controls_tuple = (
            self.monofx0knob0_ctrls, self.monofx0knob1_ctrls,
            self.monofx0knob2_ctrls, self.monofx1knob0_ctrls,
            self.monofx1knob1_ctrls, self.monofx1knob2_ctrls,
            self.monofx2knob0_ctrls, self.monofx2knob1_ctrls,
            self.monofx2knob2_ctrls, self.monofx3knob0_ctrls,
            self.monofx3knob1_ctrls, self.monofx3knob2_ctrls)

        glbl_shared.APP.processEvents()

        self.eq_ports = []
        f_port_start = SAMPLER1_FIRST_EQ_PORT
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_group_list = []
            self.eq_ports.append(f_group_list)
            for f_i2 in range(6):
                f_eq_list = []
                f_group_list.append(f_eq_list)
                f_eq_port = f_port_start + (f_i * 18) + (f_i2 * 3)
                f_freq = null_control(
                    f_eq_port, self.plugin_rel_callback,
                    self.plugin_val_callback, (f_i2 * 18) + 24, self.port_dict)
                f_eq_port += 1
                f_bw = null_control(
                    f_eq_port, self.plugin_rel_callback,
                    self.plugin_val_callback, 300, self.port_dict)
                f_eq_port += 1
                f_gain = null_control(
                    f_eq_port, self.plugin_rel_callback,
                    self.plugin_val_callback, 0, self.port_dict)
                f_eq_list.append(f_freq)
                f_eq_list.append(f_bw)
                f_eq_list.append(f_gain)

        self.sample_table.setHorizontalHeaderLabels(f_sample_table_columns)
        self.sample_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )
        self.sample_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )
        self.sample_table.resizeRowsToContents()

        self.file_selector = file_select_widget(self.load_files)
        self.file_selector.clear_button.pressed.connect(self.clearFile)
        self.file_selector.reload_button.pressed.connect(self.reloadSample)

        self.main_tab = QTabWidget()

        self.sample_tab = QWidget()
        self.sample_tab.setObjectName("plugin_widget")
        self.sample_tab_layout = QVBoxLayout(self.sample_tab)

        self.file_browser = FileBrowserWidget()
        self.file_browser.open_bookmarks()
        self.sample_tab_layout.addWidget(self.file_browser.hsplitter)

        self.file_browser.load_button.pressed.connect(
            self.file_browser_load_button_pressed)
        self.file_browser.list_file.itemDoubleClicked.connect(
            self.file_browser_load_button_pressed)
        self.file_browser.preview_button.pressed.connect(
            self.file_browser_preview_button_pressed)
        self.file_browser.stop_preview_button.pressed.connect(
            self.file_browser_stop_preview)

        self.smp_tab_main_widget = QWidget()
        self.smp_tab_main_widget.setMinimumWidth(420)
        self.smp_tab_main_verticalLayout = QVBoxLayout(
            self.smp_tab_main_widget)
        self.file_browser.hsplitter.addWidget(self.smp_tab_main_widget)
        self.file_browser.hsplitter.setSizes([240, 9999])

        self.smp_tab_main_verticalLayout.addWidget(
            self.sample_table,
            QtCore.Qt.AlignmentFlag.AlignCenter,
        )

        menubar = QPushButton(_("Menu"))
        self.main_bottom_layout = QVBoxLayout()
        self.main_bottom_hlayout = QHBoxLayout()
        self.main_bottom_hlayout.addWidget(menubar)
        self.main_bottom_hlayout.addLayout(self.main_bottom_layout)
        self.main_bottom_layout.addLayout(self.file_selector.layout)
        self.smp_tab_main_verticalLayout.addLayout(self.main_bottom_hlayout)

        glbl_shared.APP.processEvents()

        menuFile = QMenu("Menu", menubar)
        action_open_in_browser = menuFile.addAction(
            _("Open Selected Sample in Browser"))
        menuFile.addSeparator()
        actionSave_instrument_to_file = menuFile.addAction(
            _("Save Instrument to File..."))
        actionOpen_instrument_from_file = menuFile.addAction(
            _("Open Instrument from File..."))
        menuFile.addSeparator()
        action_copy_instrument = menuFile.addAction(_("Copy Instrument"))
        action_paste_instrument = menuFile.addAction(_("Paste Instrument"))
        menuFile.addSeparator()
        actionMapToKeys = menuFile.addAction(
            _("Map All Samples to 1 Key"))
        actionMapToWhiteKeys = menuFile.addAction(
            _("Map All Samples to 1 White Key"))
        actionMapToMonoFX = menuFile.addAction(
            _("Map All Samples to Own MonoFX Group"))
        f_map_octaves_action = menuFile.addAction(
            _("Map to 2 octaves per sample"))
        menuFile.addSeparator()
        actionClearAllSamples = menuFile.addAction(
            _("Clear All Samples"))
        menuFile.addSeparator()
        actionImportSfz = menuFile.addAction(
            _("Import SFZ..."))
        menuFile.addSeparator()
        actionTsPs = menuFile.addAction(
            _("Time-Stretch/Pitch-Shift..."))

        menubar.setMenu(menuFile)
        menuFile.addSeparator()
        menuSetAll = menuFile.addMenu("Set all...")

        actionSetAllHighPitches = menuSetAll.addAction(_("High Notes"))
        actionSetAllLowPitches = menuSetAll.addAction(_("Low Notes"))
        actionSetAllVolumes = menuSetAll.addAction(_("Volumes"))
        actionSetAllVelSens = menuSetAll.addAction(_("Velocity Sensitivity"))
        actionSetAllHighVels = menuSetAll.addAction(_("High Velocities"))
        actionSetAllLowVels = menuSetAll.addAction(_("Low Velocities"))
        actionSetAllPitches = menuSetAll.addAction(_("Pitches"))
        actionSetAllTunes = menuSetAll.addAction(_("Tunes"))
        actionSetAllModes = menuSetAll.addAction(_("Interpolation Modes"))
        actionSetAllNoiseTypes = menuSetAll.addAction(_("Noise Types"))
        actionSetAllNoiseAmps = menuSetAll.addAction(_("Noise Amps"))

        action_open_in_browser.triggered.connect(self.open_file_in_browser)
        actionSave_instrument_to_file.triggered.connect(self.saveToFile)
        actionOpen_instrument_from_file.triggered.connect(self.openFromFile)
        action_copy_instrument.triggered.connect(self.copy_instrument)
        action_paste_instrument.triggered.connect(self.paste_instrument)
        actionMapToKeys.triggered.connect(self.mapAllSamplesToOneKey)
        actionMapToWhiteKeys.triggered.connect(self.mapAllSamplesToOneWhiteKey)
        actionMapToMonoFX.triggered.connect(self.mapAllSamplesToOneMonoFXgroup)
        actionClearAllSamples.triggered.connect(self.clearAllSamples)
        actionImportSfz.triggered.connect(self.sfz_dialog)
        actionTsPs.triggered.connect(self.stretch_shift_dialog)
        f_map_octaves_action.triggered.connect(self.map_2_octaves_per_sample)

        actionSetAllHighPitches.triggered.connect(self.set_all_high_notes)
        actionSetAllLowPitches.triggered.connect(self.set_all_low_notes)
        actionSetAllVolumes.triggered.connect(self.set_all_volumes)
        actionSetAllVelSens.triggered.connect(self.set_all_vel_sens)
        actionSetAllHighVels.triggered.connect(self.set_all_high_vels)
        actionSetAllLowVels.triggered.connect(self.set_all_low_vels)
        actionSetAllPitches.triggered.connect(self.set_all_pitches)
        actionSetAllTunes.triggered.connect(self.set_all_tunes)
        actionSetAllModes.triggered.connect(self.set_all_interpolation_modes)
        actionSetAllNoiseTypes.triggered.connect(self.set_all_noise_types)
        actionSetAllNoiseAmps.triggered.connect(self.set_all_noise_amps)

        self.main_tab.addTab(self.sample_tab, _("Samples"))
        self.poly_fx_tab = QWidget()
        self.main_tab.addTab(self.poly_fx_tab, _("Poly FX"))
        self.mono_fx_tab = QWidget()
        self.main_tab.addTab(self.mono_fx_tab, _("Mono FX"))
        self.layout.addWidget(self.main_tab)
        self.main_tab.setCurrentIndex(0)
        self.sample_table.resizeColumnsToContents()
        #m_view_sample_tab
        self.view_sample_tab = QWidget()
        self.main_tab.addTab(self.view_sample_tab, _("View"))
        self.view_sample_tab_main_vlayout = QVBoxLayout(
            self.view_sample_tab)
        self.view_sample_tab_main_vlayout.setContentsMargins(0, 0, 0, 0)

        #Sample Graph
        self.sample_graph = sample_viewer_widget(
            self.sample_start_callback,
            self.sample_end_callback,
            self.loop_start_callback,
            self.loop_end_callback,
            self.fade_in_callback,
            self.fade_out_callback,
            bg_brush=QColor("#222222"),
            fg_brush=QColor("#aaaaaa"),
        )
        self.sample_graph.scene_context_menu.addSeparator()
        self.marker_all_action = \
            self.sample_graph.scene_context_menu.addAction(
            _("Apply Start/End/Fade Markers to All Samples"))
        self.marker_all_action.triggered.connect(self.on_marker_all)
        self.loop_all_action = self.sample_graph.scene_context_menu.addAction(
            _("Apply Loop Markers to All Samples"))
        self.loop_all_action.triggered.connect(self.on_loop_all)
        self.view_sample_tab_main_vlayout.addWidget(self.sample_graph)
        #The combobox for selecting the sample on the 'view' tab
        self.sample_view_select_sample_widget = QWidget()
        self.sample_view_select_sample_widget.setMaximumHeight(200)
        self.sample_view_select_sample_hlayout = QHBoxLayout(
            self.sample_view_select_sample_widget)

        #self.sample_view_select_sample_hlayout.addItem(QSpacerItem(
        #    40, 20, QSizePolicy.Policy.Expanding))
        self.sample_view_select_sample_hlayout.addWidget(
            self.sample_graph.label)
        self.sample_view_extra_controls_gridview = QGridLayout()
        self.selected_sample_index_combobox = QComboBox()
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.selected_sample_index_combobox.sizePolicy().
            hasHeightForWidth(),
        )
        self.selected_sample_index_combobox.setSizePolicy(sizePolicy1)
        self.selected_sample_index_combobox.setMinimumWidth(320)
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            self.selected_sample_index_combobox.addItem("")
        self.selected_sample_index_combobox.currentIndexChanged.connect(
            self.viewSampleSelectedIndexChanged,
        )
        self.sample_view_extra_controls_gridview.addWidget(
            self.selected_sample_index_combobox, 1, 0, 1, 1,
        )
        self.selected_sample_index_label = QLabel(_("Selected Sample"))
        self.sample_view_extra_controls_gridview.addWidget(
            self.selected_sample_index_label, 0, 0, 1, 1)
        self.sample_view_select_sample_hlayout.addItem(
            QSpacerItem(30, 1))
        self.sample_view_select_sample_hlayout.addLayout(
            self.sample_view_extra_controls_gridview)
        self.sample_view_select_sample_hlayout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding),
        )
        self.view_sample_tab_main_vlayout.addWidget(
            self.sample_view_select_sample_widget)
        #The loop mode combobox
        self.loop_mode_combobox = QComboBox(self.view_sample_tab)
        self.loop_mode_combobox.addItems([_("Off"), _("On")])
        self.loop_mode_combobox.currentIndexChanged.connect(
            self.loopModeChanged,
        )
        self.loop_tune_note_selector = note_selector_widget(0, None, None)
        self.loop_tune_button = QPushButton(_("Tune"))
        self.loop_tune_button.pressed.connect(self.on_loop_tune)
        self.sample_view_extra_controls_gridview.addWidget(
            QLabel(_("Loop Mode")), 0, 1)
        self.sample_view_extra_controls_gridview.addWidget(
            self.loop_mode_combobox, 1, 1)
        self.sample_view_extra_controls_gridview.addItem(
            QSpacerItem(30, 1), 1, 2)
        self.sample_view_extra_controls_gridview.addWidget(
            QLabel(_("Loop Tune")), 0, 3)
        self.sample_view_extra_controls_gridview.addWidget(
            self.loop_tune_note_selector.widget, 1, 3)
        self.sample_view_extra_controls_gridview.addWidget(
            self.loop_tune_button, 2, 3)

        glbl_shared.APP.processEvents()

        #The file select on the 'view' tab
        self.sample_view_file_select_hlayout = QHBoxLayout()
        self.view_file_selector = file_select_widget(self.load_files)
        self.view_file_selector.clear_button.pressed.connect(self.clearFile)
        self.view_file_selector.reload_button.pressed.connect(
            self.reloadSample)
        self.sample_view_file_select_hlayout.addLayout(
            self.view_file_selector.layout)
        self.view_sample_tab_main_vlayout.addLayout(
            self.sample_view_file_select_hlayout)

        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]

        f_knob_size = 42

        self.main_layout = QVBoxLayout(self.poly_fx_tab)

        self.hlayout0 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout0)
        self.fx0 = MultiFXSingle(
            _("FX0"),
            SAMPLER1_FX0_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=False,
            fixed_width=False,
        )
        self.hlayout0.addWidget(self.fx0.group_box)
        self.fx1 = MultiFXSingle(
            _("FX1"),
            SAMPLER1_FX1_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=False,
            fixed_width=False,
        )
        self.hlayout0.addWidget(self.fx1.group_box)
        self.fx2 = MultiFXSingle(
            _("FX2"),
            SAMPLER1_FX2_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=False,
            fixed_width=False,
        )
        self.hlayout0.addWidget(self.fx2.group_box)
        self.fx3 = MultiFXSingle(
            _("FX3"),
            SAMPLER1_FX3_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=False,
            fixed_width=False,
        )
        self.hlayout0.addWidget(self.fx3.group_box)

        self.mod_matrix = QTableWidget()
        self.mod_matrix.setRowCount(6)
        self.mod_matrix.setColumnCount(12)
        self.mod_matrix.setFixedHeight(228)
        self.mod_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.mod_matrix.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        f_hlabels = ["FX{}\nCtrl{}".format(x, y)
            for x in range(4) for y in range(1, 4)]
        self.mod_matrix.setHorizontalHeaderLabels(f_hlabels)

        self.mod_matrix.setVerticalHeaderLabels(
            [_("ADSR 1"), _("ADSR 2"), _("Ramp Env"),
             _("LFO"), _("Pitch"), _("Velocity")])
        f_port_num = SAMPLER1_PFXMATRIX_FIRST_PORT

        glbl_shared.APP.processEvents()

        for f_i_dst in range(4):
            for f_i_src in range(4):
                for f_i_ctrl in range(3):
                    f_ctrl = spinbox_control(
                        None, f_port_num,
                        self.plugin_rel_callback, self.plugin_val_callback,
                        -100, 100, 0, KC_NONE, self.port_dict)
                    f_x = (f_i_dst * 3) + f_i_ctrl
                    self.mod_matrix.setCellWidget(f_i_src, f_x, f_ctrl.control)
                    f_port_num += 1

        #The new pitch and velocity tracking controls
        f_port_num = SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL0

        for f_i_src in range(4, 6):
            for f_i_dst in range(4):
                for f_i_ctrl in range(3):
                    f_ctrl = spinbox_control(
                        None, f_port_num,
                        self.plugin_rel_callback, self.plugin_val_callback,
                        -100, 100, 0, KC_NONE, self.port_dict)
                    f_x = (f_i_dst * 3) + f_i_ctrl
                    self.mod_matrix.setCellWidget(f_i_src, f_x, f_ctrl.control)
                    f_port_num += 1

        self.hlayout1 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout1)
        self.hlayout1.addWidget(self.mod_matrix)
        self.mod_matrix.resizeColumnsToContents()

        self.hlayout2 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout2)

        self.adsr_amp = adsr_widget(
            f_knob_size, True, SAMPLER1_ATTACK,
            SAMPLER1_DECAY, SAMPLER1_SUSTAIN,
            SAMPLER1_RELEASE, _("ADSR Amp"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_attack_default=0, a_knob_type=KC_LOG_TIME,
            a_lin_port=SAMPLER1_ADSR_LIN_MAIN, a_lin_default=1,
            knob_kwargs=knob_kwargs,
        )
        #overriding the default for self, because we want a
        #low minimum default that won't click
        self.adsr_amp.release_knob.control.setMinimum(5)
        self.hlayout2.addWidget(self.adsr_amp.groupbox)
        self.adsr_filter = adsr_widget(
            f_knob_size, False, SAMPLER1_FILTER_ATTACK,
            SAMPLER1_FILTER_DECAY,
            SAMPLER1_FILTER_SUSTAIN,
            SAMPLER1_FILTER_RELEASE,
            _("ADSR 2"), self.plugin_rel_callback,
            self.plugin_val_callback, self.port_dict,
            a_knob_type=KC_LOG_TIME,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout2.addWidget(self.adsr_filter.groupbox)
        self.pitch_env = ramp_env_widget(
            f_knob_size, self.plugin_rel_callback,
            self.plugin_val_callback, self.port_dict,
            SAMPLER1_PITCH_ENV_TIME, None, _("Ramp Env"),
            knob_kwargs=knob_kwargs,
        )

        self.hlayout2.addWidget(self.pitch_env.groupbox)

        self.lfo = lfo_widget(
            f_knob_size, self.plugin_rel_callback,
            self.plugin_val_callback, self.port_dict,
            SAMPLER1_LFO_FREQ,
            SAMPLER1_LFO_TYPE, f_lfo_types, _("LFO"),
            knob_kwargs=knob_kwargs,
        )
        self.hlayout2.addWidget(self.lfo.groupbox)

        self.lfo_pitch = knob_control(
            f_knob_size, _("Pitch"), SAMPLER1_LFO_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 7)

        self.lfo_pitch_fine = knob_control(
            f_knob_size, _("Fine"),
            SAMPLER1_LFO_PITCH_FINE,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 8)

        glbl_shared.APP.processEvents()

        #MonoFX Tab
        self.mono_fx_tab_main_layout = QVBoxLayout(self.mono_fx_tab)
        self.mono_fx_tab_selected_hlayout = QHBoxLayout()
        self.mono_fx_tab_selected_sample = QComboBox(self.mono_fx_tab)
        self.mono_fx_tab_selected_sample.setMinimumWidth(330)
        self.mono_fx_tab_selected_group = QComboBox(self.mono_fx_tab)
        for f_i in range(1, SAMPLER1_MONO_FX_GROUPS_COUNT):
            self.mono_fx_tab_selected_group.addItem(str(f_i))
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            self.mono_fx_tab_selected_sample.addItem("")
        self.mono_fx_tab_selected_group.currentIndexChanged.connect(
            self.sample_selected_monofx_groupChanged)
        self.mono_fx_tab_selected_sample.currentIndexChanged.connect(
            self.monoFXSampleSelectedIndexChanged)
        self.mono_fx_tab_selected_group.setMinimumWidth(75)
        self.mono_fx_tab_selected_hlayout.addWidget(
            QLabel(_("Selected Sample:")))
        self.mono_fx_tab_selected_hlayout.addWidget(
            self.mono_fx_tab_selected_sample)
        self.mono_fx_tab_selected_hlayout.addWidget(
            QLabel(_("FX Group:")))
        self.mono_fx_tab_selected_hlayout.addWidget(
            self.mono_fx_tab_selected_group)
        self.mono_fx_tab_selected_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.mono_fx_tab_main_layout.addLayout(
            self.mono_fx_tab_selected_hlayout)

        self.monofx_sub_tab = QTabWidget()
        self.mono_fx_tab_main_layout.addWidget(self.monofx_sub_tab)

        self.monofx_sub_tab_fx = QWidget()
        self.monofx_sub_tab.addTab(self.monofx_sub_tab_fx, _("Effects"))
        self.monofx_sub_tab_fx_main_layout = QVBoxLayout(
            self.monofx_sub_tab_fx)
        self.monofx_sub_tab_fx_widget = QWidget()
        self.monofx_sub_tab_fx_layout = QVBoxLayout(
            self.monofx_sub_tab_fx_widget)
        self.monofx_sub_tab_fx_main_layout.addWidget(
            self.monofx_sub_tab_fx_widget,
            alignment=QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self.hlayout11 = QHBoxLayout()
        self.monofx_sub_tab_fx_layout.addLayout(self.hlayout11)
        self.mono_fx0 = MultiFXSingle(
            _("FX0"),
            0,
            None,
            self.monofx0_callback,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=True,
        )
        self.hlayout11.addWidget(self.mono_fx0.group_box)
        self.mono_fx1 = MultiFXSingle(
            _("FX1"),
            0,
            None,
            self.monofx1_callback,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=True,
        )
        self.hlayout11.addWidget(self.mono_fx1.group_box)
        self.hlayout12 = QHBoxLayout()
        self.monofx_sub_tab_fx_layout.addLayout(self.hlayout12)
        self.mono_fx2 = MultiFXSingle(
            _("FX2"),
            0,
            None,
            self.monofx2_callback,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=True,
        )
        self.hlayout12.addWidget(self.mono_fx2.group_box)
        self.mono_fx3 = MultiFXSingle(
            _("FX3"),
            0,
            None,
            self.monofx3_callback,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
            fixed_height=True,
        )
        self.hlayout12.addWidget(self.mono_fx3.group_box)

        self.monofx_knob_tuple = tuple(
            self.mono_fx0.knobs + self.mono_fx1.knobs +
            self.mono_fx2.knobs + self.mono_fx3.knobs)

        self.last_monofx_group = None
        self.set_monofx_knob_callbacks(0)

        self.main = main_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            SAMPLER1_MAIN_VOLUME,
            SAMPLER1_MAIN_GLIDE,
            SAMPLER1_MAIN_PITCHBEND_AMT,
            self.port_dict,
            _("Main"),
            a_min_note_port=SAMPLER1_MIN_NOTE,
            a_max_note_port=SAMPLER1_MAX_NOTE,
            a_pitch_port=SAMPLER1_MAIN_PITCH,
            knob_kwargs=knob_kwargs,
        )
        self.monofx_sub_tab_fx_layout.addWidget(self.main.group_box)
        self.main.vol_knob.control.setRange(-24, 24)

        glbl_shared.APP.processEvents()

        self.eq6 = eq6_widget(
            0,
            self.eq6_rel_callback,
            self.eq6_val_callback,
            a_vlayout=False,
            knob_kwargs=knob_kwargs,
        )
        self.monofx_sub_tab.addTab(self.eq6.widget, _("EQ"))
        self.eq6.hlayout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft
            |
            QtCore.Qt.AlignmentFlag.AlignTop
        )

        self.open_plugin_file()
        self.set_midi_learn(SAMPLER1_PORT_MAP)
        self.widget.setMinimumHeight(600)
        self.widget.setUpdatesEnabled(True)
        self.widget.update()

    def eq6_val_callback(self, a_port, a_val):
        f_eq_num = a_port // 3
        f_knob_num = a_port % 3
        f_index = self.mono_fx_tab_selected_group.currentIndex()
        f_cntrl = self.eq_ports[f_index][f_eq_num][f_knob_num]
        f_cntrl.set_value(a_val, True)

    def eq6_rel_callback(self, a_port, a_val):
        LOG.warning("eq6_rel_callback called (unexpected?)")

    def update_eq6(self, a_value):
        for f_i in range(6):
            self.eq6.eqs[f_i].freq_knob.set_value(
                self.eq_ports[a_value][f_i][0].get_value())
            self.eq6.eqs[f_i].res_knob.set_value(
                self.eq_ports[a_value][f_i][1].get_value())
            self.eq6.eqs[f_i].gain_knob.set_value(
                self.eq_ports[a_value][f_i][2].get_value())

        self.eq6.update_viewer()

    def monofx0_callback(self, a_port, a_val):
        self.monofx_all_callback(
            a_port,
            a_val,
            [
                self.monofx0knob0_ctrls,
                self.monofx0knob1_ctrls,
                self.monofx0knob2_ctrls,
                self.monofx0comboboxes,
            ],
        )

    def monofx1_callback(self, a_port, a_val):
        self.monofx_all_callback(
            a_port,
            a_val,
            [
                self.monofx1knob0_ctrls,
                self.monofx1knob1_ctrls,
                self.monofx1knob2_ctrls,
                self.monofx1comboboxes,
            ],
        )

    def monofx2_callback(self, a_port, a_val):
        self.monofx_all_callback(
            a_port,
            a_val,
            [
                self.monofx2knob0_ctrls,
                self.monofx2knob1_ctrls,
                self.monofx2knob2_ctrls,
                self.monofx2comboboxes,
            ],
        )

    def monofx3_callback(self, a_port, a_val):
        self.monofx_all_callback(
            a_port,
            a_val,
            [
                self.monofx3knob0_ctrls,
                self.monofx3knob1_ctrls,
                self.monofx3knob2_ctrls,
                self.monofx3comboboxes,
            ],
        )

    def monofx_all_callback(self, a_port, a_val, a_list):
        f_index = self.mono_fx_tab_selected_group.currentIndex()
        f_ctrl = a_list[a_port][f_index]
        f_ctrl.set_value(a_val, True)

    def sample_start_callback(self, a_val):
        f_index = self.selected_sample_index_combobox.currentIndex()
        self.sample_starts[f_index].set_value(a_val, True)

    def sample_end_callback(self, a_val):
        f_index = self.selected_sample_index_combobox.currentIndex()
        self.sample_ends[f_index].set_value(a_val, True)

    def loop_start_callback(self, a_val):
        f_index = self.selected_sample_index_combobox.currentIndex()
        self.loop_starts[f_index].set_value(a_val, True)

    def loop_end_callback(self, a_val):
        f_index = self.selected_sample_index_combobox.currentIndex()
        self.loop_ends[f_index].set_value(a_val, True)

    def fade_in_callback(self, a_val):
        f_index = self.selected_sample_index_combobox.currentIndex()
        self.fade_in_ends[f_index].set_value(a_val, True)

    def fade_out_callback(self, a_val):
        f_index = self.selected_sample_index_combobox.currentIndex()
        self.fade_out_starts[f_index].set_value(a_val, True)

    def on_marker_all(self):
        f_vals = (
            self.sample_graph.start_marker.value,
            self.sample_graph.end_marker.value,
            self.sample_graph.fade_in_marker.value,
            self.sample_graph.fade_out_marker.value,
        )
        f_lists = (
            self.sample_starts,
            self.sample_ends,
            self.fade_in_ends,
            self.fade_out_starts,
        )
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            for f_i2 in range(len(f_vals)):
                f_lists[f_i2][f_i].set_value(f_vals[f_i2], True)

    def on_loop_all(self):
        f_vals = (
            self.sample_graph.loop_start_marker.value,
            self.sample_graph.loop_end_marker.value,
            self.loop_mode_combobox.currentIndex(),
        )
        f_lists = (self.loop_starts, self.loop_ends, self.loop_modes)
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            for f_i2 in range(len(f_vals)):
                f_lists[f_i2][f_i].set_value(f_vals[f_i2], True)

    def on_loop_tune(self):
        self.find_selected_radio_button()
        if (
            self.sample_table.item(
                self.selected_row_index,
                SMP_TB_FILE_PATH_INDEX,
            ) is not None
        ):
            f_file_name = str(self.sample_table.item(
                self.selected_row_index, SMP_TB_FILE_PATH_INDEX).text())
            if f_file_name != "":
                f_graph = self.sg_project.get_sample_graph_by_name(
                    f_file_name)
                f_note = self.loop_tune_note_selector.get_value()
                f_hz = pitch_to_hz(f_note)
                f_time = 1.0 / f_hz
                f_loop_length = (f_time / f_graph.length_in_seconds) * 1000.0
                f_loop_end_value = \
                    self.loop_starts[
                    self.selected_row_index].get_value() + f_loop_length
                f_loop_end_value = clip_value(
                    f_loop_end_value,
                    self.loop_starts[self.selected_row_index].get_value() +
                        MARKER_MIN_DIFF,
                    1000.0,
                    _round=True,
                )
                self.loop_ends[self.selected_row_index].set_value(
                    f_loop_end_value, True)
                self.set_sample_graph()
                self.loop_mode_combobox.setCurrentIndex(1)

    def set_sample_graph(self):
        self.find_selected_radio_button()
        if (
            self.sample_table.item(
                self.selected_row_index,
                SMP_TB_FILE_PATH_INDEX,
            ) is not None
        ):
            f_file_name = str(
                self.sample_table.item(
                    self.selected_row_index,
                    SMP_TB_FILE_PATH_INDEX,
                ).text()
            )
            if f_file_name != "":
                f_graph = self.sg_project.get_sample_graph_by_name(
                    f_file_name)
                self.sample_graph.draw_item(
                    f_graph,
                    self.sample_starts[self.selected_row_index].get_value(),
                    self.sample_ends[self.selected_row_index].get_value(),
                    self.loop_starts[self.selected_row_index].get_value(),
                    self.loop_ends[self.selected_row_index].get_value(),
                    self.fade_in_ends[self.selected_row_index].get_value(),
                    self.fade_out_starts[self.selected_row_index].get_value())
            else:
                self.sample_graph.clear_drawn_items()
        else:
            self.sample_graph.clear_drawn_items()

    def get_selected_sample(self):
        self.find_selected_radio_button()
        if (
            self.sample_table.item(
                self.selected_row_index,
                SMP_TB_FILE_PATH_INDEX,
            ) is None
        ):
            return ""
        else:
            return str(
                self.sample_table.item(
                    self.selected_row_index,
                    SMP_TB_FILE_PATH_INDEX,
                ).text()
            )

    def open_file_in_browser(self):
        f_path = self.get_selected_sample()
        self.file_browser.open_file_in_browser(f_path)

    def open_plugin_file(self):
        AbstractPluginUI.open_plugin_file(self)
        self.sample_table.resizeColumnsToContents()
        f_combobox_items = []
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_item = self.sample_table.item(f_i, SMP_TB_FILE_PATH_INDEX)
            if f_item is None or str(f_item.text()) == "":
                f_combobox_items.append("")
            else:
                f_arr = os.path.split(str(f_item.text()))
                f_combobox_items.append(f_arr[-1])
        self.selected_sample_index_combobox.clear()
        self.selected_sample_index_combobox.addItems(f_combobox_items)
        self.mono_fx_tab_selected_sample.clear()
        self.mono_fx_tab_selected_sample.addItems(f_combobox_items)
        self.selected_radiobuttons[0].click()
        self.sample_selected_monofx_groupChanged(0)

    def configure_plugin(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        self.configure_callback(self.plugin_uid, a_key, a_message)
        self.has_updated_controls = True

    def set_configure(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        if a_key == "load":
            LOG.info("set_configure: load")
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            for f_i in range(len(f_arr)):
                if f_arr[f_i] == "":
                    f_path = ""
                else:
                    f_path = self.sg_project.get_wav_path_by_uid(
                        int(f_arr[f_i]),
                    )
                f_table_item = QTableWidgetItem(f_path)
                self.sample_table.setItem(
                    f_i,
                    SMP_TB_FILE_PATH_INDEX,
                    f_table_item,
                )
        else:
            LOG.error("Unknown configure message '{}'".format(a_key))

    def set_all_base_pitches(self):
        f_widget = note_selector_widget(0, None, None)
        self.set_all_dialog(
            f_widget,
            self.sample_base_pitches,
            _("Set all base pitches"),
        )

    def set_all_low_notes(self):
        f_widget = note_selector_widget(0, None, None)
        self.set_all_dialog(
            f_widget,
            self.sample_low_notes,
            _("Set all low notes"),
        )

    def set_all_high_notes(self):
        f_widget = note_selector_widget(0, None, None)
        self.set_all_dialog(
            f_widget,
            self.sample_high_notes,
            _("Set all high notes"),
        )

    def set_all_volumes(self):
        f_widget = spinbox_control(
            _("Low Velocity"),
            0,
            None,
            None,
            -60,
            36,
            0,
        )
        self.set_all_dialog(
            f_widget,
            self.sample_vols,
            _("Set all volumes"),
        )

    def set_all_vel_sens(self):
        f_widget = spinbox_control(
            _("Velocity Sensitivity"), 0, None, None, 0, 20, 0)
        self.set_all_dialog(
            f_widget, self.sample_vel_sens, _("Set all velocity sensitivity"))

    def set_all_low_vels(self):
        f_widget = spinbox_control(
            _("Low Velocity"), 0, None, None, 0, 127, 0)
        self.set_all_dialog(
            f_widget, self.sample_low_vels, _("Set all low velocities"))

    def set_all_high_vels(self):
        f_widget = spinbox_control(
            _("High Velocity"), 0, None, None, 0, 127, 127)
        self.set_all_dialog(
            f_widget, self.sample_high_vels, _("Set all high velocities"))

    def set_all_pitches(self):
        f_widget = spinbox_control(_("Pitch"), 0, None, None, -36, 36, 0)
        self.set_all_dialog(
            f_widget, self.sample_pitches, _("Set all sample pitches"))

    def set_all_tunes(self):
        f_widget = spinbox_control(
            _("Tune"), 0, None, None, -100, 100, 0)
        self.set_all_dialog(
            f_widget, self.sample_tunes, _("Set all sample tunes"))

    def set_all_interpolation_modes(self):
        f_widget = combobox_control(
            120, _("Mode"), 0, None, None,
            self.interpolation_modes_list)
        self.set_all_dialog(
            f_widget, self.sample_modes,
            _("Set all sample interpolation modes"))

    def set_all_noise_types(self):
        f_widget = combobox_control(
            120, _("Noise Type"), 0, None, None, self.noise_types_list)
        self.set_all_dialog(
            f_widget, self.noise_types,
            _("Set all sample interpolation modes"))

    def set_all_noise_amps(self):
        f_widget = spinbox_control(_("Tune"), 0, None, None, -60, 0, -30)
        self.set_all_dialog(f_widget, self.noise_amps, _("Set all noise amps"))

    def set_all_dialog(self, a_widget, a_list, a_title):
        def on_ok(a_val=None):
            f_val = a_widget.get_value()
            for f_item in a_list:
                f_item.set_value(f_val, True)
            f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QDialog(self.widget)
        f_window.setMinimumWidth(300)
        f_window.setWindowTitle(a_title)
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout0 = QHBoxLayout()
        f_hlayout0.addWidget(a_widget.widget)
        f_layout.addLayout(f_hlayout0)
        f_hlayout2 = QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)
        f_window.exec()

    def clearAllSamples(self):
        for i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            self.set_selected_sample_combobox_item(i, "")
            self.sample_graph.clear_drawn_items()
            f_item = QTableWidgetItem()
            f_item.setText((""))
            f_item.setFlags(
                QtCore.Qt.ItemFlag.ItemIsSelectable
                |
                QtCore.Qt.ItemFlag.ItemIsEnabled
            )
            self.sample_table.setItem(i, SMP_TB_FILE_PATH_INDEX, f_item)
        self.generate_files_string()
        self.view_file_selector.set_file((""))
        self.file_selector.set_file((""))

    def mapAllSamplesToOneMonoFXgroup(self):
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            self.monofx_groups[f_i].set_value(f_i, True)
        self.mono_fx_tab_selected_sample.setCurrentIndex(1)
        self.mono_fx_tab_selected_sample.setCurrentIndex(0)

    def mapAllSamplesToOneKey(self):
        f_current_note = 36
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            self.sample_base_pitches[f_i].set_value(f_current_note, True)
            self.sample_high_notes[f_i].set_value(f_current_note, True)
            self.sample_low_notes[f_i].set_value(f_current_note, True)
            f_current_note += 1
            if f_current_note >= 120:
                break

    def mapAllSamplesToOneWhiteKey(self):
        f_current_note = 36
        i_white_notes = 0
        f_white_notes = [2, 2, 1, 2, 2, 2, 1]
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            self.sample_base_pitches[f_i].set_value(f_current_note, True)
            self.sample_high_notes[f_i].set_value(f_current_note, True)
            self.sample_low_notes[f_i].set_value(f_current_note, True)
            f_current_note += f_white_notes[i_white_notes]
            if f_current_note >= 120:
                break
            i_white_notes += 1
            if i_white_notes >= 7:
                i_white_notes = 0

    def map_2_octaves_per_sample(self):
        f_index = 0
        for f_i in range(0, 120, 24):
            self.sample_low_notes[f_index].set_value(f_i, True)
            self.sample_base_pitches[f_index].set_value(f_i + 12, True)
            self.sample_high_notes[f_index].set_value(f_i + 24, True)
            f_index += 1

    def viewSampleSelectedIndexChanged(self, a_index):
        if self.suppress_selected_sample_changed:
            return
        self.suppress_selected_sample_changed = True
        self.selected_radiobuttons[a_index].setChecked(True)
        self.mono_fx_tab_selected_sample.setCurrentIndex(a_index)
        self.mono_fx_tab_selected_group.setCurrentIndex(
            self.monofx_groups[a_index].get_value(),
        )
        if self.sample_table.item(
            self.selected_row_index,
            SMP_TB_FILE_PATH_INDEX,
        ) is None:
            f_file_path = ""
        else:
            item = self.sample_table.item(
                a_index,
                SMP_TB_FILE_PATH_INDEX,
            )
            if item:
                f_file_path = str(item.text())
            else:
                f_file_path = ""
        self.file_selector.set_file(f_file_path)
        self.view_file_selector.set_file(f_file_path)
        self.loop_mode_combobox.setCurrentIndex(
            self.loop_modes[a_index].get_value(),
        )
        self.suppress_selected_sample_changed = False
        self.set_sample_graph()

    def monoFXSampleSelectedIndexChanged(self, a_index):
        if self.suppress_selected_sample_changed:
            return
        self.suppress_selected_sample_changed = True
        self.selected_radiobuttons[a_index].setChecked(True)
        self.selected_sample_index_combobox.setCurrentIndex(a_index)
        self.mono_fx_tab_selected_group.setCurrentIndex(
            self.monofx_groups[a_index].get_value())
        self.suppress_selected_sample_changed = False
        self.set_sample_graph()

    def loopModeChanged(self, a_value):
        self.find_selected_radio_button()
        self.loop_modes[self.selected_row_index].set_value(a_value, True)

    def set_selected_sample_combobox_item(self, a_index, a_text):
        self.suppress_selected_sample_changed = True
        self.selected_sample_index_combobox.removeItem(a_index)
        self.selected_sample_index_combobox.insertItem(a_index, a_text)
        self.selected_sample_index_combobox.setCurrentIndex(a_index)
        self.mono_fx_tab_selected_sample.removeItem(a_index)
        self.mono_fx_tab_selected_sample.insertItem(a_index, a_text)
        self.mono_fx_tab_selected_sample.setCurrentIndex(a_index)
        self.suppress_selected_sample_changed = False


    def find_selected_radio_button(self):
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            if self.selected_radiobuttons[f_i].isChecked():
                self.selected_row_index = f_i
                return

    def load_files(self, paths):
        if len(paths) > 0:
            self.find_selected_radio_button()
            f_sample_index_to_load = (self.selected_row_index)
            for i in range(len(paths)):
                path = str(paths[i])
                if path != "":
                    if not os.path.isfile(path):
                        QMessageBox.warning(
                            self, _("Error"),
                            _("File '{}' cannot be read.").format(path))
                        continue
                    self.sg_project.get_wav_uid_by_name(path)
                    self.set_selected_sample_combobox_item(
                        f_sample_index_to_load, os.path.split(path)[1])
                    f_item = QTableWidgetItem()
                    f_item.setText(path)
                    f_item.setFlags(
                        QtCore.Qt.ItemFlag.ItemIsSelectable
                        |
                        QtCore.Qt.ItemFlag.ItemIsEnabled
                    )
                    self.sample_table.setItem(
                        f_sample_index_to_load,
                        SMP_TB_FILE_PATH_INDEX, f_item)
                    f_sample_index_to_load += 1
                    if(f_sample_index_to_load >=
                    SAMPLER1_MAX_SAMPLE_COUNT):
                        break

            self.generate_files_string()
            self.configure_plugin("load", self.files_string)
            self.sample_table.resizeColumnsToContents()
            self.selectionChanged()

    def generate_files_string(self, a_index=-1):
        self.files_string = ""
        for f_i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_item = self.sample_table.item(f_i, SMP_TB_FILE_PATH_INDEX)
            if f_item is not None and str(f_item.text()).strip() != "":
                f_uid = self.sg_project.get_wav_uid_by_name(
                    str(f_item.text()))
                self.files_string += str(f_uid)
            if f_i < SAMPLER1_MAX_SAMPLE_COUNT - 1:
                self.files_string += '|'

    def clearFile(self):
        self.find_selected_radio_button()
        self.sample_graph.clear_drawn_items()
        self.set_selected_sample_combobox_item((self.selected_row_index), (""))
        f_item = QTableWidgetItem()
        f_item.setText((""))
        f_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsSelectable
            |
            QtCore.Qt.ItemFlag.ItemIsEnabled
        )
        self.sample_table.setItem(
            (self.selected_row_index), SMP_TB_FILE_PATH_INDEX, f_item)
        self.file_selector.clear_button_pressed()
        self.view_file_selector.clear_button_pressed()
        self.generate_files_string()
        self.configure_plugin("load", self.files_string)
        self.sample_table.resizeColumnsToContents()

    def reloadSample(self):
        path = str(self.file_selector.file_path.text()).strip()
        if path != "":
            f_uid = self.sg_project.get_wav_uid_by_name(path)
            constants.IPC.reload_audio_pool_item(f_uid)


    def selectionChanged(self):
        if self.suppress_selected_sample_changed:
            return
        self.suppress_selected_sample_changed = True
        self.find_selected_radio_button()
        self.selected_sample_index_combobox.setCurrentIndex(
            self.selected_row_index)
        self.mono_fx_tab_selected_sample.setCurrentIndex(
            self.selected_row_index)
        self.setSelectedMonoFX()
        self.suppress_selected_sample_changed = False
        self.selected_sample_index_combobox.setCurrentIndex(
            (self.selected_row_index))
        if self.sample_table.item(
            self.selected_row_index,
            SMP_TB_FILE_PATH_INDEX,
        ) is None:
            f_file_path = ""
        else:
            f_file_path = str(
                self.sample_table.item(
                    self.selected_row_index,
                    SMP_TB_FILE_PATH_INDEX,
                ).text(),
            )
        self.file_selector.set_file(f_file_path)
        self.view_file_selector.set_file(f_file_path)
        self.set_sample_graph()
        self.loop_mode_combobox.setCurrentIndex(
            self.loop_modes[(self.selected_row_index)].get_value(),
        )

    def file_browser_load_button_pressed(self):
        f_result = self.file_browser.files_selected()
        self.load_files(f_result)

    def file_browser_preview_button_pressed(self):
        f_list = self.file_browser.files_selected()
        if len(f_list) > 0:
            constants.IPC.preview_audio(f_list[0])

    def file_browser_stop_preview(self):
        constants.IPC.stop_preview()

    def sample_selected_monofx_groupChanged(self, a_value):
        self.mono_fx0.knobs[0].set_value(
            self.monofx0knob0_ctrls[a_value].get_value())
        self.mono_fx0.knobs[1].set_value(
            self.monofx0knob1_ctrls[a_value].get_value())
        self.mono_fx0.knobs[2].set_value(
            self.monofx0knob2_ctrls[a_value].get_value())
        self.mono_fx0.combobox.set_value(
            self.monofx0comboboxes[a_value].get_value())
        self.mono_fx1.knobs[0].set_value(
            self.monofx1knob0_ctrls[a_value].get_value())
        self.mono_fx1.knobs[1].set_value(
            self.monofx1knob1_ctrls[a_value].get_value())
        self.mono_fx1.knobs[2].set_value(
            self.monofx1knob2_ctrls[a_value].get_value())
        self.mono_fx1.combobox.set_value(
            self.monofx1comboboxes[a_value].get_value())
        self.mono_fx2.knobs[0].set_value(
            self.monofx2knob0_ctrls[a_value].get_value())
        self.mono_fx2.knobs[1].set_value(
            self.monofx2knob1_ctrls[a_value].get_value())
        self.mono_fx2.knobs[2].set_value(
            self.monofx2knob2_ctrls[a_value].get_value())
        self.mono_fx2.combobox.set_value(
            self.monofx2comboboxes[a_value].get_value())
        self.mono_fx3.knobs[0].set_value(
            self.monofx3knob0_ctrls[a_value].get_value())
        self.mono_fx3.knobs[1].set_value(
            self.monofx3knob1_ctrls[a_value].get_value())
        self.mono_fx3.knobs[2].set_value(
            self.monofx3knob2_ctrls[a_value].get_value())
        self.mono_fx3.combobox.set_value(
            self.monofx3comboboxes[a_value].get_value())

        self.update_eq6(a_value)

        if not self.suppress_selected_sample_changed:
            self.monofx_groups[self.selected_row_index].set_value(
                a_value, True)
        self.set_monofx_knob_callbacks(a_value)

    def set_monofx_knob_callbacks(self, a_value):
        for f_knob, f_nc in zip(
        self.monofx_knob_tuple, self.monofx_null_controls_tuple):
            if self.last_monofx_group is not None:
                f_nc[self.last_monofx_group].set_control_callback()
            f_nc[a_value].set_control_callback(f_knob)

        self.last_monofx_group = a_value


    def setSelectedMonoFX(self):
        self.mono_fx_tab_selected_group.setCurrentIndex(
            self.monofx_groups[self.selected_row_index].get_value())

    def stretch_shift_dialog(self):
        f_path = str(self.file_selector.file_path.text()).strip()
        if f_path == "":
            QMessageBox.warning(
                self.widget, _("Error"), _("No sample selected"))
            return

        f_base_file_name = os.path.split(f_path)[1]
        f_base_file_name = f_base_file_name.rsplit(".", 1)[0]
        LOG.info(f_base_file_name)

        def on_ok(a_val=None):
            f_stretch = f_timestretch_amt.value()
            f_crispness = f_crispness_combobox.currentIndex()
            f_base_note = f_base_note_selector.get_value()
            f_is_single = f_single_rb.isChecked()
            f_preserve_formants = f_preserve_formants_checkbox.isChecked()
            f_algo = f_algo_combobox.currentIndex()

            if f_is_single:
                f_step = 1
                f_bottom = f_pitch_shift.value()
                f_top = f_bottom
            else:
                f_step = f_step_spinbox.value()
                f_bottom = -(f_step * f_below_spinbox.value())
                f_top = (f_step * f_above_spinbox.value())

            f_step_m1 = f_step - 1

            f_proc_list = []
            f_file_list = []

            f_dir = self.sg_project.audio_tmp_folder
            f_selected_index = self.selected_row_index
            f_uid = util.gen_uid()

            for f_i in range(f_bottom, f_top, f_step):
                f_new_note = f_i + f_base_note
                f_note_str = util.note_num_to_string(f_new_note)
                if f_new_note < 0 or f_new_note > 90:
                    LOG.error("Skipping note {}, out of permissible "
                        "range".format(f_note_str))
                    continue
                if not f_is_single:
                    self.sample_base_pitches[f_selected_index].set_value(
                        f_new_note, True)
                    self.sample_low_notes[f_selected_index].set_value(
                        f_new_note, True)
                    self.sample_high_notes[f_selected_index].set_value(
                        f_new_note + f_step_m1, True)
                    f_selected_index += 1
                f_file = os.path.join(
                    f_dir, "{}-{}-{}.wav".format(
                        f_uid, f_base_file_name, f_note_str))
                if f_algo == 0:
                    f_proc = util.rubberband(
                        f_path, f_file, f_stretch, f_i,
                        f_crispness, f_preserve_formants)
                elif f_algo == 1:
                    f_proc = util.sbsms(
                        f_path, f_file, f_stretch, f_i)
                f_file_list.append(f_file)
                f_proc_list.append(f_proc)
                f_status_lineedit.setText("Starting {}".format(f_file))
                QtCore.QCoreApplication.processEvents()
                time.sleep(0.1)

            for f_item, f_file in zip(f_proc_list, f_file_list):
                f_status_lineedit.setText("Finished {}".format(f_file))
                QtCore.QCoreApplication.processEvents()
                f_item.wait()

            self.load_files(f_file_list)

            shutil.rmtree(f_dir)
            os.sgdir(f_dir)

            f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QDialog(self.widget)
        f_window.setMinimumWidth(390)
        f_window.setWindowTitle(_("Time-Stretch/Pitch-Shift Current Sample"))
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)

        f_time_gridlayout = QGridLayout()
        f_layout.addLayout(f_time_gridlayout)

        f_time_gridlayout.addWidget(QLabel(_("Base Pitch")), 1, 0)
        f_base_note_selector = note_selector_widget(0, None, None)
        f_time_gridlayout.addWidget(f_base_note_selector.widget, 1, 1)
        self.find_selected_radio_button()
        f_base_note_selector.set_value(
            self.sample_base_pitches[self.selected_row_index].get_value())

        f_time_gridlayout.addWidget(QLabel(_("Stretch:")), 3, 0)
        f_timestretch_amt = QDoubleSpinBox()
        f_timestretch_amt.setRange(0.2, 4.0)
        f_timestretch_amt.setDecimals(6)
        f_timestretch_amt.setSingleStep(0.1)
        f_timestretch_amt.setValue(1.0)
        f_time_gridlayout.addWidget(f_timestretch_amt, 3, 1)
        f_time_gridlayout.addWidget(QLabel(_("Algorithm:")), 6, 0)
        f_algo_combobox = QComboBox()
        f_algo_combobox.addItems(["Rubberband", "SBSMS"])
        f_time_gridlayout.addWidget(f_algo_combobox, 6, 1)

        f_time_gridlayout.addWidget(QLabel(_("Crispness")), 12, 0)
        f_crispness_combobox = QComboBox()
        f_crispness_combobox.setToolTip(_("Only valid for Rubberband mode."))
        f_crispness_combobox.addItems(
            [_("0 (smeared)"), _("1 (piano)"), "2", "3",
             "4", "5 (normal)", _("6 (sharp, drums)")])
        f_crispness_combobox.setCurrentIndex(5)
        f_time_gridlayout.addWidget(f_crispness_combobox, 12, 1)
        f_preserve_formants_checkbox = QCheckBox(
            _("Preserve formants?"))
        f_preserve_formants_checkbox.setToolTip(
            _("Only valid for Rubberband mode."))
        f_preserve_formants_checkbox.setChecked(True)
        f_time_gridlayout.addWidget(f_preserve_formants_checkbox, 18, 1)

        f_single_rb = QRadioButton(_("Single"))
        f_single_rb.setChecked(True)
        f_layout.addWidget(
            f_single_rb,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft,
        )

        f_pitch_gridlayout = QGridLayout()
        f_layout.addLayout(f_pitch_gridlayout)
        f_pitch_gridlayout.addWidget(QLabel(_("Pitch:")), 0, 0)
        f_pitch_shift = QDoubleSpinBox()
        f_pitch_shift.setRange(-36, 36)
        f_pitch_shift.setValue(0.0)
        f_pitch_shift.setDecimals(6)
        f_pitch_gridlayout.addWidget(f_pitch_shift, 0, 1)

        f_multi_rb = QRadioButton(_("Multi"))
        f_layout.addWidget(
            f_multi_rb,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft,
        )
        f_multi_gridlayout = QGridLayout()
        f_layout.addLayout(f_multi_gridlayout)
        f_multi_gridlayout.addWidget(
            QLabel(_("Step Size(semitones)")), 0, 0)
        f_step_spinbox = QSpinBox()
        f_step_spinbox.setRange(1, 3)
        f_multi_gridlayout.addWidget(f_step_spinbox, 0, 1)
        f_multi_gridlayout.addWidget(QLabel(_("Below (count)")), 1, 0)
        f_below_spinbox = QSpinBox()
        f_below_spinbox.setRange(0, 20)
        f_below_spinbox.setValue(12)
        f_multi_gridlayout.addWidget(f_below_spinbox, 1, 1)
        f_multi_gridlayout.addWidget(QLabel(_("Above (count)")), 2, 0)
        f_above_spinbox = QSpinBox()
        f_above_spinbox.setRange(0, 20)
        f_above_spinbox.setValue(12)
        f_multi_gridlayout.addWidget(f_above_spinbox, 2, 1)

        f_hlayout2 = QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)

        f_status_lineedit = QLineEdit()
        f_status_lineedit.setReadOnly(True)
        f_layout.addWidget(f_status_lineedit)

        f_window.exec()

    def copySamplesToSingleDirectory(self, a_dir):
        f_dir = str(a_dir)
        f_result = ""
        self.find_selected_radio_button()
        for i in range(SAMPLER1_MAX_SAMPLE_COUNT):
            f_current_file_path = self.sample_table.item(
                i, SMP_TB_FILE_PATH_INDEX)
            if f_current_file_path is None:
                continue
            f_current_file_path = str(f_current_file_path.text()).strip()
            if f_current_file_path == "":
                continue
            if not os.path.exists(f_current_file_path):
                f_current_file_path = os.path.join(
                    self.sg_project.samples_folder, f_current_file_path)
                if not os.path.exists(f_current_file_path):
                    LOG.error("File no longer exists on disk or"
                    " in cache, skipping {}".format(f_current_file_path))
                    continue
            f_file_name = os.path.basename(str(f_current_file_path))
            f_new_file_path = os.path.join(f_dir, f_file_name)
            if f_current_file_path == f_new_file_path:
                LOG.warning("Source and destination are the same, "
                    "not copying:\n{}\n{}".format(
                    f_current_file_path, f_new_file_path))
            else:
                shutil.copy(f_current_file_path, f_new_file_path)
                f_result += "sample|{}|{}\n".format(i, f_file_name)
        return f_result

    def copy_instrument(self):
        global SAMPLER1_INSTRUMENT_CLIPBOARD
        f_plugin_file = plugin_file.from_dict(
            self.port_dict,
            self.configure_dict,
            self.cc_map,
        )
        SAMPLER1_INSTRUMENT_CLIPBOARD = str(f_plugin_file)

    def paste_instrument(self):
        if SAMPLER1_INSTRUMENT_CLIPBOARD:
            f_file = plugin_file.from_str(
                SAMPLER1_INSTRUMENT_CLIPBOARD,
            )
            for k, v in list(f_file.port_dict.items()):
                f_port = int(k)
                f_value = int(v)
                self.port_dict[f_port].set_value(f_value, True)
            for k, v in list(f_file.configure_dict.items()):
                self.set_configure(k, v)
            self.save_plugin_file()
            self.open_plugin_file()
            self.generate_files_string()
            self.configure_plugin("load", self.files_string)

    def saveToFile(self, a_copy=False):
        while True:
            f_selected_path, f_filter = QFileDialog.getSaveFileName(
                self.widget,
                _("Select a directory to copy the samples to..."),
                util.HOME,
                filter=util.SAMPLER_FILE_TYPE,
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if f_selected_path is not None:
                f_selected_path = str(f_selected_path)
                if f_selected_path == "":
                    break
                if not f_selected_path.endswith(
                util.SAMPLER_FILE_TYPE_EXT):
                    f_selected_path += util.SAMPLER_FILE_TYPE_EXT
                f_dir = os.path.dirname(f_selected_path)
                if len(os.listdir(f_dir)) > 0:
                    f_answer = QMessageBox.warning(
                        self.widget, _("Warning"),
                        _("{} is not an empty directory, are you "
                        "sure you want to save here?").format(f_dir),
                        (
                            QMessageBox.StandardButton.Yes
                            |
                            QMessageBox.StandardButton.No
                        ),
                        QMessageBox.StandardButton.No)
                    if f_answer == QMessageBox.StandardButton.No:
                        continue
                f_sample_str = self.copySamplesToSingleDirectory(f_dir)
                f_plugin_file = plugin_file.from_dict(
                    self.port_dict, {}, {})
                f_result_str = "{}{}".format(f_sample_str, f_plugin_file)
                util.write_file_text(f_selected_path, f_result_str)
            else:
                break

    def openFromFile(self):
        f_selected_path, f_filter = QFileDialog.getOpenFileName(
            self.widget,
            _("Select a directory to move the samples to..."),
            util.HOME,
            filter=util.SAMPLER_FILE_TYPE,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if f_selected_path is not None:
            f_selected_path = str(f_selected_path)
            if f_selected_path == "":
                return
            f_dir = os.path.dirname(f_selected_path)
            f_file_str = util.read_file_text(f_selected_path)
            self.clearAllSamples()

            for f_line in f_file_str.split("\n"):
                f_line_arr = f_line.split("|", 2)
                if f_line_arr[0] == "\\":
                    break
                if f_line_arr[0] == "sample":
                    f_index = int(f_line_arr[1])
                    f_new_file_path = os.path.join(f_dir, f_line_arr[2])
                    f_item = QTableWidgetItem()
                    f_item.setText(f_new_file_path)
                    f_item.setFlags(
                        QtCore.Qt.ItemFlag.ItemIsSelectable
                        |
                        QtCore.Qt.ItemFlag.ItemIsEnabled
                    )
                    self.sample_table.setItem(
                        f_index, SMP_TB_FILE_PATH_INDEX, f_item)
                    f_path_sections = os.path.split(f_new_file_path)
                    self.set_selected_sample_combobox_item(
                        f_index, f_path_sections[-1])
                else:
                    f_port = int(f_line_arr[0])
                    f_value = int(f_line_arr[1])
                    self.port_dict[f_port].set_value(f_value, True)

            self.generate_files_string()
            self.configure_plugin("load", self.files_string)
            self.sample_table.resizeColumnsToContents()
            self.selectionChanged()

    def sfz_dialog(self):
        def on_file_open(a_val=None):
            f_selected_path, f_filter = QFileDialog.getOpenFileName(
                None,
                _("Import SFZ instrument..."),
                util.HOME,
                filter="SFZ file (*.sfz)",
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if f_selected_path is not None:
                f_selected_path = str(f_selected_path)
                if f_selected_path == "":
                    return
                try:
                    #Ensuring that it does not raise an exception
                    sfz.sfz_file(f_selected_path)
                    f_file_lineedit.setText(f_selected_path)
                except Exception as ex:
                    LOG.exception(ex)
                    QMessageBox.warning(
                        self.widget,
                        _("Error"),
                        _("Error importing {}\n{}").format(
                            f_selected_path,
                            ex,
                        ),
                    )
                    return

        def on_ok(a_val=None):
            f_text = str(f_file_lineedit.text())
            if f_text != "":
                for f_path in self.import_sfz(f_text):
                    f_status_label.setText(_("Loading {}").format(f_path))
                    QtCore.QCoreApplication.processEvents()
                f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QDialog(self.widget)
        f_window.setWindowTitle(_("Import SFZ"))
        f_window.setFixedSize(720, 180)
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout0 = QHBoxLayout()
        f_file_lineedit = QLineEdit()
        f_hlayout0.addWidget(f_file_lineedit)
        f_open_file_button = QPushButton(_("Open"))
        f_open_file_button.pressed.connect(on_file_open)
        f_hlayout0.addWidget(f_open_file_button)
        f_layout.addLayout(f_hlayout0)
        f_layout.addWidget(QLabel(
            _("Sampler1 only supports basic SFZ parameters such as "
            "key and velocity mapping.\nAny effects such as filters, etc... "
            "should be set manually after import.")))
        f_hlayout1 = QHBoxLayout()
        f_layout.addItem(
            QSpacerItem(10, 10, vPolicy=QSizePolicy.Policy.Expanding),
        )
        f_layout.addLayout(f_hlayout1)
        f_status_label = QLabel()
        f_hlayout1.addWidget(f_status_label)
        f_hlayout2 = QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)
        f_window.exec()

    def import_sfz(self, a_sfz_path):
        try:
            f_sfz_path = str(a_sfz_path)
            f_sfz = sfz.sfz_file(f_sfz_path)
            f_sfz_dir = os.path.dirname(f_sfz_path)
            self.clearAllSamples()

            for f_index, f_sample in zip(
                range(len(f_sfz.samples)),
                f_sfz.samples,
            ):
                if f_index >= SAMPLER1_MAX_SAMPLE_COUNT:
                    QMessageBox.warning(
                        self.widget,
                        _("Error"),
                        _(
                            "Sample count {} exceeds maximum of {}, not "
                            "loading all samples"
                        ).format(
                            len(f_sfz.samples),
                            SAMPLER1_MAX_SAMPLE_COUNT,
                        ),
                    )
                    return
                if "sample" in f_sample.dict:
                    if os.path.sep == '/':
                        f_sample_file = f_sample.dict["sample"].replace(
                            "\\",
                            "/",
                        )
                        f_new_file_path = os.path.join(
                            f_sfz_dir,
                            f_sample_file,
                        )
                        f_new_file_path = f_new_file_path.replace("//", "/")
                    elif os.path.sep == '\\':
                        f_sample_file = f_sample.dict[
                            "sample"].replace("/", "\\")
                        f_new_file_path = os.path.join(
                            f_sfz_dir, f_sample_file)
                        f_new_file_path = f_new_file_path.replace("\\\\", "\\")
                    else:
                        assert False, "Unknown os.path.sep {}".format(
                            os.path.sep)
                    try:
                        f_new_file_path = util.case_insensitive_path(
                            f_new_file_path,
                        )
                    except Exception as ex:
                        LOG.exception(ex)
                        LOG.warning(
                            f"{f_new_file_path} is missing, cannot load"
                        )
                        continue
                    yield f_new_file_path

                    f_item = QTableWidgetItem()
                    f_item.setText(f_new_file_path)
                    f_item.setFlags(
                        QtCore.Qt.ItemFlag.ItemIsSelectable
                        |
                        QtCore.Qt.ItemFlag.ItemIsEnabled
                    )
                    self.sample_table.setItem(
                        f_index, SMP_TB_FILE_PATH_INDEX, f_item)
                    f_path_sections = f_new_file_path.split(os.path.sep)
                    self.set_selected_sample_combobox_item(
                        f_index, f_path_sections[-1])

                    f_graph = self.sg_project.get_sample_graph_by_name(
                        f_new_file_path,
                    )
                    f_frame_count = float(f_graph.frame_count)

                    if "key" in f_sample.dict:
                        f_val = int(float(f_sample.dict["key"]))
                        self.sample_base_pitches[f_index].set_value(
                            f_val, True)
                        self.sample_high_notes[f_index].set_value(f_val, True)
                        self.sample_low_notes[f_index].set_value(f_val, True)

                    if "pitch_keycenter" in f_sample.dict:
                        f_val = int(float(f_sample.dict["pitch_keycenter"]))
                        self.sample_base_pitches[f_index].set_value(
                            f_val, True)

                    if "lokey" in f_sample.dict:
                        f_val = int(float(f_sample.dict["lokey"]))
                        self.sample_low_notes[f_index].set_value(f_val, True)

                    if "hikey" in f_sample.dict:
                        f_val = int(float(f_sample.dict["hikey"]))
                        self.sample_high_notes[f_index].set_value(f_val, True)

                    if "offset" in f_sample.dict:
                        f_val = (float(f_sample.dict["offset"]) /
                            f_frame_count) * 1000.0
                        f_val = clip_value(f_val, 0.0, 998.0)
                        self.sample_starts[f_index].set_value(f_val)
                    else:
                        self.sample_starts[f_index].set_value(0.0)

                    self.sample_starts[f_index].control_value_changed(
                        self.sample_starts[f_index].get_value())

                    if "end" in f_sample.dict:
                        f_val = (float(f_sample.dict["end"]) /
                            f_frame_count) * 1000.0
                        f_val = clip_value(f_val, 1.0, 999.0)
                        self.sample_ends[f_index].set_value(f_val)
                    else:
                        self.sample_ends[f_index].set_value(999.0)

                    self.sample_ends[f_index].control_value_changed(
                        self.sample_starts[f_index].get_value())

                    if "loop_mode" in f_sample.dict:
                        if (f_sample.dict["loop_mode"].strip() ==
                        "loop_continuous"):
                            self.loop_modes[f_index].set_value(1)
                        else:
                            self.loop_modes[f_index].set_value(0)
                    else:
                        self.loop_modes[f_index].set_value(0)

                    self.loop_modes[f_index].control_value_changed(
                        self.loop_modes[f_index].get_value())

                    if "loop_start" in f_sample.dict:
                        f_val = (float(f_sample.dict["loop_start"]) /
                            f_frame_count) * 1000.0
                        f_val = clip_value(f_val, 0.0, 1000.0)
                        self.loop_starts[f_index].set_value(f_val)
                    else:
                        self.loop_starts[f_index].set_value(0.0)

                    self.loop_starts[f_index].control_value_changed(
                        self.loop_starts[f_index].get_value())

                    if "loop_end" in f_sample.dict:
                        f_val = (float(f_sample.dict["loop_end"]) /
                            f_frame_count) * 1000.0
                        f_val = clip_value(f_val, 0.0, 1000.0)
                        self.loop_ends[f_index].set_value(f_val)
                    else:
                        self.loop_ends[f_index].set_value(1000.0)

                    self.loop_ends[f_index].control_value_changed(
                        self.loop_ends[f_index].get_value())

                    if "volume" in f_sample.dict:
                        f_val = int(float(f_sample.dict["volume"]))
                        f_val = clip_value(f_val, -40, 12)
                        self.sample_vols[f_index].set_value(f_val)
                        self.sample_vols[f_index].control_value_changed(f_val)

        except Exception as ex:
            LOG.exception(ex)
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _("Error parsing {}\n{}").format(a_sfz_path, ex),
            )

        self.generate_files_string()
        self.configure_plugin("load", self.files_string)
        self.sample_table.resizeColumnsToContents()
        self.selectionChanged()


