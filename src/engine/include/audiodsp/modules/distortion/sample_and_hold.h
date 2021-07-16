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
#ifndef SAMPLE_AND_HOLD_H
#define SAMPLE_AND_HOLD_H

#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"


typedef struct
{
    SGFLT output0, output1, hold0, hold1;
    int hold_count, hold_counter;
    SGFLT last_pitch, last_wet, sr;
    t_audio_xfade xfade;
} t_sah_sample_and_hold;

t_sah_sample_and_hold * g_sah_sample_and_hold_get(SGFLT);
void v_sah_sample_and_hold_set(t_sah_sample_and_hold*, SGFLT, SGFLT);
void v_sah_sample_and_hold_run(t_sah_sample_and_hold*, SGFLT, SGFLT);
void v_sah_free(t_sah_sample_and_hold*);
void g_sah_init(t_sah_sample_and_hold * f_result, SGFLT a_sr);

#endif /* SAMPLE_AND_HOLD_H */

