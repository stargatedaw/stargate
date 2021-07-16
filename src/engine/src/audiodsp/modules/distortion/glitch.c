#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/distortion/glitch.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


void v_glc_glitch_free(t_glc_glitch * a_glc){
    if(a_glc){
        free(a_glc->buffer);
        //free(a_glc);
    }
}

void g_glc_init(t_glc_glitch * f_result, SGFLT a_sr){
    f_result->buffer_size = (int)(a_sr * (1.0f/19.0f));

    lmalloc((void**)&f_result->buffer, sizeof(SGFLT) * f_result->buffer_size);

    int f_i = 0;

    while(f_i < f_result->buffer_size){
        f_result->buffer[f_i] = 0.0f;
        f_i++;
    }

    f_result->buffer_ptr = 0;
    f_result->current_repeat_count = 0;
    f_result->is_repeating = 0;
    f_result->last_pitch = 55.5555f;
    f_result->last_repeat = 99.99f;
    f_result->last_wet = -1.111f;
    f_result->repeat_count = 42;
    f_result->sample_count = 99;
    f_result->sample_tmp = 0.0f;
    f_result->sr = a_sr;
    g_axf_init(&f_result->xfade, -3.0f);
}

t_glc_glitch * g_glc_glitch_get(SGFLT a_sr)
{
    t_glc_glitch * f_result;

    lmalloc((void**)&f_result, sizeof(t_glc_glitch));
    g_glc_init(f_result, a_sr);
    return f_result;
}

void v_glc_glitch_set(t_glc_glitch* a_glc, SGFLT a_pitch, SGFLT a_repeat,
        SGFLT a_wet)
{
    if(a_glc->last_pitch != a_pitch)
    {
        a_glc->last_pitch = a_pitch;
        a_glc->sample_count =
            (int)((a_glc->sr) / (f_pit_midi_note_to_hz_fast(a_pitch)));
    }

    if(a_glc->last_repeat != a_repeat)
    {
        a_glc->last_repeat = a_repeat;
        a_glc->repeat_count = (int)(a_repeat);
    }

    if(a_glc->last_wet != a_wet)
    {
        a_glc->last_wet = a_wet;
        v_axf_set_xfade(&a_glc->xfade, a_wet);
    }
}

void v_glc_glitch_retrigger(t_glc_glitch* a_glc)
{
    a_glc->buffer_ptr = 0;
}

void v_glc_glitch_run(t_glc_glitch* a_glc, SGFLT a_input0, SGFLT a_input1)
{
    a_glc->output0 = f_axf_run_xfade(&a_glc->xfade, a_input0,
            a_glc->buffer[a_glc->buffer_ptr]);
    a_glc->output1 = f_axf_run_xfade(&a_glc->xfade, a_input1,
            a_glc->buffer[a_glc->buffer_ptr]);

    if(!a_glc->is_repeating)
    {
        a_glc->buffer[a_glc->buffer_ptr] = (a_input0 + a_input1) * 0.5f;
    }

    a_glc->buffer_ptr++;

    if(a_glc->buffer_ptr >= a_glc->sample_count)
    {
        a_glc->buffer_ptr = 0;
        if(a_glc->is_repeating)
        {
            a_glc->current_repeat_count++;

            if(a_glc->current_repeat_count >= a_glc->repeat_count)
            {
                a_glc->current_repeat_count = 0;
                a_glc->is_repeating = 0;
            }
        }
        else
        {
            a_glc->is_repeating = 1;
        }
    }
}
