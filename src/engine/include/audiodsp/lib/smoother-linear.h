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

#ifndef SMOOTHER_LINEAR_H
#define SMOOTHER_LINEAR_H

#include "math.h"
#include "lmalloc.h"
#include "compiler.h"

/*Comment this out when compiling for a release, as it will waste a lot of CPU*/
//#define SML_DEBUG_MODE

typedef struct
{
    SGFLT rate;
    SGFLT last_value;
    SGFLT sample_rate;
    SGFLT sr_recip;

#ifdef SML_DEBUG_MODE
    int debug_counter;
#endif
}t_smoother_linear;

/* t_smoother_linear * g_sml_get_smoother_linear(
 * SGFLT a_sample_rate,
 * SGFLT a_high, //The high value of the control
 * SGFLT a_low,  //The low value of the control
 * SGFLT a_time_in_seconds)
 *
 * There's not much good reason to change this while the synth is running
 * for controls, so you should only set it here.
 * If using this for glide or other things that must be smoothed
 * dynamically, you can use the set method below
 */
t_smoother_linear * g_sml_get_smoother_linear(SGFLT, SGFLT, SGFLT, SGFLT);
/* void v_sml_run(
 * t_smoother_linear * a_smoother,
 * SGFLT a_current_value) //the current control value you wish to smooth
 *
 * smoother->last_value will be the smoothed value
 */
void v_sml_run(t_smoother_linear * a_smoother, SGFLT);

void g_sml_init(
    t_smoother_linear * f_result,
    SGFLT a_sample_rate,
    SGFLT a_high,
    SGFLT a_low,
    SGFLT a_time_in_seconds
);

#endif /* SMOOTHER_LINEAR_H */

