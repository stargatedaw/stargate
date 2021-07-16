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

#ifndef COMPRESSOR_H
#define COMPRESSOR_H

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/peak_meter.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower2.h"
#include "compiler.h"

typedef struct
{
    SGFLT thresh, ratio, ratio_recip, knee, knee_thresh, gain, gain_lin;
    t_state_variable_filter filter;
    SGFLT output0, output1;
    SGFLT rms_time, rms_last, rms_sum, rms_count_recip, sr;
    int rms_counter, rms_count;
    t_enf2_env_follower env_follower;
    t_pkm_redux peak_tracker;
}t_cmp_compressor;


void g_cmp_init(t_cmp_compressor * self, SGFLT a_sr);
void v_cmp_set(
    t_cmp_compressor * self,
    SGFLT thresh,
    SGFLT ratio,
    SGFLT knee,
    SGFLT attack,
    SGFLT release,
    SGFLT gain
);
void v_cmp_run(
    t_cmp_compressor * self,
    SGFLT a_in0,
    SGFLT a_in1
);
void v_cmp_set_rms(
    t_cmp_compressor * self,
    SGFLT rms_time
);

void v_cmp_run_rms(
    t_cmp_compressor * self,
    SGFLT a_in0,
    SGFLT a_in1
);

#endif /* COMPRESSOR_H */

