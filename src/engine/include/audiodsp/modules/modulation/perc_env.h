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

#ifndef KICK_ENV_H
#define KICK_ENV_H

#define KICK_ENV_SECTIONS 2

#include "compiler.h"

typedef struct
{
    int sample_counts[KICK_ENV_SECTIONS];
    SGFLT incs[KICK_ENV_SECTIONS];
    int current_env;
    SGFLT sample_rate;
    SGFLT value;
    int counter;
}t_pnv_perc_env;

t_pnv_perc_env * g_pnv_get(SGFLT);
void v_pnv_set(t_pnv_perc_env*, SGFLT, SGFLT, SGFLT, SGFLT, SGFLT);
SGFLT f_pnv_run(t_pnv_perc_env*);
void g_pnv_init(t_pnv_perc_env * f_result, SGFLT a_sr);

#endif /* KICK_ENV_H */

