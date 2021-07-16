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

#ifndef VOCODER_H
#define VOCODER_H

#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/modulation/env_follower2.h"
#include "compiler.h"


#define VOCODER_BAND_COUNT 64
#define VOCODER_BAND_COUNT_M1 (VOCODER_BAND_COUNT - 1)

typedef struct
{
    t_state_variable_filter m_filter;
    t_enf2_env_follower env_follower;
    t_svf2_filter c_filter;
}t_vdr_band;

typedef struct
{
    SGFLT output0, output1;
    t_vdr_band bands[VOCODER_BAND_COUNT];
    t_vdr_band low_band;
    t_vdr_band high_band;
}t_vdr_vocoder;


void g_vdr_band_init(
    t_vdr_band * self,
    SGFLT a_sr,
    SGFLT a_pitch,
    SGFLT a_res
);

void g_vdr_init(t_vdr_vocoder * self, SGFLT a_sr);

void v_vdr_run(
    t_vdr_vocoder * self,
    SGFLT a_mod_in0,
    SGFLT a_mod_in1,
    SGFLT a_input0,
    SGFLT a_input1
);

#endif /* VOCODER_H */

