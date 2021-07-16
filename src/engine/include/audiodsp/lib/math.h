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

#ifndef LMS_MATH_H
#define LMS_MATH_H

#include "audiodsp/lib/interpolate-linear.h"
#include "compiler.h"

/* SGFLT f_sg_abs(SGFLT a_input)
 *
 * Return the absolute value of a SGFLT.  Use this instead of fabs from
 * math.h, it's much faster
 */
SGFLT f_sg_abs(SGFLT);
/* SGFLT f_sg_max(SGFLT a_1,SGFLT a_2)
 *
 * Return the larger of 2 SGFLTs
 */
SGFLT f_sg_max(SGFLT,SGFLT);
/* SGFLT f_sg_max(SGFLT a_1,SGFLT a_2)
 *
 * Return the lesser of 2 SGFLTs
 */
SGFLT f_sg_min(SGFLT,SGFLT);
/* SGFLT f_sg_floor(SGFLT a_input, SGFLT a_floor)
 *
 * Clips a value if less than a_floor
 */
SGFLT f_sg_floor(SGFLT,SGFLT);
/* SGFLT f_sg_ceiling(SGFLT a_input, SGFLT a_ceiling)
 *
 * Clips a value if more than a_ceiling
 */
SGFLT f_sg_ceiling(SGFLT,SGFLT);
/* SGFLT f_sg_sqrt(SGFLT a_input)
 *
 * Calculate a square root using a fast table-based lookup.
 * The range is zero to 4
 */
SGFLT f_sg_sqrt(SGFLT);

#define arr_sqrt_count 401
//SGFLT arr_sqrt [arr_sqrt_count];

#endif /* LMS_MATH_H */

