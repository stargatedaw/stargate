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

#ifndef DELAY_H
#define DELAY_H

#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

typedef struct {
    int read_head;
    int read_head_p1;
    SGFLT fraction;
    int delay_samples;
    SGFLT delay_seconds;
    SGFLT delay_beats;
    SGFLT delay_pitch;
    SGFLT delay_hz;
    SGFLT output;
} t_delay_tap;

typedef struct {
    int write_head;
    SGFLT sample_rate;
    SGFLT tempo;
    SGFLT tempo_recip;
    int sample_count;
    SGFLT* buffer;
} t_delay_simple;


t_delay_simple * g_dly_get_delay(SGFLT, SGFLT);
void g_dly_init(t_delay_simple * f_result, SGFLT a_max_size, SGFLT a_sr);
void g_dly_init_buffer(
    t_delay_simple* f_result,
    SGFLT a_sr,
    SGFLT* buffer,
    int sample_count
);
t_delay_tap * g_dly_get_tap();
void v_dly_set_delay_seconds(t_delay_simple*,t_delay_tap*,SGFLT);
void v_dly_set_delay_lin(t_delay_simple*,t_delay_tap*,SGFLT);
void v_dly_set_delay_tempo(t_delay_simple*,t_delay_tap*,SGFLT);
void v_dly_set_delay_pitch(t_delay_simple*,t_delay_tap*,SGFLT);
void v_dly_set_delay_pitch_fast(t_delay_simple*,t_delay_tap*,SGFLT);
void v_dly_set_delay_hz(t_delay_simple*,t_delay_tap*,SGFLT);
void v_dly_run_delay(t_delay_simple*,SGFLT);
void v_dly_run_tap(t_delay_simple*,t_delay_tap*);
void v_dly_run_tap_lin(t_delay_simple*,t_delay_tap*);
void g_dly_tap_init(t_delay_tap * f_result);
#endif /* DELAY_H */

