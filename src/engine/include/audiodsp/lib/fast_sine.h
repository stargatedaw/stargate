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

#ifndef FAST_SINE_H
#define FAST_SINE_H


#include "interpolate-linear.h"
#include "audiodsp/constants.h"
#include "compiler.h"

SGFLT f_sine_fast_run(SGFLT);
/* SGFLT f_sine_fast_run(SGFLT a_osc_core)
 *
 * Accepts zero to one input.
 */
SGFLT f_sine_fast_run_radians(SGFLT);
SGFLT f_cosine_fast_run(SGFLT);
SGFLT f_cosine_fast_run_radians(SGFLT);

#define ARR_SINE_COUNT 802
#define ARR_SINE_COUNT_RADIANS (ARR_SINE_COUNT / PI2)
#define ARR_COSINE_PHASE_RADIANS (PI* 0.25f)

//SGFLT ARR_SINE[ARR_SINE_COUNT];

#endif /* FAST_SINE_H */

