#include <math.h>

#include "audiodsp/constants.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/oscillator/osc_simple.h"

/* void v_osc_set_uni_voice_count(
 * t_osc_simple_unison* a_osc_ptr,
 * int a_value) //the number of unison voices this oscillator should use
 */
void v_osc_set_uni_voice_count(
    t_osc_simple_unison* a_osc_ptr,
    int a_value
){
    sg_assert(
        a_value <= OSC_UNISON_MAX_VOICES && a_value >= 1,
        "v_osc_set_uni_voice_count: value %i out of range 1 to %i",
        a_value,
        OSC_UNISON_MAX_VOICES
    );

    if(a_osc_ptr->voice_count != a_value){
        // Force a recalculation of v_osc_set_unison_pitch
        a_osc_ptr->last_pitch = -12345.0f;
        a_osc_ptr->voice_count = a_value;
        a_osc_ptr->adjusted_amp = (
            1.0f / (SGFLT)a_osc_ptr->voice_count
        ) + (((SGFLT)(a_osc_ptr->voice_count - 1)) * .06f);
    }
}


/* void v_osc_set_unison_pitch(
 * t_osc_simple_unison * a_osc_ptr,
 * SGFLT a_spread, //the total spread of the unison pitches, the distance in
 *                 //semitones from bottom pitch to top.  Typically .1 to .5
 * SGFLT a_pitch)  //the pitch of the oscillator in MIDI note number,
 *                 //typically 32 to 70
 */
void v_osc_set_unison_pitch(
    t_osc_simple_unison * a_osc_ptr,
    SGFLT a_spread,
    SGFLT a_pitch
){
    if((a_osc_ptr->voice_count) == 1){
        a_osc_ptr->voice_inc[0] = f_pit_midi_note_to_hz_fast(
            a_pitch
        ) * a_osc_ptr->sr_recip;
    } else {
        int f_changed = 0;
        if(unlikely(a_spread != a_osc_ptr->uni_spread)){
            a_osc_ptr->uni_spread = a_spread;
            a_osc_ptr->bottom_pitch = -0.5f * a_spread;
            a_osc_ptr->pitch_inc = a_spread / (SGFLT)a_osc_ptr->voice_count;
            f_changed = 1;
        }

        if(a_pitch != a_osc_ptr->last_pitch || f_changed){
            a_osc_ptr->last_pitch = a_pitch;

            int f_i;

            for(f_i = 0; f_i < (a_osc_ptr->voice_count); ++f_i){
                a_osc_ptr->voice_inc[f_i] = f_pit_midi_note_to_hz_fast(
                    (
                        a_pitch + a_osc_ptr->bottom_pitch +
                        (a_osc_ptr->pitch_inc * (SGFLT)f_i)
                    )
                ) * a_osc_ptr->sr_recip;
            }
        }
    }
}

/* SGFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr)
 *
 * Returns one sample of an oscillator's output
 */
SGFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr){
    int f_i = 0;
    a_osc_ptr->current_sample = 0.0f;
    t_osc_core *osc_core;
    const int voice_count = a_osc_ptr->voice_count;

    for(f_i = 0; f_i < voice_count; ++f_i){
        osc_core = &a_osc_ptr->osc_cores[f_i];
        v_run_osc(osc_core, a_osc_ptr->voice_inc[f_i]);
        a_osc_ptr->current_sample +=  a_osc_ptr->osc_type(osc_core);
    }

    return (a_osc_ptr->current_sample) * (a_osc_ptr->adjusted_amp);
}

/* SGFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr)
 *
 * For warming up oscillators
 */
void f_osc_run_unison_osc_core_only(
    t_osc_simple_unison * a_osc_ptr
){
    int f_i = 0;
    a_osc_ptr->current_sample = 0.0f;

    for(f_i = 0; f_i < (a_osc_ptr->voice_count); ++f_i){
        v_run_osc(&a_osc_ptr->osc_cores[f_i], a_osc_ptr->voice_inc[f_i]);
    }
}

SGFLT f_osc_run_unison_osc_sync(t_osc_simple_unison * a_osc_ptr){
    int f_i = 0;
    a_osc_ptr->current_sample = 0.0f;

    a_osc_ptr->is_resetting =
            v_run_osc_sync(&a_osc_ptr->osc_cores[f_i],
            (a_osc_ptr->voice_inc[f_i]));
    a_osc_ptr->current_sample =
            (a_osc_ptr->current_sample) +
            a_osc_ptr->osc_type(&a_osc_ptr->osc_cores[f_i]);

    return (a_osc_ptr->current_sample) * (a_osc_ptr->adjusted_amp);
}

SGFLT f_get_saw(t_osc_core * a_core)
{
    return (((a_core->output) * 2.0f) - 1.0f);
}

SGFLT f_get_sine(t_osc_core * a_core)
{
    //return sin((a_core->output) * PI2);
    return f_sine_fast_run((a_core->output));
}

SGFLT f_get_square(t_osc_core * a_core)
{
    if((a_core->output) >= 0.5f)
    {
        return 1.0f;
    }
    else
    {
        return -1.0f;
    }
}

SGFLT f_get_hsquare(t_osc_core * a_core)
{
    if((a_core->output) <= 0.25f)
    {
        return 1.0f;
    }
    else
    {
        return -0.33333333333f;
    }
}

SGFLT f_get_qsquare(t_osc_core * a_core)
{
    if((a_core->output) <= 0.125f)
    {
        return 1.0f;
    }
    else
    {
        return -0.14f;
    }
}

SGFLT f_get_triangle(t_osc_core * a_core)
{
    SGFLT f_ramp = ((a_core->output) * 4.0f) - 2.0f;
    if(f_ramp > 1.0f)
    {
        return 2.0f - f_ramp;
    }
    else if(f_ramp < -1.0f)
    {
        return (2.0f + f_ramp) * -1.0f;
    }
    else
    {
        return f_ramp;
    }
}


//Return zero if the oscillator is turned off.
SGFLT f_get_osc_off(t_osc_core * a_core){
    return 0.0f;
}

SG_THREAD_LOCAL fp_get_osc_func_ptr SIMPLE_OSC_TYPES[] = {
    f_get_osc_off,
    f_get_saw,
    f_get_square,
    f_get_triangle,
    f_get_sine
};

SG_THREAD_LOCAL fp_get_osc_func_ptr SIMPLE_OSC_TYPES_v2[] = {
    f_get_osc_off,
    f_get_saw,
    f_get_square,
    f_get_hsquare,
    f_get_qsquare,
    f_get_triangle,
    f_get_sine
};


void v_osc_set_simple_osc_unison_type(
        t_osc_simple_unison * a_osc_ptr, int a_index)
{
    a_osc_ptr->osc_type = SIMPLE_OSC_TYPES[a_index];
}

void v_osc_set_simple_osc_unison_type_v2(
    t_osc_simple_unison * a_osc_ptr,
    int a_index
){
    a_osc_ptr->osc_type = SIMPLE_OSC_TYPES_v2[a_index];
}

/*Resync the oscillators at note_on to hopefully avoid phasing artifacts*/
void v_osc_note_on_sync_phases(t_osc_simple_unison * a_osc_ptr){
    int i;

    if(a_osc_ptr->voice_count == 1){
        a_osc_ptr->osc_cores[0].output = 0.0;
    } else {
        for(i = 0; i < a_osc_ptr->voice_count; ++i){
            a_osc_ptr->osc_cores[i].output = a_osc_ptr->phases[i];
        }
    }
}

void v_osc_note_on_sync_phases_hard(
    t_osc_simple_unison * a_osc_ptr
){
    int i;
    for(i = 0; i < a_osc_ptr->voice_count; ++i){
        a_osc_ptr->osc_cores[i].output = 0.0f;
    }
}

NO_OPTIMIZATION void g_osc_simple_unison_init(
    t_osc_simple_unison * f_result,
    SGFLT a_sample_rate,
    int voice_num
){
    f_result->osc_type = f_get_saw;
    f_result->sr_recip = 1.0 / a_sample_rate;
    f_result->adjusted_amp = 1.0;
    f_result->bottom_pitch = -0.1;
    f_result->current_sample = 0.0;
    f_result->osc_type = f_get_osc_off;
    f_result->pitch_inc = 0.1f;
    f_result->uni_spread = 0.1f;
    f_result->voice_count = 1;
    f_result->is_resetting = 0;
    f_result->last_pitch = -12345.0f;
    v_osc_set_uni_voice_count(f_result, OSC_UNISON_MAX_VOICES);

    int f_i;

    for(f_i = 0; f_i < OSC_UNISON_MAX_VOICES; ++f_i){
        g_init_osc_core(&f_result->osc_cores[f_i]);
    }

    v_osc_set_unison_pitch(
        f_result,
        .5f,
        60.0f + (1.01234 * (float)voice_num)
    );

    for(f_i = 0; f_i < OSC_UNISON_MAX_VOICES; ++f_i){
        // Prevent phasing artifacts from the oscillators starting at the
        // same phase.
        f_result->phases[f_i] =
            f_result->osc_cores[f_i].output =
                OSC_CORE_PHASES[voice_num][f_i];
    }

    v_osc_set_unison_pitch(f_result, .2, 60.0f);

}

void g_osc_init_osc_simple_single(
    t_osc_simple_unison * f_result,
    SGFLT a_sample_rate,
    int voice_num
){
    f_result->osc_type = f_get_saw;
    f_result->sr_recip = 1.0 / a_sample_rate;
    f_result->adjusted_amp = 1.0;
    f_result->bottom_pitch = -0.1;
    f_result->current_sample = 0.0;
    f_result->osc_type = f_get_osc_off;
    f_result->pitch_inc = 0.1f;
    f_result->uni_spread = 0.1f;
    f_result->last_pitch = -12345.0f;
    f_result->voice_count = 1;
    v_osc_set_uni_voice_count(f_result, 1);

    int f_i = 0;

    while(f_i < (OSC_UNISON_MAX_VOICES))
    {
        g_init_osc_core(&f_result->osc_cores[f_i]);
        ++f_i;
    }

    v_osc_set_unison_pitch(
        f_result,
        .5f,
        60.0f + (float)voice_num * 1.01234
    );

    f_i = 0;

    while(f_i < (OSC_UNISON_MAX_VOICES)){
        f_result->phases[f_i] = 0.0f;
        ++f_i;
    }

    v_osc_set_unison_pitch(f_result, .2, 60.0f);
}

t_osc_simple_unison * g_osc_get_osc_simple_single(
    SGFLT a_sample_rate,
    int voice_num
){
    t_osc_simple_unison * f_result;
    lmalloc((void**)&f_result, sizeof(t_osc_simple_unison));
    g_osc_init_osc_simple_single(f_result, a_sample_rate, voice_num);

    return f_result;
}

