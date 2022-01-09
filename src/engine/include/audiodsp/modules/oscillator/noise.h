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

#ifndef NOISE_H
#define NOISE_H

#include <stdlib.h>
#include <time.h>

#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"


typedef struct {
    int array_count, read_head;
    SGFLT * sample_array;
    SGFLT b0,b1,b2,b3,b4,b5,b6;  //pink noise coefficients
} t_white_noise;

typedef SGFLT (*fp_noise_func_ptr)(t_white_noise*);
typedef struct SamplePair (*fp_noise_stereo)(t_white_noise*);

/* SGFLT f_run_white_noise(t_white_noise * a_w_noise)
 *
 * returns a single sample of white noise
 */
SGFLT f_run_white_noise(t_white_noise *);
/* SGFLT f_run_pink_noise(t_white_noise * a_w_noise)
 *
 * returns a single sample of pink noise
 */
SGFLT f_run_pink_noise(t_white_noise *);
SGFLT f_run_noise_off(t_white_noise *);
fp_noise_func_ptr fp_get_noise_func_ptr(int);
fp_noise_stereo fp_noise_stereo_get(int);

//fp_noise_func_ptr f_noise_func_ptr_arr[];
void g_white_noise_init(t_white_noise * f_result, SGFLT a_sample_rate);

struct SamplePair noise_off_stereo_run(t_white_noise*);
struct SamplePair white_noise_mono_run(t_white_noise*);
struct SamplePair pink_noise_mono_run(t_white_noise*);
struct SamplePair white_noise_stereo_run(t_white_noise*);
struct SamplePair pink_noise_stereo_run(t_white_noise*);

#endif /* NOISE_H */

