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

#ifndef WIDEMIXER_PLUGIN_H
#define WIDEMIXER_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/filter/dc_offset_filter.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "plugin.h"
#include "compiler.h"

#define WIDEMIXER_FIRST_CONTROL_PORT 0
#define WIDEMIXER_VOL_SLIDER 0
#define WIDEMIXER_GAIN 1
#define WIDEMIXER_PAN 2
#define WIDEMIXER_LAW 3
#define WIDEMIXER_INVERT_MODE 4
#define WIDEMIXER_STEREO_MODE 5
#define WIDEMIXER_BASS_MONO_ON 6
#define WIDEMIXER_BASS_MONO 7
#define WIDEMIXER_BASS_MONO_SOLO 8
#define WIDEMIXER_STEREO_EMPHASIS 9
#define WIDEMIXER_DC_OFFSET 10
#define WIDEMIXER_MUTE 11
#define WIDEMIXER_BASS_MONO_LOW 12
#define WIDEMIXER_BASS_MONO_HIGH 13

#define WIDEMIXER_LAST_CONTROL_PORT 13
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define WIDEMIXER_COUNT 14

#define WIDEMIXER_STEREO_MODE_STEREO 0
#define WIDEMIXER_STEREO_MODE_LEFT 1
#define WIDEMIXER_STEREO_MODE_RIGHT 2
#define WIDEMIXER_STEREO_MODE_SWAP 3

#define WIDEMIXER_INVERT_MODE_NEITHER 0
#define WIDEMIXER_INVERT_MODE_LEFT 1
#define WIDEMIXER_INVERT_MODE_RIGHT 2
#define WIDEMIXER_INVERT_MODE_BOTH 3


typedef struct {
    SGFLT current_sample0;
    SGFLT current_sample1;

    t_smoother_linear volume_smoother;
    t_smoother_linear pan_smoother;

    t_pn2_panner2 panner;

    t_dco_dc_offset_filter dc_filter[2];
    t_svf2_filter bass_mono_filter;
    t_audio_xfade xfade;
} t_widemixer_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    PluginData* vol_slider;
    PluginData* gain;
    PluginData* pan;
    PluginData* pan_law;
    PluginData* invert_mode;
    PluginData* stereo_mode;
    PluginData* bass_mono_on;
    PluginData* bass_mono;
    PluginData* bass_mono_solo;
    PluginData* bass_mono_low;
    PluginData* bass_mono_high;
    PluginData* mid_side;
    PluginData* dc_offset;
    PluginData* mute;

    SGFLT fs;
    t_widemixer_mono_modules mono_modules;

    int midi_event_types[200];
    int midi_event_ticks[200];
    SGFLT midi_event_values[200];
    int midi_event_ports[200];
    int midi_event_count;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[WIDEMIXER_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_widemixer;

void v_widemixer_mono_init(t_widemixer_mono_modules*, SGFLT, int);
PluginDescriptor *widemixer_plugin_descriptor();

#endif /* WIDEMIXER_PLUGIN_H */

