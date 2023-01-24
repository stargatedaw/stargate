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

#ifndef MULTIFX10KNOB_H
#define MULTIFX10KNOB_H

#define MULTIFX10KNOB_FX_COUNT 39
#define MULTIFX10KNOB_KNOB_COUNT 10
#define MULTIFX10_MAX_FX_COUNT 12

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/delay/chorus.h"
#include "audiodsp/modules/distortion/clipper.h"
#include "audiodsp/modules/distortion/foldback.h"
#include "audiodsp/modules/distortion/glitch.h"
#include "audiodsp/modules/distortion/lofi.h"
#include "audiodsp/modules/distortion/ring_mod.h"
#include "audiodsp/modules/distortion/sample_and_hold.h"
#include "audiodsp/modules/distortion/saturator.h"
#include "audiodsp/modules/distortion/soft_clipper.h"
#include "audiodsp/modules/dynamics/compressor.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "audiodsp/modules/filter/comb_filter.h"
#include "audiodsp/modules/filter/dc_offset_filter.h"
#include "audiodsp/modules/filter/formant_filter.h"
#include "audiodsp/modules/filter/ladder.h"
#include "audiodsp/modules/filter/peak_eq.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/signal_routing/amp_and_panner.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/signal_routing/dry_wet_pan.h"
#include "compiler.h"

/*BIG TODO:  Add a function to modify for the modulation sources*/

typedef struct {
    t_svf2_filter svf;
    t_svf2_filter svf2;
    struct LadderFilter ladder;
    t_comb_filter comb_filter0;
    t_comb_filter comb_filter1;
    t_pkq_peak_eq eq0;
    t_clipper clipper;
    t_cmp_compressor compressor;
    t_lim_limiter limiter;
    t_sat_saturator saturator;
    SGFLT output0, output1;
    SGFLT control[MULTIFX10KNOB_KNOB_COUNT];
    SGFLT control_value[MULTIFX10KNOB_KNOB_COUNT];
    SGFLT mod_value[MULTIFX10KNOB_KNOB_COUNT];
    t_audio_xfade xfader;
    t_amp_and_panner amp_and_panner;
    t_for_formant_filter formant_filter;
    t_crs_chorus chorus;
    t_glc_glitch glitch;
    t_rmd_ring_mod ring_mod;
    t_lfi_lofi lofi;
    t_sah_sample_and_hold s_and_h;
    t_grw_growl_filter growl_filter;
    t_fbk_foldback foldback;
    t_dco_dc_offset_filter dc_offset[2];
    t_soft_clipper soft_clipper;
} t_mf10_multi;

typedef void (*fp_mf10_run)(t_mf10_multi*,SGFLT,SGFLT);
typedef void (*fp_mf10_reset)(t_mf10_multi*);

struct MultiFX10MetaData {
    fp_mf10_run run;
    fp_mf10_reset reset;
    int knob_count;
};

struct MultiFX10Controls {
    PluginData* knobs[MULTIFX10KNOB_KNOB_COUNT];
    PluginData* dry;
    PluginData* wet;
    PluginData* pan;
    PluginData* type;
    PluginData* route;
};

struct MultiFX10MonoCluster {
    int fx_index;  // The index of the effect being used
    int mf10_index;  // The index of this effect within Nabu
    struct MultiFX10MetaData meta;
    // 1 if this cluster should mix the main input into it's own
    int input_main;
    struct SamplePair input;
    t_pkm_peak_meter input_peak;
    struct MultiFX10Controls controls;
    t_smoother_linear dry_smoother;
    t_smoother_linear wet_smoother;
    t_smoother_linear pan_smoother;
    t_smoother_linear smoothers[MULTIFX10KNOB_KNOB_COUNT];
    t_mf10_multi mf10;
    struct DryWetPan dry_wet_pan;
    struct SamplePair* output;
    t_pkm_peak_meter output_peak;
};

struct MultiFX10RoutingPlan {
    int active_fx_count;
    struct MultiFX10MonoCluster* steps[MULTIFX10_MAX_FX_COUNT];
};

void v_mf10_set(
    t_mf10_multi*,
    SGFLT[MULTIFX10KNOB_KNOB_COUNT],
    int
);
void v_mf10_set_from_smoothers(
    t_mf10_multi*,
    t_smoother_linear smoothers[MULTIFX10KNOB_KNOB_COUNT],
    int
);
void v_mf10_mod(t_mf10_multi*,SGFLT,SGFLT,SGFLT,SGFLT);
void v_mf10_mod_single(t_mf10_multi*,SGFLT,SGFLT, int);
void v_mf10_commit_mod(t_mf10_multi*);
void v_mf10_run_off(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_lp2(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_lp4(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_hp2(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_hp4(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_bp2(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_bp4(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_notch2(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_notch4(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_eq(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_dist(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_soft_clipper(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_comb(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_phaser_static(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_flanger_static(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_amp_panner(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_limiter(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_compressor(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_saturator(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_formant_filter(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_chorus(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_glitch(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_ring_mod(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_lofi(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_s_and_h(t_mf10_multi*, SGFLT, SGFLT);
void v_mf10_run_bp_dw(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_hp_dw(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_lp_dw(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_monofier(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_lp_hp(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_growl_filter(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_screech_lp(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_metal_comb(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_notch_dw(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_notch_spread(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_foldback(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_dc_offset(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_bp_spread(t_mf10_multi*,SGFLT,SGFLT);
void v_mf10_run_ladder4(t_mf10_multi*, SGFLT, SGFLT);

void mf10_transform_svf_filter(t_mf10_multi*);

//SGFLT f_mf10_midi_to_pitch(SGFLT);

void v_mf10_free(t_mf10_multi*);
struct MultiFX10MetaData mf10_get_meta(int);

//const fp_mf10_run mf10_function_pointers[MULTIFX10KNOB_FX_COUNT];

void v_mf10_reset_null(t_mf10_multi*);
void v_mf10_reset_svf(t_mf10_multi*);
void v_mf10_reset_glitch(t_mf10_multi*);
void v_mf10_reset_dc_offset(t_mf10_multi*);
void g_mf10_init(
    t_mf10_multi * f_result,
    SGFLT a_sample_rate,
    int a_huge_pages
);
int mf10_routing_plan_set(
    struct MultiFX10RoutingPlan* plan,
    struct MultiFX10MonoCluster* fx,
    struct SamplePair* output,
    int fx_count
);
void mf10_mono_cluster_init(struct MultiFX10MonoCluster*, SGFLT, int);

#endif /* MULTIFX10KNOB_H */

