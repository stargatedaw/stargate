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

#ifndef GLITCH_V2_H
#define GLITCH_V2_H

#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/modulation/adsr.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"

typedef struct
{
    SGFLT * buffer;
    SGFLT read_head;
    int buffer_size, read_head_int, write_head, first_run;
    SGFLT last_time, last_pitch;
    int sample_count;
    SGFLT sr, sample_count_f;
    SGFLT rate;
    SGFLT output0, output1;
    t_pit_ratio pitch_ratio;
    t_audio_xfade xfade;
    t_adsr adsr;
}t_glc_glitch_v2;

void g_glc_glitch_v2_init(t_glc_glitch_v2*, SGFLT);
void v_glc_glitch_v2_set(t_glc_glitch_v2*, SGFLT, SGFLT);
void v_glc_glitch_v2_run(t_glc_glitch_v2*, SGFLT, SGFLT);
void v_glc_glitch_v2_retrigger(t_glc_glitch_v2* a_glc);
void v_glc_glitch_v2_release(t_glc_glitch_v2* a_glc);

#endif /* GLITCH_V2_H */

