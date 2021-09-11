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

#ifndef PEAK_METER_H
#define PEAK_METER_H

#define PEAK_STEP_SIZE 4

#include "lmalloc.h"
#include "compiler.h"

// a peak meter
typedef struct
{
    volatile SGFLT value[2];
    int buffer_pos;
    volatile int dirty;
}t_pkm_peak_meter;

// a gain reduction meter
typedef struct
{
    SGFLT gain_redux;
    int counter;
    int count;
    int dirty;
}t_pkm_redux;

void g_pkm_redux_init(t_pkm_redux * self, SGFLT a_sr);
void v_pkm_redux_lin_reset(t_pkm_redux * self);
void v_pkm_redux_run(t_pkm_redux * self, SGFLT a_gain);
void g_pkm_init(t_pkm_peak_meter * f_result);
t_pkm_peak_meter * g_pkm_get();
SGFLT f_pkm_compare(SGFLT a_audio, SGFLT a_peak);
/* For the host to call after reading the peak value
 */
void v_pkm_reset(t_pkm_peak_meter * self);
void v_pkm_run(
    t_pkm_peak_meter * self,
    SGFLT * a_in0,
    SGFLT * a_in1,
    int a_count
);

void v_pkm_run_single(
    t_pkm_peak_meter * self,
    SGFLT a_in0,
    SGFLT a_in1
);
#endif /* PEAK_METER_H */

