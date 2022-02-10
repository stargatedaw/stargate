/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef SGEQ_PLUGIN_H
#define SGEQ_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/delay/reverb.h"
#include "audiodsp/modules/distortion/glitch_v2.h"
#include "audiodsp/modules/filter/peak_eq.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/modulation/gate.h"
#include "audiodsp/modules/multifx/multifx3knob.h"
#include "plugin.h"
#include "compiler.h"

#define SGEQ_EQ_COUNT 6

#define SGEQ_FIRST_CONTROL_PORT 4

#define SGEQ_EQ1_FREQ 4
#define SGEQ_EQ1_RES 5
#define SGEQ_EQ1_GAIN 6
#define SGEQ_EQ2_FREQ 7
#define SGEQ_EQ2_RES 8
#define SGEQ_EQ2_GAIN 9
#define SGEQ_EQ3_FREQ 10
#define SGEQ_EQ3_RES 11
#define SGEQ_EQ3_GAIN 12
#define SGEQ_EQ4_FREQ 13
#define SGEQ_EQ4_RES 14
#define SGEQ_EQ4_GAIN 15
#define SGEQ_EQ5_FREQ 16
#define SGEQ_EQ5_RES 17
#define SGEQ_EQ5_GAIN 18
#define SGEQ_EQ6_FREQ 19
#define SGEQ_EQ6_RES 20
#define SGEQ_EQ6_GAIN 21
#define SGEQ_SPECTRUM_ENABLED 22

#define SGEQ_PRE_FX0_KNOB0 23
#define SGEQ_PRE_FX0_KNOB1 24
#define SGEQ_PRE_FX0_KNOB2 25
#define SGEQ_PRE_FX0_COMBOBOX 26
#define SGEQ_PRE_FX1_KNOB0 27
#define SGEQ_PRE_FX1_KNOB1 28
#define SGEQ_PRE_FX1_KNOB2 29
#define SGEQ_PRE_FX1_COMBOBOX 30
#define SGEQ_PRE_FX2_KNOB0 31
#define SGEQ_PRE_FX2_KNOB1 32
#define SGEQ_PRE_FX2_KNOB2 33
#define SGEQ_PRE_FX2_COMBOBOX 34
#define SGEQ_PRE_FX3_KNOB0 35
#define SGEQ_PRE_FX3_KNOB1 36
#define SGEQ_PRE_FX3_KNOB2 37
#define SGEQ_PRE_FX3_COMBOBOX 38
#define SGEQ_PRE_FX4_KNOB0 39
#define SGEQ_PRE_FX4_KNOB1 40
#define SGEQ_PRE_FX4_KNOB2 41
#define SGEQ_PRE_FX4_COMBOBOX 42
#define SGEQ_PRE_FX5_KNOB0 43
#define SGEQ_PRE_FX5_KNOB1 44
#define SGEQ_PRE_FX5_KNOB2 45
#define SGEQ_PRE_FX5_COMBOBOX 46

#define SGEQ_POST_FX0_KNOB0 47
#define SGEQ_POST_FX0_KNOB1 48
#define SGEQ_POST_FX0_KNOB2 49
#define SGEQ_POST_FX0_COMBOBOX 50
#define SGEQ_POST_FX1_KNOB0 51
#define SGEQ_POST_FX1_KNOB1 52
#define SGEQ_POST_FX1_KNOB2 53
#define SGEQ_POST_FX1_COMBOBOX 54
#define SGEQ_POST_FX2_KNOB0 55
#define SGEQ_POST_FX2_KNOB1 56
#define SGEQ_POST_FX2_KNOB2 57
#define SGEQ_POST_FX2_COMBOBOX 58
#define SGEQ_POST_FX3_KNOB0 59
#define SGEQ_POST_FX3_KNOB1 60
#define SGEQ_POST_FX3_KNOB2 61
#define SGEQ_POST_FX3_COMBOBOX 62
#define SGEQ_POST_FX4_KNOB0 63
#define SGEQ_POST_FX4_KNOB1 64
#define SGEQ_POST_FX4_KNOB2 65
#define SGEQ_POST_FX4_COMBOBOX 66
#define SGEQ_POST_FX5_KNOB0 67
#define SGEQ_POST_FX5_KNOB1 68
#define SGEQ_POST_FX5_KNOB2 69
#define SGEQ_POST_FX5_COMBOBOX 70

#define SGEQ_LAST_CONTROL_PORT 70
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SGEQ_COUNT 71


typedef struct {
    t_pkq_peak_eq eqs[SGEQ_EQ_COUNT];
    t_spa_spectrum_analyzer * spectrum_analyzer;

    t_mf3_multi prefx[6];
    t_mf3_multi postfx[6];
    fp_mf3_run pre_fx_func_ptr[6];
    fp_mf3_run post_fx_func_ptr[6];
    t_smoother_linear pre_smoothers[6][3];
    t_smoother_linear post_smoothers[6][3];

} t_sgeq_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];

    PluginData *eq_freq[6];
    PluginData *eq_res[6];
    PluginData *eq_gain[6];
    PluginData *spectrum_analyzer_on;

    PluginData *pre_fx_knob0[6];
    PluginData *pre_fx_knob1[6];
    PluginData *pre_fx_knob2[6];
    PluginData *pre_fx_combobox[6];

    PluginData *post_fx_knob0[6];
    PluginData *post_fx_knob1[6];
    PluginData *post_fx_knob2[6];
    PluginData *post_fx_combobox[6];

    SGFLT fs;
    t_sgeq_mono_modules mono_modules;

    int i_buffer_clear;

    struct MIDIEvents midi_events;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SGEQ_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_sgeq;

void v_sgeq_mono_init(t_sgeq_mono_modules*, SGFLT, int);
PluginDescriptor *sgeq_plugin_descriptor();

#endif /* SGEQ_PLUGIN_H */

