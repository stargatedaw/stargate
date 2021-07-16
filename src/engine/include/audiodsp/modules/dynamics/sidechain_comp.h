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

#ifndef SIDECHAIN_COMP_H
#define SIDECHAIN_COMP_H

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/lib/peak_meter.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower2.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"

typedef struct
{
    SGFLT pitch, ratio, thresh, wet, attack, release;
    t_state_variable_filter filter;
    SGFLT output0, output1;
    t_enf2_env_follower env_follower;
    t_audio_xfade xfade;
    t_pkm_redux peak_tracker;
}t_scc_sidechain_comp;

void g_scc_init(t_scc_sidechain_comp * self, SGFLT a_sr);
void v_scc_set(
    t_scc_sidechain_comp *self,
    SGFLT a_thresh,
    SGFLT a_ratio,
    SGFLT a_attack,
    SGFLT a_release,
    SGFLT a_wet
);
void v_scc_run_comp(
    t_scc_sidechain_comp* self,
    SGFLT a_input0,
    SGFLT a_input1,
    SGFLT a_output0,
    SGFLT a_output1
);
#endif /* SIDECHAIN_COMP_H */

