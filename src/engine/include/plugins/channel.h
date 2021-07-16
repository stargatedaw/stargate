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

#ifndef SGCHNL_PLUGIN_H
#define SGCHNL_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "plugin.h"
#include "compiler.h"

#define SGCHNL_FIRST_CONTROL_PORT 0
#define SGCHNL_VOL_SLIDER 0
#define SGCHNL_GAIN 1
#define SGCHNL_PAN 2
#define SGCHNL_LAW 3

#define SGCHNL_LAST_CONTROL_PORT 3
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SGCHNL_COUNT 4


typedef struct
{
    SGFLT current_sample0;
    SGFLT current_sample1;

    t_smoother_linear volume_smoother;
    t_smoother_linear pan_smoother;

    t_pn2_panner2 panner;
}t_sgchnl_mono_modules;

typedef struct
{
    SGFLT * buffers[2];
    PluginData *vol_slider;
    PluginData *gain;
    PluginData *pan;
    PluginData *pan_law;
    SGFLT fs;
    t_sgchnl_mono_modules * mono_modules;

    int i_mono_out;
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
} t_sgchnl;

t_sgchnl_mono_modules * v_sgchnl_mono_init(SGFLT, int);
PluginDescriptor *sgchnl_plugin_descriptor();

#endif /* SGCHNL_PLUGIN_H */

