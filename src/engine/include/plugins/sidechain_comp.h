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

#ifndef SCC_PLUGIN_H
#define SCC_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/dynamics/sidechain_comp.h"
#include "audiodsp/modules/dynamics/sidechain_comp.h"
#include "plugin.h"
#include "compiler.h"

#define SCC_FIRST_CONTROL_PORT 0

#define SCC_THRESHOLD 0
#define SCC_RATIO 1
#define SCC_ATTACK 2
#define SCC_RELEASE 3
#define SCC_WET 4
#define SCC_UI_MSG_ENABLED 5

#define SCC_LAST_CONTROL_PORT 5
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SCC_COUNT 6

typedef struct
{
    t_scc_sidechain_comp sidechain_comp;
}t_scc_mono_modules;

typedef struct
{
    PluginData *output0;
    PluginData *output1;

    PluginData *sc_input0;
    PluginData *sc_input1;

    PluginData *threshold;
    PluginData *ratio;
    PluginData *attack;
    PluginData *release;
    PluginData *wet;
    PluginData *peak_meter;

    SGFLT fs;
    t_scc_mono_modules * mono_modules;

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
    char ui_msg_buff[64];
} t_scc;

t_scc_mono_modules * v_scc_mono_init(SGFLT, int);

PluginDescriptor *scc_plugin_descriptor();

#endif /* SCC_PLUGIN_H */

