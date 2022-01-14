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

#ifndef LIMITER_H
#define LIMITER_H

#include <math.h>
#include <assert.h>

#include "audiodsp/lib/math.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/lib/peak_meter.h"
#include "compiler.h"

#define SG_HOLD_TIME_DIVISOR 500.0f

typedef struct st_lim_limiter
{
    int holdtime, r1Timer, r2Timer;
    SGFLT output0, output1;
    SGFLT sr, sr_recip;
    SGFLT thresh, ceiling, volume, release, r;
    SGFLT maxSpls, max1Block, max2Block, envT, env, gain;
    SGFLT last_thresh, last_ceiling, last_release;
    SGFLT autogain;
    SGFLT *buffer0, *buffer1;
    int buffer_size, buffer_index, buffer_read_index;
    t_state_variable_filter filter;
    t_pkm_redux peak_tracker;
}t_lim_limiter;

void v_lim_set(t_lim_limiter*,SGFLT, SGFLT, SGFLT);
void v_lim_run(t_lim_limiter*,SGFLT, SGFLT);
void v_lim_free(t_lim_limiter*);
void g_lim_init(t_lim_limiter * f_result, SGFLT a_sr, int a_huge_pages);

#endif /* LIMITER_H */

