#include <math.h>

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/filter/peak_eq.h"


void v_pkq_free(t_pkq_peak_eq * a_pkq){
    free(a_pkq);
}

/* void v_pkq_calc_coeffs(
 * t_pkq_peak_eq *a_pkq,
 * SGFLT a_pitch,
 * SGFLT a_bw,
 * SGFLT a_db)
 */
void v_pkq_calc_coeffs(
    t_pkq_peak_eq * a_pkq,
    SGFLT a_pitch,
    SGFLT a_bw,
    SGFLT a_db
){
    if((a_db != (a_pkq->dB)) || (a_bw != (a_pkq->BW))){
        a_pkq->BW = a_bw;
        a_pkq->dB = a_db;
        a_pkq->exp_value = exp((a_pkq->BW)*log(1.421f));
        a_pkq->exp_db = exp((a_pkq->dB)*log(1.061f));

        a_pkq->d = (((a_pkq->exp_value) * (a_pkq->exp_value)) - 1.0f) /
                ((a_pkq->exp_value) * (a_pkq->exp_db));

        a_pkq->B = ((a_pkq->exp_db) * (a_pkq->exp_db)) - 1.0f;

        a_pkq->d_times_B = (a_pkq->d) * (a_pkq->B);
    }

    if(a_pitch != a_pkq->last_pitch){
        a_pkq->last_pitch = a_pitch;
        a_pkq->warp_input =
            f_pit_midi_note_to_hz_fast(a_pitch) * (a_pkq->pi_div_sr);
        a_pkq->warp_input_squared = (a_pkq->warp_input) * (a_pkq->warp_input);
        a_pkq->warp_input_tripled =
                (a_pkq->warp_input_squared) * (a_pkq->warp_input);
        a_pkq->warp_outstream0 = (a_pkq->warp_input_squared) *
                (a_pkq->warp_input_tripled) * 0.133333f;
        a_pkq->warp_outstream1 = (a_pkq->warp_input_tripled) * 0.333333f;
        a_pkq->w = (a_pkq->warp_outstream0) + (a_pkq->warp_outstream1) +
                (a_pkq->warp_input);
    }


    a_pkq->w2 = (a_pkq->w) * (a_pkq->w);
    a_pkq->wQ = (a_pkq->w) * (a_pkq->d);


    a_pkq->w2p1 = (a_pkq->w2) + 1.0f;
    a_pkq->coeff0 = 1.0f / ((a_pkq->w2p1) + (a_pkq->wQ));
    a_pkq->coeff1 = ((a_pkq->w2) - 1.0f) * 2.0f;
    a_pkq->coeff2 = (a_pkq->w2p1) - (a_pkq->wQ);
}

void v_pkq_run(t_pkq_peak_eq * a_pkq,SGFLT a_in0, SGFLT a_in1)
{
    a_pkq->in0_m2 = (a_pkq->in0_m1);
    a_pkq->in0_m1 = a_in0;

    a_pkq->y2_0 = a_pkq->in0_m2;
    a_pkq->FIR_out_0 = (a_in0 - (a_pkq->y2_0)) * (a_pkq->w);

    a_pkq->in1_m2 = (a_pkq->in1_m1);
    a_pkq->in1_m1 = a_in1;

    a_pkq->y2_1 = a_pkq->in1_m2;
    a_pkq->FIR_out_1 = (a_in1 - (a_pkq->y2_1)) * (a_pkq->w);

    a_pkq->coeff1_x_out_m1_0 = (a_pkq->FIR_out_0) -
            ((a_pkq->coeff1) * (a_pkq->out0_m1));
    a_pkq->coeff2_x_out_m2_0 = (a_pkq->coeff1_x_out_m1_0) -
            ((a_pkq->coeff2) * (a_pkq->out0_m2));
    a_pkq->iir_output0 = f_remove_denormal(
            (a_pkq->coeff2_x_out_m2_0) * (a_pkq->coeff0));
    a_pkq->output0 = ((a_pkq->d_times_B) * (a_pkq->iir_output0)) + a_in0;

    a_pkq->coeff1_x_out_m1_1 = (a_pkq->FIR_out_1) -
            ((a_pkq->coeff1) * (a_pkq->out1_m1));
    a_pkq->coeff2_x_out_m2_1 = (a_pkq->coeff1_x_out_m1_1) -
            ((a_pkq->coeff2) * (a_pkq->out1_m2));
    a_pkq->iir_output1 =
            f_remove_denormal((a_pkq->coeff2_x_out_m2_1) * (a_pkq->coeff0));
    a_pkq->output1 = ((a_pkq->d_times_B) * (a_pkq->iir_output1)) + a_in1;


    a_pkq->out0_m2 = (a_pkq->out0_m1);
    a_pkq->out0_m1 = (a_pkq->iir_output0);

    a_pkq->out1_m2 = (a_pkq->out1_m1);
    a_pkq->out1_m1 = (a_pkq->iir_output1);
}

void g_pkq_init(t_pkq_peak_eq * f_result, SGFLT a_sample_rate){
    f_result->B = 0.0f;
    f_result->FIR_out_0 = 0.0f;
    f_result->FIR_out_1 = 0.0f;
    f_result->BW = 0.0f;
    f_result->coeff1 = 0.0f;
    f_result->coeff2 = 0.0f;
    f_result->d = 0.0f;
    f_result->dB = 0.0f;
    f_result->d_times_B = 0.0f;
    f_result->exp_db = 0.0f;
    f_result->exp_value = 0.0f;
    f_result->in0_m1 = 0.0f;
    f_result->in0_m2 = 0.0f;
    f_result->in1_m1 = 0.0f;
    f_result->in1_m2 = 0.0f;
    f_result->input0 = 0.0f;
    f_result->input1 = 0.0f;
    f_result->out0_m1 = 0.0f;
    f_result->out0_m2 = 0.0f;
    f_result->out1_m1 = 0.0f;
    f_result->out1_m2 = 0.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->pi_div_sr = PI / a_sample_rate;
    f_result->pitch = 66.0f;
    f_result->coeff0 = 0.0f;
    f_result->warp_input = 0.0f;
    f_result->warp_input_squared = 0.0f;
    f_result->warp_input_tripled = 0.0f;
    f_result->warp_output = 0.0f;
    f_result->warp_outstream0 = 0.0f;
    f_result->warp_outstream1 = 0.0f;
    f_result->w = 0.0f;
    f_result->w2 = 0.0f;
    f_result->w2p1 = 0.0f;
    f_result->wQ = 0.0f;
    f_result->y2_0 = 0.0f;
    f_result->y2_1 = 0.0f;
    f_result->last_pitch = -452.66447f;
}

void g_eq6_init(t_eq6 * f_result, SGFLT a_sr)
{
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;

    int f_i = 0;

    while(f_i < 6)
    {
        g_pkq_init(&f_result->eqs[f_i], a_sr);
        ++f_i;
    }
}

void v_eq6_connect_port(t_eq6 * a_eq6, int a_port, SGFLT * a_ptr)
{
    int f_eq_num = a_port / 3;
    int f_knob_num = a_port % 3;

    a_eq6->knobs[f_eq_num][f_knob_num] = a_ptr;
}

void v_eq6_set(t_eq6* a_eq6){
    int f_i;

    for(f_i = 0; f_i < 6; ++f_i)
    {
        if(*a_eq6->knobs[f_i][2] != 0.0f)
        {
            v_pkq_calc_coeffs(&a_eq6->eqs[f_i],
                    *a_eq6->knobs[f_i][0],
                    *a_eq6->knobs[f_i][1] * 0.01f,
                    *a_eq6->knobs[f_i][2] * 0.1f);
        }
    }
}

void v_eq6_run(t_eq6 *a_eq6, SGFLT a_input0, SGFLT a_input1)
{
    int f_i;

    a_eq6->output0 = a_input0;
    a_eq6->output1 = a_input1;

    for(f_i = 0; f_i < 6; ++f_i)
    {
        if(*a_eq6->knobs[f_i][2] != 0.0f)
        {
            v_pkq_run(&a_eq6->eqs[f_i], a_eq6->output0, a_eq6->output1);

            a_eq6->output0 = a_eq6->eqs[f_i].output0;
            a_eq6->output1 = a_eq6->eqs[f_i].output1;
        }
    }
}

