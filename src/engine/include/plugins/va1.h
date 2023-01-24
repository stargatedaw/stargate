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

#ifndef VA1_PLUGIN_H
#define VA1_PLUGIN_H

#include "compiler.h"

#include "audiodsp/constants.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/voice.h"
#include "audiodsp/modules/distortion/multi.h"
#include "audiodsp/modules/filter/ladder.h"
#include "audiodsp/modules/filter/nosvf.h"
#include "audiodsp/modules/modulation/adsr.h"
#include "audiodsp/modules/modulation/ramp_env.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "audiodsp/modules/oscillator/noise.h"
#include "audiodsp/modules/oscillator/osc_simple.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "plugin.h"

#define VA1_ATTACK  2
#define VA1_DECAY   3
#define VA1_SUSTAIN 4
#define VA1_RELEASE 5
#define VA1_TIMBRE  6
#define VA1_RES  7
#define VA1_DIST 8
#define VA1_FILTER_ATTACK  9
#define VA1_FILTER_DECAY   10
#define VA1_FILTER_SUSTAIN 11
#define VA1_FILTER_RELEASE 12
#define VA1_NOISE_AMP 13
#define VA1_FILTER_ENV_AMT 14
#define VA1_DIST_WET 15
#define VA1_OSC1_TYPE 16
#define VA1_OSC1_PITCH 17
#define VA1_OSC1_TUNE 18
#define VA1_OSC1_VOLUME 19
#define VA1_OSC2_TYPE 20
#define VA1_OSC2_PITCH 21
#define VA1_OSC2_TUNE 22
#define VA1_OSC2_VOLUME 23
#define VA1_MAIN_VOLUME 24
#define VA1_UNISON_VOICES1 25
#define VA1_UNISON_SPREAD1 26
#define VA1_MAIN_GLIDE 27
#define VA1_MAIN_PITCHBEND_AMT 28
#define VA1_PITCH_ENV_TIME 29
#define VA1_PITCH_ENV_AMT 30
#define VA1_LFO_FREQ 31
#define VA1_LFO_TYPE 32
#define VA1_LFO_AMP 33
#define VA1_LFO_PITCH 34
#define VA1_LFO_FILTER 35
#define VA1_OSC_HARD_SYNC 36
#define VA1_RAMP_CURVE 37
#define VA1_FILTER_KEYTRK 38
#define VA1_MONO_MODE 39
#define VA1_LFO_PHASE 40
#define VA1_LFO_PITCH_FINE 41
#define VA1_ADSR_PREFX 42
#define VA1_MIN_NOTE 43
#define VA1_MAX_NOTE 44
#define VA1_MAIN_PITCH 45
#define VA1_UNISON_VOICES2 46
#define VA1_UNISON_SPREAD2 47
#define VA1_NOISE_TYPE 48
#define VA1_FILTER_TYPE 49
#define VA1_FILTER_VELOCITY 50
#define VA1_DIST_OUTGAIN 51
#define VA1_OSC1_PB 52
#define VA1_OSC2_PB 53
#define VA1_DIST_TYPE 54
#define VA1_ADSR_LIN_MAIN 55
#define VA1_PAN 56
#define VA1_ATTACK_PMN_START 57
#define VA1_ATTACK_PMN_END 58
#define VA1_DECAY_PMN_START 59
#define VA1_DECAY_PMN_END 60
#define VA1_SUSTAIN_PMN_START 61
#define VA1_SUSTAIN_PMN_END 62
#define VA1_RELEASE_PMN_START 63
#define VA1_RELEASE_PMN_END 64

/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define VA1_COUNT 65

#define VA1_POLYPHONY 24
#define VA1_POLYPHONY_THRESH 12

typedef struct _t_va1 t_va1;
typedef struct _t_va1_poly_voice t_va1_poly_voice;

typedef SGFLT (*va1_filter_func)(t_va1*, t_va1_poly_voice*, SGFLT);

typedef struct {
    t_smoother_linear filter_smoother;
    t_smoother_linear pitchbend_smoother;
    t_smoother_linear lfo_smoother;
    t_nosvf_filter aa_filterL;
    t_nosvf_filter aa_filterR;

    t_smoother_linear pan_smoother;
    t_pn2_panner2 panner;
} t_va1_mono_modules;

typedef struct _t_va1_poly_voice {
    SGFLT amp;
    t_pn2_panner2 panner;
    SGFLT note_f;
    int note;
    SGFLT osc1_linamp;
    SGFLT osc2_linamp;
    SGFLT noise_linamp;
    int hard_sync;
    int noise_prefx;
    fp_noise_func_ptr noise_func_ptr;
    int adsr_prefx;
    SGFLT unison_spread1;
    SGFLT unison_spread2;
    SGFLT dist_out_gain;
    SGFLT osc1pb;
    SGFLT osc2pb;

    SGFLT lfo_amp_output, lfo_pitch_output, lfo_filter_output;

    t_smoother_linear glide_smoother;
    t_ramp_env glide_env;
    t_lfs_lfo lfo1;
    t_ramp_env pitch_env;
    //For glide
    SGFLT last_pitch;
      //base pitch for all oscillators, to avoid redundant calculations
    SGFLT base_pitch;
    SGFLT target_pitch;

    SGFLT osc1_pitch_adjust, osc2_pitch_adjust;

    t_osc_simple_unison osc_unison1;
    t_osc_simple_unison osc_unison2;
    t_white_noise white_noise1;

    SGFLT noise_amp;
    SGFLT filter_keytrk;

    t_adsr adsr_filter;
    fp_adsr_run adsr_run_func;
    t_adsr adsr_amp;
    t_nosvf_filter svf_filter;
    struct LadderFilter ladder_filter;
    va1_filter_func filter_func;

    t_mds_multidist mdist;
    fp_multi_dist mdist_fp;
} t_va1_poly_voice;

typedef struct _t_va1 {
    char pad1[CACHE_LINE_SIZE];
    int oversample;
    SGFLT os_recip;
    struct SamplePair* os_buffer;
    PluginData *tune;
    PluginData *adsr_lin_main;
    PluginData *attack;
    PluginData *attack_start;
    PluginData *attack_end;
    PluginData *decay;
    PluginData *decay_start;
    PluginData *decay_end;
    PluginData *sustain;
    PluginData *sustain_start;
    PluginData *sustain_end;
    PluginData *release;
    PluginData *release_start;
    PluginData *release_end;
    PluginData *timbre;
    PluginData *res;
    PluginData *filter_type;
    PluginData *filter_vel;
    PluginData *dist;
    PluginData *dist_out_gain;
    PluginData *dist_wet;
    PluginData *dist_type;
    PluginData *main_pitch;

    PluginData *attack_f;
    PluginData *decay_f;
    PluginData *sustain_f;
    PluginData *release_f;

    PluginData *osc1pitch;
    PluginData *osc1tune;
    PluginData *osc1type;
    PluginData *osc1vol;
    PluginData *osc1pb;

    PluginData *osc2pitch;
    PluginData *osc2tune;
    PluginData *osc2type;
    PluginData *osc2vol;
    PluginData *osc2pb;

    PluginData *filter_env_amt;
    PluginData *filter_keytrk;
    PluginData *main_vol;

    PluginData *noise_amp;
    PluginData *noise_type;

    PluginData *uni_voice1;
    PluginData *uni_voice2;
    PluginData *uni_spread1;
    PluginData *uni_spread2;
    PluginData *main_glide;
    PluginData *main_pb_amt;

    PluginData *pitch_env_amt;
    PluginData *pitch_env_time;

    PluginData *lfo_freq;
    PluginData *lfo_type;
    PluginData *lfo_phase;
    PluginData *lfo_amp;
    PluginData *lfo_pitch;
    PluginData *lfo_pitch_fine;
    PluginData *lfo_filter;
    PluginData *ramp_curve;

    PluginData *sync_hard;
    PluginData *adsr_prefx;
    PluginData *mono_mode;
    PluginData *min_note;
    PluginData *max_note;

    PluginData *pan;

    t_va1_poly_voice data[VA1_POLYPHONY];
    t_voc_voices voices;
    long sampleNo;

    SGFLT fs;
    t_va1_mono_modules mono_modules;

    SGFLT sv_pitch_bend_value;
    SGFLT sv_last_note;  //For glide
    SGFLT main_vol_lin;

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    SGFLT port_table[VA1_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_va1;


void g_va1_poly_init(t_va1_poly_voice*, SGFLT, int);
void v_va1_poly_note_off(t_va1_poly_voice * a_voice, int a_fast);
void v_va1_mono_init(t_va1_mono_modules*, SGFLT);
PluginDescriptor *va1_plugin_descriptor();
PluginHandle g_va1_instantiate(
    PluginDescriptor * descriptor,
    int a_sr,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
);

extern SG_THREAD_LOCAL va1_filter_func VA1_FILTER_FUNCS[10];

#endif /* RAY_VSYNTH_H */
