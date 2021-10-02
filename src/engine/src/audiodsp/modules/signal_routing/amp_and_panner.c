#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/signal_routing/amp_and_panner.h"


void v_app_set(t_amp_and_panner* a_app,SGFLT a_db,SGFLT a_pan)
{
    a_app->amp_db = a_db;
    a_app->pan = a_pan;

    a_app->amp_linear = f_db_to_linear_fast(a_db);

    a_app->amp_linear0 =
        (f_sine_fast_run(((a_pan * .5f) + 0.25f)) * 0.5f + 1.0f)
            * (a_app->amp_linear);
    a_app->amp_linear1 =
        (f_sine_fast_run((0.75f - (a_pan * 0.5f))) * 0.5f + 1.0f)
            * (a_app->amp_linear);
}

void v_app_run(t_amp_and_panner* a_app, SGFLT a_in0, SGFLT a_in1)
{
    a_app->output0 = a_in0 * (a_app->amp_linear0);
    a_app->output1 = a_in1 * (a_app->amp_linear1);
}

void v_app_run_monofier(
    t_amp_and_panner* a_app,
    SGFLT a_in0,
    SGFLT a_in1
){
    SGFLT mono = a_in0 + a_in1;
    v_app_run(a_app, mono, mono);
}

void g_app_init(t_amp_and_panner * f_result)
{
    f_result->amp_db = 0.0f;
    f_result->pan = 0.0f;
    f_result->amp_linear0 = 1.0f;
    f_result->amp_linear1 = 1.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
}

t_amp_and_panner * g_app_get()
{
    t_amp_and_panner * f_result;

    lmalloc((void**)&f_result, sizeof(t_amp_and_panner));
    g_app_init(f_result);

    return f_result;
}

void v_app_free(t_amp_and_panner * a_app)
{
    free(a_app);
}
