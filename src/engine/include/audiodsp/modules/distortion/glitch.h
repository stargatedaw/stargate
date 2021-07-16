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

#ifndef GLITCH_H
#define GLITCH_H

#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

typedef struct
{
    SGFLT * buffer;
    int buffer_size, buffer_ptr;
    SGFLT last_pitch, last_repeat, last_wet;
    int sample_count, repeat_count, is_repeating, current_repeat_count;
    SGFLT sr, sample_tmp;
    SGFLT output0, output1;
    t_audio_xfade xfade;
}t_glc_glitch;

t_glc_glitch * g_glc_glitch_get(SGFLT);
void v_glc_glitch_set(t_glc_glitch*, SGFLT, SGFLT, SGFLT);
void v_glc_glitch_run(t_glc_glitch*, SGFLT, SGFLT);
void v_glc_glitch_free(t_glc_glitch*);
void g_glc_init(t_glc_glitch * f_result, SGFLT a_sr);
void v_glc_glitch_retrigger(t_glc_glitch* a_glc);

#endif /* GLITCH_H */

