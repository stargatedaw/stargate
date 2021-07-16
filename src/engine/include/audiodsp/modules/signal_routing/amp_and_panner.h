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

#ifndef AMP_AND_PANNER_H
#define AMP_AND_PANNER_H

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

typedef struct st_amp_and_panner
{
    SGFLT amp_db;
    SGFLT amp_linear;
    SGFLT pan; //0 to 1
    SGFLT amp_linear0;
    SGFLT amp_linear1;
    SGFLT output0;
    SGFLT output1;
}t_amp_and_panner;

void v_app_set(t_amp_and_panner*,SGFLT,SGFLT);
void v_app_run(t_amp_and_panner*,SGFLT,SGFLT);
t_amp_and_panner * g_app_get();

void v_app_run_monofier(t_amp_and_panner* a_app, SGFLT a_in0, SGFLT a_in1);
void g_app_init(t_amp_and_panner * f_result);
void v_app_free(t_amp_and_panner * a_app);

#endif /* AMP_AND_PANNER_H */

