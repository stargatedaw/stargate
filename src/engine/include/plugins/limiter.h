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

#ifndef SG_LIM_PLUGIN_H
#define SG_LIM_PLUGIN_H

#include "plugin.h"
#include "audiodsp/modules/dynamics/compressor.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/constants.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "compiler.h"


#define SG_LIM_FIRST_CONTROL_PORT 0

#define SG_LIM_THRESHOLD 0
#define SG_LIM_CEILING 1
#define SG_LIM_RELEASE 2
#define SG_LIM_UI_MSG_ENABLED 3

#define SG_LIM_LAST_CONTROL_PORT 3
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SG_LIM_COUNT 4


typedef struct {
    t_lim_limiter limiter;
} t_sg_lim_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    SGFLT fs;
    t_sg_lim_mono_modules mono_modules;

    struct MIDIEvents midi_events;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SG_LIM_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char ui_msg_buff[64];
    char pad2[CACHE_LINE_SIZE];
} t_sg_lim;

void v_sg_lim_mono_init(t_sg_lim_mono_modules*, SGFLT a_sr, int a_plugin_uid);
PluginDescriptor *sg_lim_plugin_descriptor();


#endif /* SG_LIM_PLUGIN_H */

