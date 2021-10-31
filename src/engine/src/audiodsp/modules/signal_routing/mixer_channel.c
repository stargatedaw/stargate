#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/modules/signal_routing/mixer_channel.h"


void v_mxc_run_smoothers(
    t_mxc_mixer_channel* a_mxc,
    SGFLT a_amp,
    SGFLT a_pan,
    SGFLT a_pan_law
){
    v_sml_run(&a_mxc->amp_smoother, a_amp);
    v_sml_run(&a_mxc->pan_smoother, a_pan);

    if(a_pan > 0.5f)    {
        a_mxc->pan_law_gain_linear = f_db_to_linear_fast(
            (a_pan_law * a_mxc->pan_smoother.last_value * 2)
        );
    }
    else
    {
        a_mxc->pan_law_gain_linear = f_db_to_linear_fast(
            (a_pan_law * (1 - a_mxc->pan_smoother.last_value) * 2)
        );
    }

    a_mxc->pan0 = f_sine_fast_run(
        (((1 - a_pan) * 0.5) + 0.25f)
    ) * (a_mxc->pan_law_gain_linear);
    a_mxc->pan1 = f_sine_fast_run(
        ((a_pan * 0.5) + 0.25f)
    ) * (a_mxc->pan_law_gain_linear);

    a_mxc->amp_linear = f_db_to_linear_fast(
        (a_mxc->amp_smoother.last_value)
    );

    a_mxc->main_gain0 = (a_mxc->amp_linear) * (a_mxc->pan0);
    a_mxc->main_gain1 = (a_mxc->amp_linear) * (a_mxc->pan1);
}

void v_mxc_mix_stereo_to_stereo(
    t_mxc_mixer_channel* a_mxc,
    SGFLT a_in0,
    SGFLT a_in1,
    SGFLT a_amp,
    SGFLT a_gain,
    SGFLT a_pan,
    SGFLT a_pan_law
){
    v_mxc_run_smoothers(a_mxc, a_amp, a_pan, a_pan_law);

    a_mxc->out0 = (a_mxc->main_gain0) * a_in0;
    a_mxc->out1 = (a_mxc->main_gain1) * a_in1;
}

void v_mxc_mix_stereo_to_mono(
    t_mxc_mixer_channel* a_mxc,
    SGFLT a_in0,
    SGFLT a_in1,
    SGFLT a_amp,
    SGFLT a_gain,
    SGFLT a_pan,
    SGFLT a_pan_law
){
    v_mxc_run_smoothers(a_mxc, a_amp, a_pan, a_pan_law);

    a_mxc->in0 = (a_in0 + a_in1) * 0.5f;
    a_mxc->in1 = (a_mxc->in0);

    a_mxc->out0 = (a_mxc->main_gain0) * a_mxc->in0;
    a_mxc->out1 = (a_mxc->main_gain1) * a_mxc->in1;
}

t_mxc_mixer_channel * g_mxc_get(SGFLT a_sr){
    t_mxc_mixer_channel* f_result = (t_mxc_mixer_channel*)malloc(
        sizeof(t_mxc_mixer_channel)
    );

    f_result->amp_linear = 1;
    f_result->in0 = 0;
    f_result->in1 = 0;
    f_result->gain_db = 0;
    f_result->gain_linear = 1;
    f_result->out0 = 0;
    f_result->out1 = 0;
    f_result->main_gain0 = 1;
    f_result->main_gain1 = 1;
    g_sml_init(
        &f_result->amp_smoother,
        a_sr,
        0,
        -48,
        0.5f
    );
    g_sml_init(
        &f_result->pan_smoother,
        a_sr,
        1.0f,
        -1.0f,
        0.5f
    );
    f_result->pan_law_gain_linear = 3.0f;
    f_result->pan0 = 1;
    f_result->pan1 = 1;

    return f_result;
}

