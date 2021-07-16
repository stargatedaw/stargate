#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules//modulation/adsr.h"
#include "audiodsp/modules/distortion/glitch_v2.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


void g_glc_glitch_v2_init(t_glc_glitch_v2 * f_result, SGFLT a_sr)
{
    f_result->buffer_size = (int)(a_sr * 0.25f);

    hpalloc(
        (void**)&f_result->buffer,
        sizeof(SGFLT) * (f_result->buffer_size + 100)
    );

    g_pit_ratio_init(&f_result->pitch_ratio);
    g_adsr_init(&f_result->adsr, a_sr);
    g_axf_init(&f_result->xfade, -3.0f);

    v_adsr_set_adsr(&f_result->adsr, 0.0f, 0.05f, 1.0f, 0.01f);

    int f_i = 0;

    while(f_i < f_result->buffer_size + 100)
    {
        f_result->buffer[f_i] = 0.0f;
        ++f_i;
    }

    f_result->read_head_int = 0;
    f_result->read_head = 0.0f;
    f_result->rate = 1.0f;
    f_result->write_head = 0;
    f_result->last_time = 654654.89f;
    f_result->last_pitch = 654654.89f;
    f_result->sample_count = 99;
    f_result->sample_count_f = 99.99f;
    f_result->sr = a_sr;
}

void v_glc_glitch_v2_set(t_glc_glitch_v2* a_glc, SGFLT a_time, SGFLT a_pitch)
{
    if(a_glc->last_time != a_time)
    {
        a_glc->last_time = a_time;
        a_glc->sample_count_f = ((a_glc->sr) * a_time);
        a_glc->sample_count = (int)a_glc->sample_count_f;

        if(a_glc->read_head >= a_glc->sample_count_f)
        {
            a_glc->read_head = 0.0f;
        }
    }

    if(a_glc->last_pitch != a_pitch)
    {
        a_glc->last_pitch = a_pitch;
        if(a_pitch == 0.0f)
        {
            a_glc->rate = 1.0f;
        }
        else if (a_pitch > 0.0f)
        {
            a_glc->rate = f_pit_midi_note_to_ratio_fast(
                0.0f, a_pitch, &a_glc->pitch_ratio);
        }
        else
        {
            a_glc->rate = f_pit_midi_note_to_ratio_fast(
                a_pitch * -1.0f, 0.0f, &a_glc->pitch_ratio);
        }

    }
}

void v_glc_glitch_v2_retrigger(t_glc_glitch_v2* a_glc)
{
    a_glc->read_head = 0.0f;
    a_glc->read_head_int = 0;
    a_glc->write_head = 0;
    a_glc->first_run = 1;
    v_adsr_retrigger(&a_glc->adsr);
}

void v_glc_glitch_v2_release(t_glc_glitch_v2* a_glc)
{
    v_adsr_release(&a_glc->adsr);
}

void v_glc_glitch_v2_run(t_glc_glitch_v2* a_glc, SGFLT a_input0, SGFLT a_input1)
{
    if(a_glc->write_head < a_glc->buffer_size)
    {
        a_glc->buffer[a_glc->write_head] = (a_input0 + a_input1) * 0.5f;
        ++a_glc->write_head;
    }

    v_adsr_run(&a_glc->adsr);

    if(a_glc->first_run)
    {
        a_glc->output0 = a_input0;
        a_glc->output1 = a_input1;

        ++a_glc->read_head_int;
        if(a_glc->read_head_int >= a_glc->sample_count)
        {
            a_glc->first_run = 0;
        }
    }
    else
    {
        SGFLT f_pos = a_glc->read_head;

        if(f_pos > (SGFLT)a_glc->write_head)
        {
            f_pos = (SGFLT)a_glc->write_head;
        }

        SGFLT f_output =
            f_cubic_interpolate_ptr_wrap(
                a_glc->buffer, a_glc->sample_count, a_glc->read_head);

        v_axf_set_xfade(&a_glc->xfade, a_glc->adsr.output);

        a_glc->output0 = f_axf_run_xfade(&a_glc->xfade, a_input0, f_output);
        a_glc->output1 = f_axf_run_xfade(&a_glc->xfade, a_input1, f_output);

        a_glc->read_head += a_glc->rate;
        if(a_glc->read_head >= a_glc->sample_count_f)
        {
            a_glc->read_head -= a_glc->sample_count_f;
        }
    }
}
