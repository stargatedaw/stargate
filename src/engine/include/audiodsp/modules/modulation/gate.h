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

#ifndef GATE_H
#define GATE_H

#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"

typedef struct
{
    t_state_variable_filter svf;
    t_audio_xfade xfade;
    SGFLT last_cutoff;
    SGFLT last_wet;
    SGFLT output[2];
    SGFLT value;
}t_gat_gate;

t_gat_gate * g_gat_get(SGFLT);
void v_gat_set(t_gat_gate*, SGFLT, SGFLT);
void v_gat_run(t_gat_gate*, SGFLT, SGFLT, SGFLT);
void g_gat_init(t_gat_gate * f_result, SGFLT a_sr);

#endif /* GATE_H */

