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

#ifndef REVERB_H
#define REVERB_H

#define REVERB_DIFFUSER_COUNT 5
#define REVERB_TAP_COUNT 12


#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/filter/comb_filter.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "compiler.h"

typedef struct {
    t_comb_filter tap;
    SGFLT pitch;
}t_rvb_tap;

typedef struct {
    t_state_variable_filter diffuser;
    SGFLT pitch;
}t_rvb_diffuser;

typedef struct {
    SGFLT output[2];
    SGFLT feedback;
    t_lfs_lfo lfo;
    t_state_variable_filter lp;
    t_state_variable_filter hp;
    SGFLT wet_linear;
    t_rvb_tap taps[REVERB_TAP_COUNT];
    t_rvb_diffuser diffusers[REVERB_DIFFUSER_COUNT];
    SGFLT* predelay_buffer[2];
    int predelay_counter;
    int predelay_size;
    SGFLT color;
    SGFLT wet;
    SGFLT time;
    SGFLT volume_factor;
    SGFLT last_predelay;
    SGFLT sr;
    SGFLT hp_cutoff;
} t_rvb_reverb;

void v_rvb_reverb_set(t_rvb_reverb*, SGFLT, SGFLT, SGFLT, SGFLT, SGFLT);
void v_rvb_reverb_run(t_rvb_reverb*, SGFLT, SGFLT);
void v_rvb_panic(t_rvb_reverb* self);
void g_rvb_reverb_init(t_rvb_reverb* f_result, SGFLT a_sr);
void g_rvb_reverb_init_buffer(
    t_rvb_reverb* f_result,
    SGFLT a_sr,
    SGFLT** buffer
);

#endif /* REVERB_H */

