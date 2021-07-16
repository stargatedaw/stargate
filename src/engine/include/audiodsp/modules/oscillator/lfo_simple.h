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

#ifndef LFO_SIMPLE_H
#define LFO_SIMPLE_H

#include "osc_simple.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/osc_core.h"
#include "compiler.h"

typedef struct st_lfs_lfo
{
    SGFLT inc, sr, sr_recip, output;
    t_osc_core osc_core;
    fp_get_osc_func_ptr osc_ptr;
}t_lfs_lfo;

/* void v_lfs_sync(
 * t_lfs_lfo * a_lfs,
 * SGFLT a_phase,  //the phase to resync to.  Range:  0 to .9999
 * int a_type)  //The type of LFO.  See types below
 *
 * Types:
 * 0 : Off
 * 1 : Sine
 * 2 : Triangle
 */
void v_lfs_sync(t_lfs_lfo *,SGFLT,int);
/* void v_osc_set_hz(
 * t_lfs_lfo * a_lfs_ptr,
 * SGFLT a_hz)  //the pitch of the oscillator in hz, typically 0.1 to 10000
 *
 * For setting LFO frequency.
 */
void v_lfs_set(t_lfs_lfo *, SGFLT);
/* void v_lfs_run(t_lfs_lfo *)
 */
void v_lfs_run(t_lfs_lfo *);
t_lfs_lfo * g_lfs_get(SGFLT);
void v_lfs_free(t_lfs_lfo * );
void g_lfs_init(t_lfs_lfo * f_result, SGFLT a_sr);

#endif /* LFO_SIMPLE_H */

