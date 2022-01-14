#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/delay/delay.h"
#include "audiodsp/modules/delay/delay_plugin.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/signal_routing/dry_wet.h"


/*t_sg_delay * g_ldl_get_delay(
 * SGFLT a_seconds, //The maximum amount of time for the delay to buffer
 * SGFLT a_sr  //sample rate
 * )
 */
t_sg_delay * g_ldl_get_delay(SGFLT a_seconds, SGFLT a_sr){
    t_sg_delay* f_result;
    hpalloc((void**)&f_result, sizeof(t_sg_delay));

    g_dly_init(&f_result->delay0, a_seconds, a_sr);
    g_dly_init(&f_result->delay1, a_seconds, a_sr);
    g_dly_tap_init(&f_result->tap0);
    g_dly_tap_init(&f_result->tap1);
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->feedback0 = 0.0f;
    f_result->feedback1 = 0.0f;
    f_result->feedback_db = -50.0f;
    f_result->feedback_linear = 0.0f;
    dry_wet_init(&f_result->dw0);
    dry_wet_init(&f_result->dw1);
    g_axf_init(&f_result->stereo_xfade0, -3.0f);
    g_axf_init(&f_result->stereo_xfade1, -3.0f);

    env_follower_init(&f_result->feedback_env_follower, a_sr);
    env_follower_init(&f_result->input_env_follower, a_sr);
    f_result->combined_inputs = 0.0f;

    g_lim_init(&f_result->limiter, a_sr, 1);
    f_result->last_duck = -99.999f;

    f_result->limiter_gain = 0.0f;

    g_svf_init(&f_result->svf0, a_sr);
    g_svf_init(&f_result->svf1, a_sr);
    v_svf_set_res(&f_result->svf0, -18.0f);
    v_svf_set_res(&f_result->svf1, -18.0f);

    return f_result;
}

void v_ldl_run_delay(t_sg_delay* a_dly, SGFLT a_in0, SGFLT a_in1)
{
    v_lim_run(&a_dly->limiter, a_in0, a_in1);

    v_dly_run_delay(
        &a_dly->delay0,
        f_axf_run_xfade(
            &a_dly->stereo_xfade0,
            (a_in0 + ((a_dly->feedback0) * (a_dly->feedback_linear))),
            (
                (a_dly->feedback1 * a_dly->feedback_linear) +
                ((a_in0 + a_in1) * 0.5f)
            )
        )
    );

    v_dly_run_tap(&a_dly->delay0, &a_dly->tap0);

    v_dly_run_delay(
        &a_dly->delay1,
        f_axf_run_xfade(
            &a_dly->stereo_xfade0 ,
            (a_in1 + (a_dly->feedback1 * a_dly->feedback_linear)),
            a_dly->tap0.output
        )
    );

    v_dly_run_tap(&a_dly->delay1, &a_dly->tap1);

    a_dly->feedback0 = v_svf_run_2_pole_lp(&a_dly->svf0, a_dly->tap0.output);
    a_dly->feedback1 = v_svf_run_2_pole_lp(&a_dly->svf1, a_dly->tap1.output);

    a_dly->limiter_gain =  (a_dly->limiter.gain)  * (a_dly->limiter.autogain);

    if(a_dly->limiter_gain > 1.0f){
        a_dly->limiter_gain = 1.0f;
    }

    v_dw_run_dry_wet(
        &a_dly->dw0,
        a_in0,
        a_dly->feedback0 * a_dly->limiter_gain
    );
    v_dw_run_dry_wet(
        &a_dly->dw1,
        a_in1,
        a_dly->feedback1 * a_dly->limiter_gain
    );

    a_dly->output0 = (a_dly->dw0.output);
    a_dly->output1 = (a_dly->dw1.output);
}


/*void v_ldl_set_delay(
 * t_sg_delay* a_dly,
 * SGFLT a_seconds,
 * SGFLT a_feedback_db, //This should not exceed -2 or it could explode
 * int a_is_ducking,
 * SGFLT a_wet,
 * SGFLT a_dry,
 * SGFLT a_stereo)  //Crossfading between dual-mono and stereo.  0 to 1
 */
void v_ldl_set_delay(
    t_sg_delay* a_dly,
    SGFLT a_seconds,
    SGFLT a_feedback_db,
    SGFLT a_wet,
    SGFLT a_dry,
    SGFLT a_stereo,
    SGFLT a_duck,
    SGFLT a_damp
){
    v_dly_set_delay_seconds(&a_dly->delay0, &a_dly->tap0, a_seconds);
    v_dly_set_delay_seconds(&a_dly->delay1, &a_dly->tap1, a_seconds);

    v_axf_set_xfade(&a_dly->stereo_xfade0, a_stereo);
    v_axf_set_xfade(&a_dly->stereo_xfade1, a_stereo);

    if(a_feedback_db != (a_dly->feedback_db)){
        a_dly->feedback_db = a_feedback_db;
        a_dly->feedback_linear = f_db_to_linear_fast(a_feedback_db);
        if(a_dly->feedback_linear > 0.9f){
            a_dly->feedback_linear = 0.9f;
        }
    }

    if(a_dly->last_duck != a_duck){
        a_dly->last_duck = a_duck;
        v_lim_set(&a_dly->limiter, a_duck, 0.0f, 400.0f);
    }

    v_svf_set_cutoff_base(&a_dly->svf0, a_damp);
    v_svf_set_cutoff_base(&a_dly->svf1, a_damp);
    v_svf_set_cutoff(&a_dly->svf0);
    v_svf_set_cutoff(&a_dly->svf1);

    v_dw_set_dry_wet(&a_dly->dw0, a_dry, a_wet);
    v_dw_set_dry_wet(&a_dly->dw1, a_dry, a_wet);
}

