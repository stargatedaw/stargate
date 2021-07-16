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

#ifndef PEAK_EQ_H
#define PEAK_EQ_H

#include <math.h>

#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"


typedef struct
{
    SGFLT BW, dB, pitch, exp_value, exp_db, d, B, d_times_B,
            w, w2, wQ, y2_0, y2_1, FIR_out_0, FIR_out_1, w2p1,
            coeff0, coeff1, coeff2, pi_div_sr;
    SGFLT input0, input1, in0_m1, in0_m2, in1_m1, in1_m2;
    SGFLT output0, output1, out0_m1, out0_m2, out1_m1, out1_m2;
    SGFLT warp_input, warp_input_squared, warp_input_tripled,
            warp_outstream0, warp_outstream1, warp_output;

    SGFLT coeff1_x_out_m1_0, coeff2_x_out_m2_0, iir_output0,
            coeff1_x_out_m1_1, coeff2_x_out_m2_1, iir_output1;

    SGFLT last_pitch;
}t_pkq_peak_eq;


void v_pkq_calc_coeffs(t_pkq_peak_eq*, SGFLT, SGFLT, SGFLT);
void v_pkq_run(t_pkq_peak_eq*, SGFLT, SGFLT);
void v_pkq_free(t_pkq_peak_eq*);

void g_pkq_init(t_pkq_peak_eq * f_result, SGFLT a_sample_rate);

typedef struct
{
    t_pkq_peak_eq eqs[6];
    SGFLT * knobs[6][3];  //freq, bw, gain
    SGFLT output0;
    SGFLT output1;
}t_eq6;

void g_eq6_init(t_eq6 * f_result, SGFLT a_sr);
void v_eq6_connect_port(t_eq6 * a_eq6, int a_port, SGFLT * a_ptr);
void v_eq6_set(t_eq6* a_eq6);
void v_eq6_run(t_eq6 *a_eq6, SGFLT a_input0, SGFLT a_input1);

#endif /* PEAK_EQ_H */

