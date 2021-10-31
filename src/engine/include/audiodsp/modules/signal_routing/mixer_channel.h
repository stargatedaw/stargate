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

#ifndef MIXER_CHANNEL_H
#define MIXER_CHANNEL_H

#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "compiler.h"

typedef struct st_mxc_mixer_channel{
    SGFLT amp_linear;
    t_smoother_linear amp_smoother;
    SGFLT gain_db;
    SGFLT gain_linear;
    SGFLT main_gain0;
    SGFLT main_gain1;
    t_smoother_linear pan_smoother;
    SGFLT pan0;
    SGFLT pan1;
    SGFLT pan_law_gain_linear;
    SGFLT in0, in1;
    SGFLT out0, out1;
}t_mxc_mixer_channel;

t_mxc_mixer_channel * g_mxc_get(SGFLT a_sr);
void v_mxc_mix_stereo_to_stereo(
    t_mxc_mixer_channel*,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT
);
void v_mxc_mix_stereo_to_mono(
    t_mxc_mixer_channel*,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT
);
void v_mxc_run_smoothers(t_mxc_mixer_channel*, SGFLT, SGFLT, SGFLT);

#endif /* MIXER_CHANNEL_H */

