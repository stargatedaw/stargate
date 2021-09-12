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

#ifndef SVF_STEREO_H
#define SVF_STEREO_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/filter/svf.h"
#include "compiler.h"


#define SVF_FILTER_TYPE_LP 0
#define SVF_FILTER_TYPE_HP 1
#define SVF_FILTER_TYPE_BP 2
#define SVF_FILTER_TYPE_EQ 3
#define SVF_FILTER_TYPE_NOTCH 4

/*The maximum number of filter kernels to cascade.
 */
#define SVF_MAX_CASCADE 2

#define SVF_OVERSAMPLE_MULTIPLIER 4
#define SVF_OVERSAMPLE_STEP_SIZE 0.25f


typedef struct {
    SGFLT filter_input;
    SGFLT filter_last_input;
    SGFLT bp_m1;
    SGFLT lp_m1;
    SGFLT hp;
    SGFLT bp;
    SGFLT lp;
}t_svf2_kernel;

typedef struct {
    SGFLT cutoff_note;
    SGFLT cutoff_hz;
    SGFLT cutoff_filter;
    SGFLT pi2_div_sr;
    SGFLT sr;
    SGFLT filter_res;
    SGFLT filter_res_db;
    SGFLT velocity_cutoff; //, velocity_cutoff_amt;
    SGFLT cutoff_base;
    SGFLT cutoff_mod;
    SGFLT cutoff_last;
    SGFLT velocity_mod_amt;
    t_svf2_kernel filter_kernels[SVF_MAX_CASCADE][2];
    SGFLT output0;
    SGFLT output1;
} t_svf2_filter;

void v_svf2_set_cutoff(t_svf2_filter*);
void v_svf2_set_res(t_svf2_filter*, SGFLT);
void v_svf2_set_cutoff_base(t_svf2_filter*, SGFLT);
void v_svf2_set_cutoff_hz(t_svf2_filter * a_svf, SGFLT hz);
void v_svf2_add_cutoff_mod(t_svf2_filter*, SGFLT);
void v_svf2_velocity_mod(t_svf2_filter*,SGFLT);

typedef void (*fp_svf2_run_filter)(t_svf2_filter*, SGFLT, SGFLT);

/*The int is the number of cascaded filter kernels*/
fp_svf2_run_filter fp_svf2_get_run_filter_ptr(int, int);

void v_svf2_run(t_svf2_filter*, t_svf2_kernel *, SGFLT);

void v_svf2_run_2_pole_lp(t_svf2_filter*, SGFLT, SGFLT);
void v_svf2_run_4_pole_lp(t_svf2_filter*, SGFLT, SGFLT);

void v_svf2_run_2_pole_hp(t_svf2_filter*, SGFLT, SGFLT);
void v_svf2_run_4_pole_hp(t_svf2_filter*, SGFLT, SGFLT);

void v_svf2_run_2_pole_bp(t_svf2_filter*, SGFLT, SGFLT);
void v_svf2_run_4_pole_bp(t_svf2_filter*, SGFLT, SGFLT);

void v_svf2_run_2_pole_notch(t_svf2_filter*, SGFLT, SGFLT);
void v_svf2_run_4_pole_notch(t_svf2_filter*, SGFLT, SGFLT);

void v_svf2_run_no_filter(t_svf2_filter*, SGFLT, SGFLT);

void v_svf2_run_2_pole_allpass(t_svf2_filter*, SGFLT, SGFLT);

void v_svf2_reset(t_svf2_filter*);
void g_svf2_init(t_svf2_filter * f_svf, SGFLT a_sample_rate);

#endif /* SVF_STEREO_H */

