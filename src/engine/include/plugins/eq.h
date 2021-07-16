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

#define SGEQ_LAST_CONTROL_PORT 22
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SGEQ_COUNT 23


typedef struct
{
    SGFLT current_sample0;
    SGFLT current_sample1;

    SGFLT vol_linear;

    t_pkq_peak_eq eqs[SGEQ_EQ_COUNT];
    t_spa_spectrum_analyzer * spectrum_analyzer;
}t_sgeq_mono_modules;

typedef struct
{
    PluginData *output0;
    PluginData *output1;

    PluginData *eq_freq[6];
    PluginData *eq_res[6];
    PluginData *eq_gain[6];
    PluginData *spectrum_analyzer_on;

    SGFLT fs;
    t_sgeq_mono_modules * mono_modules;

    int i_buffer_clear;

    int midi_event_types[200];
    int midi_event_ticks[200];
    SGFLT midi_event_values[200];
    int midi_event_ports[200];
    int midi_event_count;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT * port_table;
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
} t_sgeq;

t_sgeq_mono_modules * v_sgeq_mono_init(SGFLT, int);
PluginDescriptor *sgeq_plugin_descriptor();

#endif /* SGEQ_PLUGIN_H */

