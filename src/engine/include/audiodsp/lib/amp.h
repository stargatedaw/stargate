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

#ifndef AMP_H
#define AMP_H

#include <math.h>

#include "interpolate-linear.h"
#include "lmalloc.h"
#include "compiler.h"

SGFLT f_db_to_linear(SGFLT);
SGFLT f_linear_to_db(SGFLT);
/* SGFLT f_db_to_linear_fast(SGFLT a_db)
 *
 * Convert decibels to linear using an approximated table lookup
 *
 * Input range:  -100 to 36
 *
 * Use the regular version if you may require more range, otherwise the values
 * will be clipped
 */
SGFLT f_db_to_linear_fast(SGFLT);
/* SGFLT f_linear_to_db_fast(
 * SGFLT a_input  //Linear amplitude.  Typically 0 to 1
 * )
 *
 * A fast, table-lookup based linear to decibels converter.
 * The range is 0 to 4, above 4 will clip at 4.
 */
SGFLT f_linear_to_db_fast(SGFLT);
/* SGFLT f_linear_to_db_linear(SGFLT a_input)
 *
 * This takes a 0 to 1 signal and approximates it to a useful range with a logarithmic decibel curve
 * Typical use would be on an envelope that controls the amplitude of an audio signal
 */
SGFLT f_linear_to_db_linear(SGFLT);

/*Arrays*/

#define arr_amp_db2a_count 545
#define arr_amp_db2a_count_m1_f 544.0f

extern SG_THREAD_LOCAL SGFLT arr_amp_db2a[arr_amp_db2a_count];

#define arr_amp_a2db_count 400
#define arr_amp_a2db_count_SGFLT 400.0f
#define arr_amp_a2db_count_SGFLT_m1 399.0f

extern SG_THREAD_LOCAL SGFLT arr_amp_a2db[arr_amp_a2db_count];

#endif /* AMP_H */

