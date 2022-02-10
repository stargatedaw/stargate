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

#ifndef SIMPLE_FADER_PLUGIN_H
#define SIMPLE_FADER_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "plugin.h"
#include "compiler.h"


#define SFADER_FIRST_CONTROL_PORT 0
#define SFADER_VOL_SLIDER 0

#define SFADER_LAST_CONTROL_PORT 0
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SFADER_COUNT 1


typedef struct {
    SGFLT current_sample0;
    SGFLT current_sample1;

    SGFLT vol_linear;

    t_smoother_linear volume_smoother;
}t_sfader_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    SGFLT fs;
    t_sfader_mono_modules mono_modules;

    int i_mono_out;
    int i_buffer_clear;

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SFADER_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_sfader;

void v_sfader_mono_init(t_sfader_mono_modules*, SGFLT, int);
PluginDescriptor *sfader_plugin_descriptor();

#endif /* SIMPLE_FADER_PLUGIN_H */

