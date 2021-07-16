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

#ifndef WAVETABLES_H
#define WAVETABLES_H

#include <pthread.h>

#include "compiler.h"

#define plain_saw_count 1200
//SGFLT plain_saw_array[plain_saw_count];

#define superbsaw_count 1200
//SGFLT superbsaw_array[superbsaw_count];

#define viralsaw_count 1200
//SGFLT viralsaw_array[viralsaw_count];

#define soft_saw_count 1200
//SGFLT soft_saw_array[soft_saw_count];

#define mid_saw_count 1200
//SGFLT mid_saw_array[mid_saw_count];

#define lush_saw_count 1200
//SGFLT lush_saw_array[lush_saw_count];

#define evil_square_count 1200
//SGFLT evil_square_array[evil_square_count];

#define punchy_square_count 1200
//SGFLT punchy_square_array[punchy_square_count];

#define soft_square_count 1200
//SGFLT soft_square_array[soft_square_count];

#define pink_glitch_count 1200
//SGFLT pink_glitch_array[pink_glitch_count];

#define white_glitch_count 1200
//SGFLT white_glitch_array[white_glitch_count];

#define acid_count 1200
//SGFLT acid_array[acid_count];

#define screetch_count 1200
//SGFLT screetch_array[screetch_count];

#define thick_bass_count 1200
//SGFLT thick_bass_array[thick_bass_count];

#define rattler_count 1200
//SGFLT rattler_array[rattler_count];

#define deep_saw_count 1200
//SGFLT deep_saw_array[deep_saw_count];

#define sine_count 1200
//SGFLT sine_array[sine_count];

//17 + 3 for the additive osc
#define WT_TOTAL_WAVETABLE_COUNT 20
#define WT_HZ 40.0f
#define WT_FRAMES_PER_CYCLE 1200
#define WT_SR 48000.0f
//#define WT_HZ_RECIP (1.0f/WT_HZ)

typedef struct st_wavetable
{
    int length;
    SGFLT * wavetable;
}t_wavetable;

t_wavetable * g_wavetable_get();

typedef struct
{
    t_wavetable ** tables;
    int f_count;
}t_wt_wavetables;

void v_wt_set_wavetable(
    t_wt_wavetables* a_wt,
    int a_index,
    SGFLT * a_arr,
    int a_count,
    pthread_spinlock_t* a_spinlock,
    int* a_reset_var
);

t_wt_wavetables* g_wt_wavetables_get();

#endif /* WAVETABLES_H */

