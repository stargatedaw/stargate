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

#ifndef SREVERB_PLUGIN_H
#define SREVERB_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/delay/reverb.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "compiler.h"
#include "plugin.h"

#define SREVERB_FIRST_CONTROL_PORT 0

#define SREVERB_REVERB_TIME 0
#define SREVERB_REVERB_WET 1
#define SREVERB_REVERB_COLOR 2
#define SREVERB_REVERB_DRY 3
#define SREVERB_REVERB_PRE_DELAY 4
#define SREVERB_REVERB_HP 5
#define SREVERB_WET_PAN 6
#define SREVERB_DRY_PAN 7

#define SREVERB_LAST_CONTROL_PORT 7
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SREVERB_COUNT 8

typedef struct {
    t_smoother_linear reverb_smoother;
    t_smoother_linear reverb_dry_smoother;
    t_smoother_linear dry_pan_smoother;
    t_pn2_panner2 dry_panner;
    t_smoother_linear wet_pan_smoother;
    t_pn2_panner2 wet_panner;
    t_rvb_reverb reverb;
} t_sreverb_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];

    SGFLT fs;
    t_sreverb_mono_modules mono_modules;

    struct MIDIEvents midi_events;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SREVERB_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_sreverb;

void v_sreverb_mono_init(t_sreverb_mono_modules*, SGFLT, int);
PluginDescriptor *sreverb_plugin_descriptor();

#endif /* SREVERB_PLUGIN_H */

