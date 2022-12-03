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

#ifndef PITCHGLITCH_PLUGIN_H
#define PITCHGLITCH_PLUGIN_H


#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/voice.h"
#include "audiodsp/modules/distortion/poly_glitch.h"
#include "audiodsp/modules/filter/dc_offset_filter.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/modulation/ramp_env.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "plugin.h"
#include "compiler.h"

#define PITCHGLITCH_POLYPHONY 8
#define PITCHGLITCH_POLYPHONY_THRESH 6

#define PITCHGLITCH_INPUT0  0
#define PITCHGLITCH_INPUT1  1
#define PITCHGLITCH_OUTPUT0  2
#define PITCHGLITCH_OUTPUT1  3

#define PITCHGLITCH_FIRST_CONTROL_PORT 4
#define PITCHGLITCH_MODE 4
#define PITCHGLITCH_PITCHBEND 5
#define PITCHGLITCH_DRY_WET 6
#define PITCHGLITCH_VEL_MIN 7
#define PITCHGLITCH_VEL_MAX 8
#define PITCHGLITCH_PAN 9
#define PITCHGLITCH_PITCH 10
#define PITCHGLITCH_GLIDE 11

#define PITCHGLITCH_LAST_CONTROL_PORT 11
#define PITCHGLITCH_COUNT (PITCHGLITCH_LAST_CONTROL_PORT + 1)

struct PitchGlitchMonoModules {
    t_smoother_linear pitchbend_smoother;
    t_pn2_panner2 panner;
    t_smoother_linear pan_smoother;
    struct StereoDCFilter dc_filter;
    t_smoother_linear dry_wet_smoother;
    t_audio_xfade dry_wet;
};

struct PitchGlitchControls {
    PluginData *pitchbend;
    PluginData *dry_wet;
    PluginData *mode;
    PluginData *vel_min;
    PluginData *vel_max;
    PluginData *pan;
    PluginData *pitch;
    PluginData *glide;
};

struct PitchGlitchPolyVoice {
    struct PolyGlitch glitch;
    SGFLT amp;
    t_pn2_panner2 panner;
    SGFLT note_f;
    int note;
    SGFLT unison_spread1;
    SGFLT unison_spread2;

    t_smoother_linear glide_smoother;
    t_ramp_env glide_env;
    t_ramp_env pitch_env;
    //For glide
    SGFLT last_pitch;
    //base pitch for all oscillators, to avoid redundant calculations
    SGFLT base_pitch;
    SGFLT target_pitch;
};

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    long sampleNo;
    struct PitchGlitchControls controls;
    t_voc_voices voices;
    struct PitchGlitchPolyVoice voice_data[PITCHGLITCH_POLYPHONY];
    SGFLT sv_last_note;  //For glide

    SGFLT fs;
    SGFLT sv_pitch_bend_value;
    struct PitchGlitchMonoModules mono_modules;

    int i_buffer_clear;

    t_plugin_event_queue atm_queue;
    t_plugin_event_queue midi_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[PITCHGLITCH_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_pitchglitch;

void PitchGlitchMonoInit(struct PitchGlitchMonoModules*, SGFLT);
PluginDescriptor* PitchGlitchPluginDescriptor();
void g_pitchglitch_poly_init(
    struct PitchGlitchPolyVoice* f_voice,
    SGFLT a_sr,
    int voice_num
);
void v_run_pitchglitch_voice(
    t_pitchglitch *plugin_data,
    t_voc_single_voice * a_poly_voice,
    struct PitchGlitchPolyVoice *a_voice,
    struct SamplePair input,
    struct SamplePair* out
);


#endif /* PITCHGLITCH_PLUGIN_H */

