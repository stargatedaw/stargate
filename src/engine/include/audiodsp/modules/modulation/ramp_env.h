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

#ifndef RAMP_ENV_H
#define RAMP_ENV_H

#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "compiler.h"

typedef struct st_ramp_env
{
    SGFLT output;  //if == 1, the ramp can be considered finished running
    SGFLT output_multiplied;
    SGFLT ramp_time;
    SGFLT ramp_inc;
    SGFLT sr;
    SGFLT sr_recip;
    SGFLT output_multiplier;
    SGFLT curve;  //0.0-1.0, for the interpolator
    SGFLT last_curve;  //0.0-1.0, for the interpolator
    SGFLT curve_table[5];
}t_ramp_env;


void f_rmp_run_ramp(t_ramp_env*);
/*void v_rmp_retrigger(
 * t_ramp_env* a_rmp_ptr,
 * SGFLT a_time,
 * SGFLT a_multiplier)
 */
void v_rmp_retrigger(t_ramp_env*,SGFLT,SGFLT);
/*Glide with constant time in seconds*/
void v_rmp_retrigger_glide_t(t_ramp_env*,SGFLT,SGFLT,SGFLT);
/*Glide with constant rate in seconds-per-octave*/
void v_rmp_retrigger_glide_r(t_ramp_env*,SGFLT,SGFLT,SGFLT);
/* void v_rmp_set_time(
 * t_ramp_env* a_rmp_ptr,
 * SGFLT a_time)  //time in seconds
 *
 * Set envelope time without retriggering the envelope
 */
void v_rmp_set_time(t_ramp_env*,SGFLT);
t_ramp_env * g_rmp_get_ramp_env(SGFLT);
void f_rmp_run_ramp_curve(t_ramp_env* a_rmp_ptr);
void v_rmp_retrigger_curve(
    t_ramp_env* a_rmp_ptr,
    SGFLT a_time,
    SGFLT a_multiplier,
    SGFLT a_curve
);

void g_rmp_init(t_ramp_env * f_result, SGFLT a_sr);
#endif /* RAMP_ENV_H */

