#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/delay/multi_comb_filter.h"


/* v_mcm_run(
 * t_mcm_multicomb*,
 * SGFLT input value (audio sample, -1 to 1, typically)
 * );
 * This runs the filter.  You can then use the output sample in your plugin*/
void v_mcm_run(t_mcm_multicomb* a_cmb_ptr,SGFLT a_value)
{
    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] = a_value;
    a_cmb_ptr->output_sample = 0.0f;

    int f_i = 0;

    while(f_i < a_cmb_ptr->comb_count)
    {
        a_cmb_ptr->delay_pointer =
            (a_cmb_ptr->input_pointer) - (a_cmb_ptr->delay_samples[f_i]);

        if((a_cmb_ptr->delay_pointer) < 0.0f){
            a_cmb_ptr->delay_pointer =
                (a_cmb_ptr->delay_pointer) + (a_cmb_ptr->buffer_size);
        }

        a_cmb_ptr->wet_sample = f_linear_interpolate_ptr_wrap(
            a_cmb_ptr->input_buffer,
            a_cmb_ptr->buffer_size,
            a_cmb_ptr->delay_pointer
        );

        a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] +=
                ((a_cmb_ptr->wet_sample) * (a_cmb_ptr->feedback_linear));

        a_cmb_ptr->output_sample += (a_cmb_ptr->wet_sample);

        ++f_i;
    }

    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] *=
            (a_cmb_ptr->volume_recip);
    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] =
        f_remove_denormal(a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)]);
    a_cmb_ptr->input_pointer = (a_cmb_ptr->input_pointer) + 1;

    if(a_cmb_ptr->input_pointer >= a_cmb_ptr->buffer_size){
        a_cmb_ptr->input_pointer = 0;
    }
}

/*v_mcm_set(
 * t_mcm_multicomb*,
 * SGFLT feedback (decibels -20 to 0)
 * SGFLT pitch (midi note number, 20 to 120),
 * SGFLT a_spread);
 *
 * Sets all parameters of the comb filters.
 */
void v_mcm_set(
    t_mcm_multicomb* a_cmb_ptr,
    SGFLT a_feedback_db,
    SGFLT a_midi_note_number,
    SGFLT a_spread
){
    /*Set feedback_linear, but only if it's changed since last time*/
    if((a_cmb_ptr->feedback_db) != a_feedback_db){
        if(a_feedback_db > -0.1f){
            a_cmb_ptr->feedback_db = -0.1f;
        } else {
            a_cmb_ptr->feedback_db = a_feedback_db;
        }

        // * -1;  //negative feedback, gives a comb-ier sound
        a_cmb_ptr->feedback_linear = f_db_to_linear_fast(
            a_cmb_ptr->feedback_db
        );
    }

    if(
        (a_cmb_ptr->midi_note_number != a_midi_note_number)
        ||
        (a_cmb_ptr->spread != a_spread)
    ){
        a_cmb_ptr->midi_note_number = a_midi_note_number;
        a_cmb_ptr->spread = a_spread;
        SGFLT f_note = a_midi_note_number;
        int f_i;
        for(f_i = 0; f_i < a_cmb_ptr->comb_count; ++f_i){
            a_cmb_ptr->delay_samples[f_i] = f_pit_midi_note_to_samples(
                f_note,
                a_cmb_ptr->sr
            );
            f_note += a_spread;
        }
    }

}

/* t_mcm_multicomb * g_mcm_get(
 * int a_comb_count,
 * SGFLT a_sr) //sample rate
 */
t_mcm_multicomb * g_mcm_get(int a_comb_count, SGFLT a_sr)
{
    t_mcm_multicomb * f_result;

    lmalloc((void**)&f_result, sizeof(t_mcm_multicomb));

    //Allocate enough memory to accommodate 20hz filter frequency
    f_result->buffer_size = (int)((a_sr / 20.0f) + 300);

    hpalloc(
        (void**)(&(f_result->input_buffer)),
        sizeof(SGFLT) * (f_result->buffer_size)
    );

    int f_i;

    for(f_i = 0; f_i < (f_result->buffer_size); ++f_i){
        f_result->input_buffer[f_i] = 0.0f;
    }

    f_result->input_pointer = 0;
    f_result->delay_pointer = 0;
    f_result->wet_sample = 0.0f;
    f_result->output_sample = 0.0f;
    f_result->feedback_db = -6.0f;
    f_result->feedback_linear = 0.5f;
    f_result->midi_note_number = 60.0f;

    f_result->volume_recip = 1.0f/(SGFLT)a_comb_count;

    lmalloc((void**)&f_result->delay_samples, sizeof(SGFLT) * a_comb_count);

    for(f_i = 0; f_i < a_comb_count; ++f_i){
        f_result->delay_samples[f_i] = 150.0f + (SGFLT)f_i;
    }

    f_result->sr = a_sr;
    //f_result->linear = g_lin_get();
    //f_result->pitch_core = g_pit_get();
    f_result->comb_count = a_comb_count;

    v_mcm_set(f_result, -1.0f, 66.0f, 1.0f);
    v_mcm_run(f_result, 0.0f);

    return f_result;
}

