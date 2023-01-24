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

#ifndef MULTIFX3KNOB_H
#define MULTIFX3KNOB_H

/*This is actually count, not index TODO:  Rename*/
#define MULTIFX3KNOB_MAX_INDEX 39
#define MULTIFX3KNOB_KNOB_COUNT 3

#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/delay/chorus.h"
#include "audiodsp/modules/distortion/clipper.h"
#include "audiodsp/modules/distortion/foldback.h"
#include "audiodsp/modules/distortion/glitch.h"
#include "audiodsp/modules/distortion/lofi.h"
#include "audiodsp/modules/distortion/ring_mod.h"
#include "audiodsp/modules/distortion/sample_and_hold.h"
#include "audiodsp/modules/distortion/saturator.h"
#include "audiodsp/modules/distortion/soft_clipper.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "audiodsp/modules/filter/comb_filter.h"
#include "audiodsp/modules/filter/dc_offset_filter.h"
#include "audiodsp/modules/filter/formant_filter.h"
#include "audiodsp/modules/filter/ladder.h"
#include "audiodsp/modules/filter/peak_eq.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/signal_routing/amp_and_panner.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"

/*BIG TODO:  Add a function to modify for the modulation sources*/

typedef struct {
    int effect_index;
    int channels;  //Currently only 1 or 2 are supported
    t_svf2_filter svf;
    t_svf2_filter svf2;
    struct LadderFilter ladder;
    t_comb_filter comb_filter0;
    t_comb_filter comb_filter1;
    t_pkq_peak_eq eq0;
    t_clipper clipper;
    t_lim_limiter limiter;
    t_sat_saturator saturator;
    SGFLT output0, output1;
    SGFLT control[MULTIFX3KNOB_KNOB_COUNT];
    SGFLT control_value[MULTIFX3KNOB_KNOB_COUNT];
    SGFLT mod_value[MULTIFX3KNOB_KNOB_COUNT];
    t_audio_xfade xfader;
    t_amp_and_panner amp_and_panner;
    SGFLT outgain;  //For anything with an outgain knob
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
} t_mf3_multi;

typedef void (*fp_mf3_reset)(t_mf3_multi*);

/*A function pointer for switching between effect types*/
typedef void (*fp_mf3_run)(t_mf3_multi*,SGFLT,SGFLT);

void v_mf3_set(t_mf3_multi*,SGFLT,SGFLT,SGFLT);
void v_mf3_mod(t_mf3_multi*,SGFLT,SGFLT,SGFLT,SGFLT);
void v_mf3_mod_single(t_mf3_multi*,SGFLT,SGFLT, int);
void v_mf3_commit_mod(t_mf3_multi*);
void v_mf3_run_off(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_lp2(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_lp4(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_hp2(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_hp4(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_bp2(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_bp4(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_notch2(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_notch4(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_eq(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_dist(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_soft_clipper(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_comb(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_phaser_static(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_flanger_static(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_amp_panner(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_limiter(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_saturator(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_formant_filter(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_chorus(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_glitch(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_ring_mod(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_lofi(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_s_and_h(t_mf3_multi*, SGFLT, SGFLT);
void v_mf3_run_bp_dw(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_hp_dw(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_lp_dw(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_monofier(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_lp_hp(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_growl_filter(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_screech_lp(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_metal_comb(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_notch_dw(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_notch_spread(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_foldback(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_dc_offset(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_bp_spread(t_mf3_multi*,SGFLT,SGFLT);
void v_mf3_run_ladder4(t_mf3_multi*,SGFLT,SGFLT);

void f_mfx_transform_svf_filter(t_mf3_multi*);

//SGFLT f_mf3_midi_to_pitch(SGFLT);

t_mf3_multi * g_mf3_get(SGFLT);
void v_mf3_free(t_mf3_multi*);
fp_mf3_run g_mf3_get_function_pointer( int);

//const fp_mf3_run mf3_function_pointers[MULTIFX3KNOB_MAX_INDEX];

void v_mf3_reset_null(t_mf3_multi*);
void v_mf3_reset_svf(t_mf3_multi*);
void v_mf3_reset_glitch(t_mf3_multi*);
void v_mf3_reset_dc_offset(t_mf3_multi*);
void g_mf3_init(
    t_mf3_multi * f_result,
    SGFLT a_sample_rate,
    int a_huge_pages
);

/*A function pointer for switching between effect types*/
//const fp_mf3_reset mf3_reset_function_pointers[MULTIFX3KNOB_MAX_INDEX];

fp_mf3_reset g_mf3_get_reset_function_pointer(int a_fx_index);

#endif /* MULTIFX3KNOB_H */

