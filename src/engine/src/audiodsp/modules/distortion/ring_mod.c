#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/distortion/ring_mod.h"
#include "audiodsp/modules/oscillator/osc_simple.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


void g_rmd_init(t_rmd_ring_mod * f_result, SGFLT a_sr)
{
    g_osc_init_osc_simple_single(&f_result->osc, a_sr, 0);
    v_osc_set_simple_osc_unison_type(&f_result->osc, 3);
    v_osc_set_uni_voice_count(&f_result->osc, 1);
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->last_wet = -110.0f;
    f_result->pitch = -99.99f;
    f_result->osc_output = 0.0f;
    g_axf_init(&f_result->xfade, 0.5f);
}

t_rmd_ring_mod * g_rmd_ring_mod_get(SGFLT a_sr)
{
    t_rmd_ring_mod * f_result;
    lmalloc((void**)&f_result, sizeof(t_rmd_ring_mod));
    g_rmd_init(f_result, a_sr);
    return f_result;
}

void v_rmd_ring_mod_set(t_rmd_ring_mod* a_rmd, SGFLT a_pitch, SGFLT a_wet)
{
    if(a_rmd->last_wet != a_wet)
    {
        a_rmd->last_wet = a_wet;
        v_axf_set_xfade(&a_rmd->xfade, a_wet);
    }

    if(a_rmd->pitch != a_pitch)
    {
        a_rmd->pitch = a_pitch;
        v_osc_set_unison_pitch(&a_rmd->osc, 0.0f, a_pitch);
    }
}

void v_rmd_ring_mod_run(t_rmd_ring_mod* a_rmd, SGFLT a_input0, SGFLT a_input1)
{
    a_rmd->osc_output = f_osc_run_unison_osc(&a_rmd->osc);

    a_rmd->output0 = f_axf_run_xfade(&a_rmd->xfade, a_input0,
            (a_input0 * (a_rmd->osc_output)));
    a_rmd->output1 = f_axf_run_xfade(&a_rmd->xfade, a_input1,
            (a_input1 * (a_rmd->osc_output)));
}

