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

#ifndef ENV_FOLLOWER_H
#define ENV_FOLLOWER_H

//#define ENF_DEBUG_MODE

#include "audiodsp/modules/filter/one_pole.h"
#include "audiodsp/lib/amp.h"
#include "compiler.h"

typedef struct st_enf_env_follower
{
    SGFLT input;
    SGFLT output_smoothed;
    t_opl_one_pole * smoother;
#ifdef ENF_DEBUG_MODE
    int debug_counter;
#endif
}t_enf_env_follower;

t_enf_env_follower* g_enf_get_env_follower(SGFLT);
void env_follower_init(t_enf_env_follower*, SGFLT);
void v_enf_run_env_follower(t_enf_env_follower*, SGFLT);

#endif /* ENV_FOLLOWER_H */

