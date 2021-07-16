#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/distortion/sample_and_hold.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


void g_sah_init(t_sah_sample_and_hold * f_result, SGFLT a_sr)
{
    f_result->hold_count = 1;
    f_result->hold_counter = 0;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->hold0 = 0.0f;
    f_result->hold1 = 0.0f;
    f_result->last_pitch = -99.999f;
    f_result->sr = a_sr;
    f_result->last_wet = -99.00088f;
    g_axf_init(&f_result->xfade, -3.0f);
}

t_sah_sample_and_hold * g_sah_sample_and_hold_get(SGFLT a_sr)
{
    t_sah_sample_and_hold * f_result;

    lmalloc((void**)&f_result, sizeof(t_sah_sample_and_hold));
    g_sah_init(f_result, a_sr);
    return f_result;
}

void v_sah_sample_and_hold_set(t_sah_sample_and_hold* a_sah, SGFLT a_pitch,
        SGFLT a_wet)
{
    if(a_sah->last_pitch != a_pitch)
    {
        a_sah->last_pitch = a_pitch;
        a_sah->hold_count =
            (int)(a_sah->sr / f_pit_midi_note_to_hz_fast(a_pitch));
    }

    if(a_sah->last_wet != a_wet)
    {
        a_sah->last_wet = a_wet;
        v_axf_set_xfade(&a_sah->xfade, a_wet);
    }
}

void v_sah_sample_and_hold_run(t_sah_sample_and_hold* a_sah,
        SGFLT a_in0, SGFLT a_in1)
{
    a_sah->output0 = f_axf_run_xfade(&a_sah->xfade, a_in0, a_sah->hold0);
    a_sah->output1 = f_axf_run_xfade(&a_sah->xfade, a_in1, a_sah->hold1);

    ++a_sah->hold_counter;

    if(a_sah->hold_counter >= a_sah->hold_count)
    {
        a_sah->hold_counter = 0;
        a_sah->hold0 = a_in0;
        a_sah->hold1 = a_in1;
    }
}

