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

#ifndef MULTIFX_PLUGIN_H
#define MULTIFX_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/spectrum_analyzer.h"
#include "audiodsp/modules/delay/delay_plugin.h"
#include "audiodsp/modules/delay/reverb.h"
#include "audiodsp/modules/distortion/glitch_v2.h"
#include "audiodsp/modules/filter/peak_eq.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/modulation/gate.h"
#include "audiodsp/modules/multifx/multifx3knob.h"
#include "plugin.h"
#include "compiler.h"


#define MULTIFX_SLOW_INDEX_ITERATIONS 30

#define MULTIFX_FIRST_CONTROL_PORT 4
#define MULTIFX_FX0_KNOB0  4
#define MULTIFX_FX0_KNOB1  5
#define MULTIFX_FX0_KNOB2  6
#define MULTIFX_FX0_COMBOBOX 7
#define MULTIFX_FX1_KNOB0  8
#define MULTIFX_FX1_KNOB1  9
#define MULTIFX_FX1_KNOB2  10
#define MULTIFX_FX1_COMBOBOX 11
#define MULTIFX_FX2_KNOB0  12
#define MULTIFX_FX2_KNOB1  13
#define MULTIFX_FX2_KNOB2  14
#define MULTIFX_FX2_COMBOBOX 15
#define MULTIFX_FX3_KNOB0  16
#define MULTIFX_FX3_KNOB1  17
#define MULTIFX_FX3_KNOB2  18
#define MULTIFX_FX3_COMBOBOX 19
#define MULTIFX_FX4_KNOB0  20
#define MULTIFX_FX4_KNOB1  21
#define MULTIFX_FX4_KNOB2  22
#define MULTIFX_FX4_COMBOBOX 23
#define MULTIFX_FX5_KNOB0  24
#define MULTIFX_FX5_KNOB1  25
#define MULTIFX_FX5_KNOB2  26
#define MULTIFX_FX5_COMBOBOX 27
#define MULTIFX_FX6_KNOB0  28
#define MULTIFX_FX6_KNOB1  29
#define MULTIFX_FX6_KNOB2  30
#define MULTIFX_FX6_COMBOBOX 31
#define MULTIFX_FX7_KNOB0  32
#define MULTIFX_FX7_KNOB1  33
#define MULTIFX_FX7_KNOB2  34
#define MULTIFX_FX7_COMBOBOX 35

#define MULTIFX_LAST_CONTROL_PORT 35
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MULTIFX_COUNT 36

typedef struct {
    t_mf3_multi multieffect[8];
    fp_mf3_run fx_func_ptr[8];

    SGFLT current_sample0;
    SGFLT current_sample1;

    t_smoother_linear smoothers[8][3];
} t_multifx_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];

    PluginData *fx_knob0[8];
    PluginData *fx_knob1[8];
    PluginData *fx_knob2[8];
    PluginData *fx_combobox[8];

    SGFLT fs;
    t_multifx_mono_modules mono_modules;

    int i_slow_index;
    int is_on;

    struct MIDIEvents midi_events;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[MULTIFX_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_multifx;

void v_multifx_mono_init(t_multifx_mono_modules*, SGFLT, int);
PluginDescriptor *multifx_plugin_descriptor();

#endif /* MULTIFX_PLUGIN_H */

