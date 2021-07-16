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

#ifndef NOSVF_H
#define NOSVF_H

#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/denormal.h"
#include "compiler.h"

/* This is the same as the regular mono state variable filter,
 * except that is does not have built-in oversampling.  To use this,
 * you must have the entire signal chain oversampled, otherwise it
 * will explode at higher frequencies
 */

 /*Define filter types for changing the function pointer*/
 #define NOSVF_FILTER_TYPE_LP 0
 #define NOSVF_FILTER_TYPE_HP 1
 #define NOSVF_FILTER_TYPE_BP 2
 #define NOSVF_FILTER_TYPE_EQ 3
 #define NOSVF_FILTER_TYPE_NOTCH 4

 /*The maximum number of filter kernels to cascade.
  */
 #define NOSVF_MAX_CASCADE 3

typedef struct
{
    SGFLT bp_m1, lp_m1, hp, lp, bp;
}t_nosvf_kernel;


typedef struct
{
    //t_smoother_linear * cutoff_smoother;
    SGFLT cutoff_note, cutoff_hz, cutoff_filter, pi2_div_sr, sr,
            filter_res, filter_res_db, velocity_cutoff; //, velocity_cutoff_amt;

    SGFLT cutoff_base, cutoff_mod, cutoff_last;
    /*For the eq*/
    SGFLT gain_db, gain_linear;
    t_nosvf_kernel filter_kernels [NOSVF_MAX_CASCADE];
} t_nosvf_filter;

//Used to switch between values
typedef SGFLT (*fp_nosvf_run_filter)(t_nosvf_filter*,SGFLT);

/*The int is the number of cascaded filter kernels*/
fp_nosvf_run_filter nosvf_get_run_filter_ptr(int,int);

void v_nosvf_set_input_value(t_nosvf_filter*, t_nosvf_kernel *, SGFLT);

SGFLT v_nosvf_run_2_pole_lp(t_nosvf_filter*, SGFLT);
SGFLT v_nosvf_run_4_pole_lp(t_nosvf_filter*, SGFLT);
SGFLT v_nosvf_run_6_pole_lp(t_nosvf_filter*, SGFLT);

SGFLT v_nosvf_run_2_pole_hp(t_nosvf_filter*, SGFLT);
SGFLT v_nosvf_run_4_pole_hp(t_nosvf_filter*, SGFLT);

SGFLT v_nosvf_run_2_pole_bp(t_nosvf_filter*, SGFLT);
SGFLT v_nosvf_run_4_pole_bp(t_nosvf_filter*, SGFLT);

SGFLT v_nosvf_run_2_pole_notch(t_nosvf_filter*, SGFLT);
SGFLT v_nosvf_run_4_pole_notch(t_nosvf_filter*, SGFLT);

SGFLT v_nosvf_run_2_pole_eq(t_nosvf_filter*, SGFLT);
SGFLT v_nosvf_run_4_pole_eq(t_nosvf_filter*, SGFLT);

SGFLT v_nosvf_run_no_filter(t_nosvf_filter*, SGFLT);

SGFLT v_nosvf_run_2_pole_allpass(t_nosvf_filter*, SGFLT);

void v_nosvf_set_eq(t_nosvf_filter*, SGFLT);
void v_nosvf_set_eq4(t_nosvf_filter*, SGFLT);

void v_nosvf_reset(t_nosvf_filter*);

void v_nosvf_set_cutoff(t_nosvf_filter*);
void v_nosvf_set_res(t_nosvf_filter*,  SGFLT);
t_nosvf_filter * g_nosvf_get(SGFLT);
void v_nosvf_set_cutoff_base(t_nosvf_filter*, SGFLT);
void v_nosvf_add_cutoff_mod(t_nosvf_filter*, SGFLT);
void v_nosvf_velocity_mod(t_nosvf_filter*, SGFLT, SGFLT);
void g_nosvf_init(t_nosvf_filter * f_svf, SGFLT a_sample_rate);

extern SG_THREAD_LOCAL fp_nosvf_run_filter NOSVF_TYPES[9];

#endif /* NOSVF_H */
