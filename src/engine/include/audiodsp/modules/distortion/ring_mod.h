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

#ifndef RING_MOD_H
#define RING_MOD_H

#include "audiodsp/modules/oscillator/osc_simple.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

typedef struct
{
    SGFLT pitch;
    SGFLT last_wet;
    SGFLT output0, output1;
    t_osc_simple_unison osc;
    SGFLT osc_output;
    t_audio_xfade xfade;
}t_rmd_ring_mod;

t_rmd_ring_mod * g_rmd_ring_mod_get(SGFLT);
void v_rmd_ring_mod_set(t_rmd_ring_mod*, SGFLT, SGFLT);
void v_rmd_ring_mod_run(t_rmd_ring_mod*, SGFLT, SGFLT);
void g_rmd_init(t_rmd_ring_mod * f_result, SGFLT a_sr);

#endif /* RING_MOD_H */

