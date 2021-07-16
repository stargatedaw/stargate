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

#ifndef INTERPOLATE_LINEAR_H
#define INTERPOLATE_LINEAR_H

#include "lmalloc.h"
#include "compiler.h"

/* SGFLT f_linear_interpolate(
 * SGFLT a_a, //item 0
 * SGFLT a_b, //item 1
 * SGFLT a_position)  //position between the 2, range:  0 to 1
 */
SGFLT f_linear_interpolate(SGFLT, SGFLT, SGFLT);
/* SGFLT f_linear_interpolate_ptr_wrap(
 * SGFLT * a_table,
 * int a_table_size,
 * SGFLT a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the SGFLT* must be malloc'd
 * to (sizeof(SGFLT) * a_table_size)
 */
SGFLT f_linear_interpolate_ptr_wrap(SGFLT*, int, SGFLT);
SGFLT f_linear_interpolate_ptr(SGFLT*, SGFLT);
// For use with the read_head type in Sampler1 Sampler
SGFLT f_linear_interpolate_ptr_ifh(
    SGFLT * a_table,
    int a_whole_number,
    SGFLT a_frac
);

#endif /* INTERPOLATE_LINEAR_H */

