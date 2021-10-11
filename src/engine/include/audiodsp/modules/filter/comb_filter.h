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

#ifndef COMB_FILTER_H
#define COMB_FILTER_H

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

#define MC_CMB_COUNT 4

typedef struct st_comb_filter {
    SGFLT delay_pointer;
    int input_pointer;  //The index where the current sample is written to
    int buffer_size;  //The size of input_buffer
    SGFLT wet_sample;
    SGFLT feedback_linear;
    SGFLT wet_db;
    SGFLT output_sample;
    SGFLT wet_linear;
    SGFLT feedback_db;
    SGFLT midi_note_number;
    //How many samples, including the fractional part, to delay the signal
    SGFLT delay_samples;
    SGFLT sr;
    SGFLT * input_buffer;
    int mc_delay_samples[MC_CMB_COUNT];
    SGFLT mc_detune;
}t_comb_filter;

void v_cmb_run(t_comb_filter*, SGFLT);
/*v_cmb_set_all(
 * t_comb_filter*,
 * SGFLT wet (decibels -20 to 0)
 * SGFLT feedback (decibels -20 to 0)
 * SGFLT pitch (midi note number, 20 to 120)
 * );
 *
 * Sets all parameters of the comb filter.
 */
void v_cmb_set_all(t_comb_filter*, SGFLT, SGFLT, SGFLT);
void v_cmb_free(t_comb_filter*);

void v_cmb_mc_run(t_comb_filter* a_cmb_ptr, SGFLT a_value);
void v_cmb_mc_set_all(
    t_comb_filter* a_cmb,
    SGFLT a_wet_db,
    SGFLT a_midi_note_number,
    SGFLT a_detune
);

void g_cmb_init(t_comb_filter * f_result, SGFLT a_sr, int a_huge_pages);

#endif /* COMB_FILTER_H */

