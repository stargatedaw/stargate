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

#ifndef ENF_ENV_FOLLOWER_H
#define ENF_ENV_FOLLOWER_H

#include <math.h>

#include "audiodsp/lib/math.h"
#include "compiler.h"

typedef struct
{
    SGFLT attack;
    SGFLT release;
    SGFLT a_coeff;
    SGFLT r_coeff;
    SGFLT envelope;
    SGFLT sample_rate;
}t_enf2_env_follower;

void g_enf_init(t_enf2_env_follower* self, SGFLT a_sr);
void v_enf_set(t_enf2_env_follower* self, SGFLT a_attack, SGFLT a_release);
void v_enf_run(t_enf2_env_follower* self, SGFLT a_input);

#endif /* ENF_ENV_FOLLOWER_H */

