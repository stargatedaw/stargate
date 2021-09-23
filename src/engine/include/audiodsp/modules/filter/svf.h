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

#ifndef SVF_H
#define SVF_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "compiler.h"


/*Define filter types for changing the function pointer*/
#define SVF_FILTER_TYPE_LP 0
#define SVF_FILTER_TYPE_HP 1
#define SVF_FILTER_TYPE_BP 2
#define SVF_FILTER_TYPE_EQ 3
#define SVF_FILTER_TYPE_NOTCH 4

/*The maximum number of filter kernels to cascade.
 */
#define SVF_MAX_CASCADE 2

/*Changing this only affects initialization of the filter,
 * you must still change the code in v_svf_set_input_value()*/
#define SVF_OVERSAMPLE_MULTIPLIER 4
#define SVF_OVERSAMPLE_STEP_SIZE 0.25f

typedef struct
{
    SGFLT filter_input, filter_last_input, bp_m1, lp_m1, hp, lp, bp;

}t_svf_kernel;


typedef struct
{
    //t_smoother_linear * cutoff_smoother;
    SGFLT cutoff_note, cutoff_hz, cutoff_filter, pi2_div_sr, sr,
            filter_res, filter_res_db, velocity_cutoff; //, velocity_cutoff_amt;

    SGFLT cutoff_base, cutoff_mod, cutoff_last,  velocity_mod_amt;
    /*For the eq*/
    SGFLT gain_db, gain_linear;
    t_svf_kernel filter_kernels [SVF_MAX_CASCADE];
} t_state_variable_filter;

void g_svf_init(t_state_variable_filter * f_svf, SGFLT a_sample_rate);
//Used to switch between values
typedef SGFLT (*fp_svf_run_filter)(t_state_variable_filter*,SGFLT);

/*The int is the number of cascaded filter kernels*/
fp_svf_run_filter svf_get_run_filter_ptr(int,int);

void v_svf_set_input_value(t_state_variable_filter*,
        t_svf_kernel *, SGFLT);

SGFLT v_svf_run_2_pole_lp(t_state_variable_filter*, SGFLT);
SGFLT v_svf_run_4_pole_lp(t_state_variable_filter*, SGFLT);

SGFLT v_svf_run_2_pole_hp(t_state_variable_filter*, SGFLT);
SGFLT v_svf_run_4_pole_hp(t_state_variable_filter*, SGFLT);

SGFLT v_svf_run_2_pole_bp(t_state_variable_filter*, SGFLT);
SGFLT v_svf_run_4_pole_bp(t_state_variable_filter*, SGFLT);

SGFLT v_svf_run_2_pole_notch(t_state_variable_filter*, SGFLT);
SGFLT v_svf_run_4_pole_notch(t_state_variable_filter*, SGFLT);

SGFLT v_svf_run_2_pole_eq(t_state_variable_filter*, SGFLT);
SGFLT v_svf_run_4_pole_eq(t_state_variable_filter*, SGFLT);

SGFLT v_svf_run_no_filter(t_state_variable_filter*, SGFLT);

SGFLT v_svf_run_2_pole_allpass(t_state_variable_filter*, SGFLT);

void v_svf_set_eq(t_state_variable_filter*, SGFLT);
void v_svf_set_eq4(t_state_variable_filter*, SGFLT);

void v_svf_reset(t_state_variable_filter*);


void v_svf_set_cutoff(t_state_variable_filter*);
void v_svf_set_res(t_state_variable_filter*,  SGFLT);
t_state_variable_filter * g_svf_get(SGFLT);
void v_svf_set_cutoff_base(t_state_variable_filter*, SGFLT);
void v_svf_add_cutoff_mod(t_state_variable_filter*, SGFLT);
void v_svf_velocity_mod(t_state_variable_filter*,SGFLT);
/* When using a filter as a smoother, use this to set it to the current value
 * to avoid a jump in value
 */
void v_svf_set_output(t_state_variable_filter * a_svf, SGFLT value);

#endif /* SVF_H */
