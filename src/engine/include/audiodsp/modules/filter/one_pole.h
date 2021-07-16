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

#ifndef ONE_POLE_H
#define ONE_POLE_H

//#define OPL_DEBUG_MODE

#include "audiodsp/constants.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/pitch_core.h"
#include "compiler.h"


typedef struct st_opl_one_pole
{
    SGFLT a0, a1, b1, x;
    SGFLT output;
    SGFLT cutoff;
    SGFLT sample_rate;
    SGFLT sr_recip;
    SGFLT hp;

#ifdef OPL_DEBUG_MODE
    int debug_counter;
#endif
}t_opl_one_pole;

void v_opl_set_coeff(t_opl_one_pole*, SGFLT);
void v_opl_set_coeff_slow(t_opl_one_pole*, SGFLT);
void v_opl_set_coeff_hz(t_opl_one_pole*, SGFLT);
void v_opl_run(t_opl_one_pole*, SGFLT);
t_opl_one_pole * g_opl_get_one_pole(SGFLT);

#endif /* ONE_POLE_H */

