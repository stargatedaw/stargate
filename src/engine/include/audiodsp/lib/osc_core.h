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

#ifndef OSC_CORE_H
#define OSC_CORE_H

#include <stdlib.h>

#include "compiler.h"
#include "pitch_core.h"

#define OSC_UNISON_MAX_VOICES 7

extern SGFLT OSC_CORE_PHASES[32][OSC_UNISON_MAX_VOICES];

typedef struct {
    SGFLT output;   //range:  0 to 1
}t_osc_core;


/* void v_run_osc(
 * t_osc_core *a_core,
 * SGFLT a_inc) //The increment to run the oscillator by.
 * The oscillator will increment until it reaches 1,
 * then resets to (value - 1), for each oscillation
 */
void v_run_osc(t_osc_core *, SGFLT);
void v_osc_core_free(t_osc_core *);
void g_init_osc_core(t_osc_core * f_result);
int v_run_osc_sync(t_osc_core *a_core, SGFLT a_inc);

#endif /* OSC_CORE_H */

