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

#ifndef SGDELAY_PLUGIN_H
#define SGDELAY_PLUGIN_H

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

#define SGDELAY_FIRST_CONTROL_PORT 0
#define SGDELAY_DELAY_TIME  0
#define SGDELAY_FEEDBACK  1
#define SGDELAY_DRY  2
#define SGDELAY_WET  3
#define SGDELAY_DUCK  4
#define SGDELAY_CUTOFF 5
#define SGDELAY_STEREO 6

#define SGDELAY_LAST_CONTROL_PORT 6
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SGDELAY_COUNT 7


typedef struct {
    t_sg_delay * delay;
    t_smoother_linear time_smoother;

    SGFLT current_sample0;
    SGFLT current_sample1;

    SGFLT vol_linear;
} t_sgdelay_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];

    SGFLT fs;
    t_sgdelay_mono_modules mono_modules;

    struct MIDIEvents midi_events;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SGDELAY_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_sgdelay;

void v_sgdelay_mono_init(t_sgdelay_mono_modules*, SGFLT, int);
PluginDescriptor *sgdelay_plugin_descriptor();

#endif /* SGDELAY_PLUGIN_H */

