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

#ifndef SATURATOR_H
#define SATURATOR_H

#include <math.h>

#include "audiodsp/lib/math.h"
#include "compiler.h"


typedef struct st_sat_saturator
{
    SGFLT output0;
    SGFLT output1;
    SGFLT a;
    SGFLT b;
    SGFLT amount;
    SGFLT last_ingain;
    SGFLT last_outgain;
    SGFLT ingain_lin;
    SGFLT outgain_lin;
}t_sat_saturator;

t_sat_saturator * g_sat_get();
void v_sat_set(t_sat_saturator*,SGFLT,SGFLT,SGFLT);
void v_sat_run(t_sat_saturator*,SGFLT,SGFLT);
void v_sat_free(t_sat_saturator*);
void g_sat_init(t_sat_saturator * f_result);

#endif /* SATURATOR_H */

