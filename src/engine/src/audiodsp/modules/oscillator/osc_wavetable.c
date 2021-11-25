#include <math.h>

#include "audiodsp/constants.h"
#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/oscillator/osc_wavetable.h"
#include "audiodsp/modules/oscillator/wavetables.h"


void v_osc_wav_set_waveform(
    t_osc_wav_unison* a_osc_wav,
    SGFLT * a_waveform,
    int a_sample_count
){
    a_osc_wav->selected_wavetable = a_waveform;
    a_osc_wav->selected_wavetable_sample_count = a_sample_count;
    a_osc_wav->selected_wavetable_sample_count_SGFLT = (SGFLT)(a_sample_count);
}

/* void v_osc_wav_set_uni_voice_count(
 * t_osc_simple_unison* a_osc_ptr,
 * int a_value) //the number of unison voices this oscillator should use
 */
void v_osc_wav_set_uni_voice_count(t_osc_wav_unison* a_osc_ptr, int a_value)
{
    if(a_value > (OSC_UNISON_MAX_VOICES))
    {
        a_osc_ptr->voice_count = OSC_UNISON_MAX_VOICES;
    }
    else if(a_value < 1)
    {
        a_osc_ptr->voice_count = 1;
    }
    else
    {
        a_osc_ptr->voice_count = a_value;
    }

    a_osc_ptr->adjusted_amp = (1.0f / (SGFLT)(a_osc_ptr->voice_count)) +
            ((a_osc_ptr->voice_count - 1) * .06f);
}


/* void v_osc_set_unison_pitch(
 * t_osc_simple_unison * a_osc_ptr,
 * SGFLT a_spread, //the total spread of the unison pitches,
 *                 //the distance in semitones from bottom pitch to top.
 *                 //Typically .1 to .5
 * SGFLT a_pitch,  //the pitch of the oscillator in MIDI note number,
 *                 //typically 32 to 70
 * SGFLT a_wav_recip) //The the reciprocal of the wavetable's base pitch
 *
 * This uses the formula:
 * (1.0f/(sample_rate/table_length)) * osc_hz = ratio
 *
 * This avoids division in the main loop
 */
void v_osc_wav_set_unison_pitch(
    t_osc_wav_unison* a_osc_ptr,
    SGFLT a_spread,
    SGFLT a_pitch
){
    if((a_osc_ptr->voice_count) == 1)
    {
        a_osc_ptr->fm_phases[0] = 0.0f;

        a_osc_ptr->voice_inc[0] =
            f_pit_midi_note_to_hz_fast(a_pitch) * (a_osc_ptr->sr_recip);
    }
    else
    {
        if(unlikely(a_spread != (a_osc_ptr->uni_spread)))
        {
            a_osc_ptr->uni_spread = a_spread;
            a_osc_ptr->bottom_pitch = -0.5f * a_spread;
            a_osc_ptr->pitch_inc = a_spread / ((SGFLT)(a_osc_ptr->voice_count));
        }

        int i;

        for(i = 0; i < a_osc_ptr->voice_count; ++i){
            a_osc_ptr->fm_phases[i] = 0.0f;

            a_osc_ptr->voice_inc[i] = f_pit_midi_note_to_hz_fast(
                a_pitch +
                a_osc_ptr->bottom_pitch +
                (a_osc_ptr->pitch_inc * (SGFLT)i)
            ) * a_osc_ptr->sr_recip;
        }
    }

}

void v_osc_wav_apply_fm(
    t_osc_wav_unison* a_osc_ptr,
    SGFLT a_signal,
    SGFLT a_amt
){
    int i;
    SGFLT f_amt = a_signal * a_amt;

    if(f_amt != 0.0f)
    {
        for(i = 0; i < a_osc_ptr->voice_count; ++i){
            a_osc_ptr->fm_phases[i] += f_amt;
        }
    }
}

void v_osc_wav_apply_fm_direct(
    t_osc_wav_unison* a_osc_ptr,
    SGFLT a_signal,
    SGFLT a_amt
){
    int i;
    SGFLT f_amt = a_signal * a_amt;

    if(f_amt != 0.0f)
    {
        for(i = 0; i < a_osc_ptr->voice_count; ++i){
            a_osc_ptr->osc_cores[i].output += f_amt;
        }
    }
}

/*Return zero if the oscillator is turned off.  A function pointer should
point here if the oscillator is turned off.*/
SGFLT f_osc_wav_run_unison_off(
    t_osc_wav_unison * a_osc_ptr
){
    return 0.0f;
}

/* SGFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr)
 *
 * Returns one sample of an oscillator's output
 */
SGFLT f_osc_wav_run_unison(
    t_osc_wav_unison * a_osc_ptr
){
    int i;
    a_osc_ptr->current_sample = 0.0f;

    for(i = 0; i < a_osc_ptr->voice_count; ++i){
        v_run_osc(
            &a_osc_ptr->osc_cores[i],
            a_osc_ptr->voice_inc[i]
        );

        a_osc_ptr->fm_phases[i] += a_osc_ptr->osc_cores[i].output;

        while(a_osc_ptr->fm_phases[i] < 0.0f)
        {
            a_osc_ptr->fm_phases[i] += 1.0f;
        }

        while(a_osc_ptr->fm_phases[i] > 1.0f)
        {
            a_osc_ptr->fm_phases[i] -= 1.0f;
        }

        a_osc_ptr->current_sample += f_cubic_interpolate_ptr_wrap(
            a_osc_ptr->selected_wavetable,
            a_osc_ptr->selected_wavetable_sample_count,
            a_osc_ptr->fm_phases[i] *
            a_osc_ptr->selected_wavetable_sample_count_SGFLT
        );
    }

    return (a_osc_ptr->current_sample) * (a_osc_ptr->adjusted_amp);
}

void v_osc_wav_run_unison_core_only(
    t_osc_wav_unison * a_osc_ptr
){
    int i;
    a_osc_ptr->current_sample = 0.0f;

    for(i = 0; i < a_osc_ptr->voice_count; ++i){
        v_run_osc(
            &a_osc_ptr->osc_cores[i],
            a_osc_ptr->voice_inc[i]
        );
    }
}

/*Resync the oscillators at note_on to hopefully avoid phasing artifacts*/
void v_osc_wav_note_on_sync_phases(
    t_osc_wav_unison * a_osc_ptr
){
    int i;

    if(a_osc_ptr->voice_count == 1){
        a_osc_ptr->osc_cores[0].output = 0.0;
    } else {
        for(i = 0; i < a_osc_ptr->voice_count; ++i){
            a_osc_ptr->osc_cores[i].output = a_osc_ptr->phases[i];
        }
    }
}

t_osc_wav * g_osc_get_osc_wav(){
    t_osc_wav * f_result = (t_osc_wav*)malloc(sizeof(t_osc_wav));

    f_result->inc = 0.0f;
    f_result->last_pitch = 20.0f;
    f_result->output = 0.0f;

    return f_result;
}

void g_osc_init_osc_wav_unison(
    t_osc_wav_unison * f_result,
    SGFLT a_sample_rate,
    int voice_num
){
    v_osc_wav_set_uni_voice_count(
        f_result,
        OSC_UNISON_MAX_VOICES
    );
    f_result->sr_recip = 1.0f / a_sample_rate;
    f_result->adjusted_amp = 1.0f;
    f_result->bottom_pitch = -0.1f;
    f_result->current_sample = 0.0f;
    f_result->pitch_inc = 0.1f;
    f_result->uni_spread = 0.1f;
    f_result->voice_count = 1;

    int f_i;

    for(f_i = 0; f_i < OSC_UNISON_MAX_VOICES; ++f_i){
        g_init_osc_core(&f_result->osc_cores[f_i]);
        //f_result->osc_wavs[f_i] =
    }

    v_osc_wav_set_unison_pitch(
        f_result,
        .5f,
        60.0f + (1.01234 * (float)voice_num)
    );

    for(f_i = 0; f_i < OSC_UNISON_MAX_VOICES; ++f_i){
        // Prevent phasing artifacts from the oscillators starting at
        // the same phase.
        f_result->phases[f_i] =
            f_result->osc_cores[f_i].output =
                OSC_CORE_PHASES[voice_num][f_i];
        f_result->fm_phases[f_i] = 0.0f;
    }

    v_osc_wav_set_unison_pitch(f_result, .2f, 60.0f);

    f_result->selected_wavetable = 0;
    f_result->selected_wavetable_sample_count = 0;
    f_result->selected_wavetable_sample_count_SGFLT = 0.0f;

}

t_osc_wav_unison * g_osc_get_osc_wav_unison(
    SGFLT a_sample_rate,
    int voice_num
){
    t_osc_wav_unison * f_result = (t_osc_wav_unison*)malloc(
        sizeof(t_osc_wav_unison)
    );

    g_osc_init_osc_wav_unison(
        f_result,
        a_sample_rate,
        voice_num
    );

    return f_result;
}


