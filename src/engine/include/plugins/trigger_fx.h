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

#ifndef TRIGGERFX_PLUGIN_H
#define TRIGGERFX_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/distortion/glitch_v2.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/modulation/gate.h"
#include "plugin.h"
#include "compiler.h"


#define TRIGGERFX_INPUT0  0
#define TRIGGERFX_INPUT1  1
#define TRIGGERFX_OUTPUT0  2
#define TRIGGERFX_OUTPUT1  3

#define TRIGGERFX_FIRST_CONTROL_PORT 4
#define TRIGGERFX_GATE_NOTE 4
#define TRIGGERFX_GATE_MODE 5
#define TRIGGERFX_GATE_WET 6
#define TRIGGERFX_GATE_PITCH 7
#define TRIGGERFX_GLITCH_ON 8
#define TRIGGERFX_GLITCH_NOTE 9
#define TRIGGERFX_GLITCH_TIME 10
#define TRIGGERFX_GLITCH_PB 11

#define TRIGGERFX_LAST_CONTROL_PORT 11
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define TRIGGERFX_COUNT 12

typedef struct {
    t_smoother_linear pitchbend_smoother;

    SGFLT current_sample0;
    SGFLT current_sample1;

    SGFLT vol_linear;

    t_smoother_linear gate_wet_smoother;
    t_smoother_linear glitch_time_smoother;

    t_gat_gate gate;
    SGFLT gate_on;

    t_glc_glitch_v2 glitch;
    SGFLT glitch_on;
} t_triggerfx_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];

    PluginData *gate_note;
    PluginData *gate_mode;
    PluginData *gate_wet;
    PluginData *gate_pitch;

    PluginData *glitch_on;
    PluginData *glitch_note;
    PluginData *glitch_time;
    PluginData *glitch_pb;

    SGFLT fs;
    SGFLT sv_pitch_bend_value;
    t_triggerfx_mono_modules mono_modules;

    int i_buffer_clear;

    int midi_event_types[200];
    int midi_event_ticks[200];
    SGFLT midi_event_values[200];
    int midi_event_ports[200];
    int midi_event_count;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[TRIGGERFX_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_triggerfx;

void v_triggerfx_mono_init(t_triggerfx_mono_modules*, SGFLT, int);
PluginDescriptor *triggerfx_plugin_descriptor();

#endif /* TRIGGERFX_PLUGIN_H */

