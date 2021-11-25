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

#ifndef OSC_SIMPLE_H
#define OSC_SIMPLE_H

#include "audiodsp/lib/osc_core.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

typedef SGFLT (*fp_get_osc_func_ptr)(t_osc_core*);

typedef struct {
    SGFLT sr_recip;
    //Set this to the max number of voices, not to exceed OSC_UNISON_MAX_VOICES
    int voice_count;
    fp_get_osc_func_ptr osc_type;
    SGFLT bottom_pitch;
    SGFLT pitch_inc;
    SGFLT voice_inc [OSC_UNISON_MAX_VOICES];
    t_osc_core osc_cores [OSC_UNISON_MAX_VOICES];
    //Restart the oscillators at the same phase on each note-on
    SGFLT phases [OSC_UNISON_MAX_VOICES];
    SGFLT uni_spread;
    //Set this with unison voices to prevent excessive volume
    SGFLT last_pitch;
    SGFLT adjusted_amp;
    SGFLT current_sample;  //current output sample for the entire oscillator
    int is_resetting;  //For oscillator sync
} t_osc_simple_unison;


void v_osc_set_uni_voice_count(t_osc_simple_unison*, int);
void v_osc_set_unison_pitch(
    t_osc_simple_unison * a_osc_ptr,
    SGFLT a_spread,
    SGFLT a_pitch
);
SGFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr);
SGFLT f_get_saw(t_osc_core *);
SGFLT f_get_sine(t_osc_core *);
SGFLT f_get_square(t_osc_core *);
SGFLT f_get_triangle(t_osc_core *);
SGFLT f_get_osc_off(t_osc_core *);
void v_osc_set_simple_osc_unison_type(t_osc_simple_unison *, int);
void v_osc_note_on_sync_phases(t_osc_simple_unison *);
void g_osc_init_osc_simple_single(
    t_osc_simple_unison * f_result,
    SGFLT a_sample_rate,
    int voice_num
);
void g_osc_simple_unison_init(
    t_osc_simple_unison * f_result,
    SGFLT a_sample_rate,
    int voice_num
);
void v_osc_note_on_sync_phases_hard(t_osc_simple_unison * a_osc_ptr);
void v_osc_set_simple_osc_unison_type_v2(
    t_osc_simple_unison * a_osc_ptr,
    int a_index
);
void f_osc_run_unison_osc_core_only(t_osc_simple_unison * a_osc_ptr);
SGFLT f_osc_run_unison_osc_sync(t_osc_simple_unison * a_osc_ptr);

#endif /* OSC_SIMPLE_H */

