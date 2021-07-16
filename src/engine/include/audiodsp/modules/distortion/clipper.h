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

#ifndef CLIPPER_H
#define CLIPPER_H

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

//#define CLP_DEBUG_MODE

typedef struct st_clipper
{
    SGFLT clip_high, clip_low, input_gain_linear, clip_db, in_db, result;
#ifdef CLP_DEBUG_MODE
    int debug_counter;
#endif
}t_clipper;

/*Set the values of a clipper struct symmetrically,
 * ie: value of .75 clips at .75 and -.75*/
void v_clp_set_clip_sym(t_clipper *, SGFLT);
void v_clp_set_in_gain(t_clipper *, SGFLT);
t_clipper * g_clp_get_clipper();
void v_clp_free(t_clipper *);
/* SGFLT f_clp_clip(
 * t_clipper *,
 * SGFLT a_input  //value to be clipped
 * )
 *
 * This function performs the actual clipping, and returns a SGFLT
 */
SGFLT f_clp_clip(t_clipper*, SGFLT);
void g_clp_init(t_clipper * f_result);

#endif /* CLIPPER_H */

