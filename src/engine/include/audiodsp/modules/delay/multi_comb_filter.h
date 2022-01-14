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

#ifndef MULTI_COMB_FILTER_H
#define MULTI_COMB_FILTER_H


#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/denormal.h"
#include "compiler.h"

typedef struct {
    int buffer_size;  //The size of input_buffer
    int input_pointer;  //The index where the current sample is written to
    SGFLT delay_pointer; //
    SGFLT wet_sample;
    SGFLT output_sample;
    SGFLT feedback_db;
    SGFLT feedback_linear;
    SGFLT midi_note_number;
    SGFLT volume_recip;
    SGFLT spread;
    int comb_count;
    //How many samples, including the fractional part, to delay the signal
    SGFLT * delay_samples;
    SGFLT sr;
    SGFLT * input_buffer;
    //t_lin_interpolater * linear;
    //t_pit_pitch_core * pitch_core;
} t_mcm_multicomb;

/* v_mcm_run(
 * t_mcm_multicomb*,
 * SGFLT input value (audio sample, -1 to 1, typically)
 * );
 * This runs the filter.  You can then use the output sample in your plugin*/
void v_mcm_run(t_mcm_multicomb*,SGFLT);
/*v_mcm_set(
 * t_mcm_multicomb*,
 * SGFLT feedback (decibels -20 to 0)
 * SGFLT pitch (midi note number, 20 to 120),
 * SGFLT a_spread);
 *
 * Sets all parameters of the comb filters.
 */
void v_mcm_set(t_mcm_multicomb*, SGFLT,SGFLT,SGFLT);
/* t_mcm_multicomb * g_mcm_get(
 * int a_comb_count,
 * SGFLT a_sr) //sample rate
 */
t_mcm_multicomb * g_mcm_get(int, SGFLT);

#endif /* COMB_FILTER_H */

