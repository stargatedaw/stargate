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

#ifndef SPECTRUM_ANALYZER_H
#define SPECTRUM_ANALYZER_H

#include <complex.h>
#include <fftw3.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "lmalloc.h"
#include "fftw_lock.h"
#include "compiler.h"

typedef struct {
    int plugin_uid;
    SGFLT * buffer;
    int buf_pos;
#ifdef SG_USE_DOUBLE
    fftw_complex *output;
    fftw_plan plan;
#else
    fftwf_complex *output;
    fftwf_plan plan;
#endif
    int height, width;
    int samples_count;
    int samples_count_div2;
    SGFLT *samples;
    char * str_buf;
    char str_tmp[128];
} t_spa_spectrum_analyzer;

t_spa_spectrum_analyzer * g_spa_spectrum_analyzer_get(
    int a_sample_count,
    int a_plugin_uid
);

void v_spa_compute_fft(t_spa_spectrum_analyzer *a_spa);

// Run for a single sample
void v_spa_run(
    t_spa_spectrum_analyzer *a_spa,
    SGFLT sample
);

//void g_spa_free(t_spa_spectrum_analyzer *a_spa){;

#endif /* SPECTRUM_ANALYZER_H */

