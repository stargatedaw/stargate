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

#ifndef FFTW_LOCK_H
#define FFTW_LOCK_H

#include <pthread.h>
#include <fftw3.h>

#include "compiler.h"

extern pthread_mutex_t FFTW_LOCK;
extern int FFTW_LOCK_INIT;

#ifdef SG_USE_DOUBLE
fftw_plan g_fftw_plan_dft_r2c_1d(
    int a_size,
    SGFLT * a_in,
    fftw_complex * a_out,
    unsigned a_flags
);
#else
fftwf_plan g_fftw_plan_dft_r2c_1d(
    int a_size,
    SGFLT * a_in,
    fftwf_complex * a_out,
    unsigned a_flags
);
#endif

#endif /* FFTW_LOCK_H */

