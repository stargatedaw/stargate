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

#ifndef PITCH_CORE_H
#define PITCH_CORE_H

#include <math.h>

#include "audiodsp/constants.h"
#include "interpolate-linear.h"
#include "lmalloc.h"
#include "compiler.h"

typedef struct st_pit_ratio
{
    SGFLT pitch, hz, hz_recip;
}t_pit_ratio;

t_pit_ratio * g_pit_ratio();


/* SGFLT f_pit_midi_note_to_hz(
 * SGFLT a_midi_note_number)  //typical range:  20 to 124
 *
 * Convert midi note number to hz*/
SGFLT f_pit_midi_note_to_hz(SGFLT);
/* SGFLT f_pit_hz_to_midi_note(
 * SGFLT _hz) //typical range:  20 to 20000
 *
 * Convert hz to midi note number*/
SGFLT f_pit_hz_to_midi_note(SGFLT);
/* SGFLT f_pit_midi_note_to_samples(
 * SGFLT a_midi_note_number, //typical range 20 to 124
 * SGFLT a_sample_rate)
 *
 * Convert a midi note number pitch to the number of samples in a single
 * wave-length at that pitch*/
SGFLT f_pit_midi_note_to_samples(SGFLT, SGFLT);
/* SGFLT f_pit_midi_note_to_hz_fast(
 * SGFLT a_midi_note_number) //range: 20 to 124
 *
 * Convert midi note number to hz, using a fast table lookup.
 * You should prefer this function whenever possible, it is much faster than the
 * regular version.
 */
SGFLT f_pit_midi_note_to_hz_fast(SGFLT);
/* SGFLT f_pit_midi_note_to_ratio_fast(
 * SGFLT a_base_pitch, //The base pitch of the sample in MIDI note number
 * SGFLT a_transposed_pitch, //The pitch the sample will be transposed to
 * t_pit_pitch_core* a_pit,
 * t_pit_ratio * a_ratio)
 */
SGFLT f_pit_midi_note_to_ratio_fast(SGFLT, SGFLT, t_pit_ratio*);
void g_pit_ratio_init(t_pit_ratio * f_result);

#define arr_pit_p2f_count_limit 2500.0f
#define arr_pit_p2f_count 2521
#define arr_pit_p2f_count_m1 2520

#endif /* PITCH_CORE_H */

