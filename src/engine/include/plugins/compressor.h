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

#ifndef SG_COMP_PLUGIN_H
#define SG_COMP_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/dynamics/compressor.h"
#include "plugin.h"
#include "compiler.h"


#define SG_COMP_FIRST_CONTROL_PORT 0

#define SG_COMP_THRESHOLD 0
#define SG_COMP_RATIO 1
#define SG_COMP_KNEE 2
#define SG_COMP_ATTACK 3
#define SG_COMP_RELEASE 4
#define SG_COMP_GAIN 5
#define SG_COMP_MODE 6
#define SG_COMP_RMS_TIME 7
#define SG_COMP_UI_MSG_ENABLED 8

#define SG_COMP_LAST_CONTROL_PORT 8
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SG_COMP_COUNT 9

typedef struct {
    t_cmp_compressor compressor;
} t_sg_comp_mono_modules;

void v_sg_comp_mono_init(t_sg_comp_mono_modules*, SGFLT, int);

typedef struct {
    char pad1[CACHE_LINE_SIZE];

    SGFLT fs;
    t_sg_comp_mono_modules mono_modules;

    struct MIDIEvents midi_events;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SG_COMP_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char ui_msg_buff[64];
    char pad2[CACHE_LINE_SIZE];
} t_sg_comp;

PluginDescriptor *sg_comp_plugin_descriptor();
#endif /* SG_COMP_PLUGIN_H */

