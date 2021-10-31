#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/filter/comb_filter.h"


/* v_cmb_run(
 * t_comb_filter*,
 * SGFLT input value (audio sample, -1 to 1, typically)
 * );
 * This runs the filter.  You can then use the output sample in your plugin*/
void v_cmb_run(t_comb_filter* a_cmb_ptr, SGFLT a_value){
    a_cmb_ptr->delay_pointer =
        a_cmb_ptr->input_pointer - a_cmb_ptr->delay_samples;

    if((a_cmb_ptr->delay_pointer) < 0.0f){
        a_cmb_ptr->delay_pointer =
            a_cmb_ptr->delay_pointer + a_cmb_ptr->buffer_size;
    }

    a_cmb_ptr->wet_sample = f_linear_interpolate_ptr_wrap(
        a_cmb_ptr->input_buffer,
        a_cmb_ptr->buffer_size,
        a_cmb_ptr->delay_pointer
    );

    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] = f_remove_denormal(
        a_value + (a_cmb_ptr->wet_sample * a_cmb_ptr->feedback_linear)
    );

    if(unlikely((a_cmb_ptr->wet_db) <= -20.0f)){
        a_cmb_ptr->output_sample = a_value;
    } else {
        a_cmb_ptr->output_sample =
            a_value + (a_cmb_ptr->wet_sample * a_cmb_ptr->wet_linear);
    }

    ++a_cmb_ptr->input_pointer;

    if(unlikely(a_cmb_ptr->input_pointer >= a_cmb_ptr->buffer_size)){
        a_cmb_ptr->input_pointer = 0;
    }
}

void v_cmb_mc_run(t_comb_filter* a_cmb_ptr, SGFLT a_value){
    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] = a_value;
    a_cmb_ptr->output_sample = a_value;

    if((a_cmb_ptr->wet_db) > -20.0f){
        int f_i;
        for(f_i = 0; f_i < MC_CMB_COUNT; ++f_i){
            a_cmb_ptr->delay_pointer =
                a_cmb_ptr->input_pointer - a_cmb_ptr->mc_delay_samples[f_i];

            if((a_cmb_ptr->delay_pointer) < 0.0f){
                a_cmb_ptr->delay_pointer =
                    a_cmb_ptr->delay_pointer + a_cmb_ptr->buffer_size;
            }

            a_cmb_ptr->wet_sample = f_linear_interpolate_ptr_wrap(
                a_cmb_ptr->input_buffer,
                a_cmb_ptr->buffer_size,
                a_cmb_ptr->delay_pointer
            );

            a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] +=
                    a_cmb_ptr->wet_sample * a_cmb_ptr->feedback_linear;

            a_cmb_ptr->output_sample +=
                a_cmb_ptr->wet_sample * a_cmb_ptr->wet_linear;
        }
    }

    ++a_cmb_ptr->input_pointer;

    if(a_cmb_ptr->input_pointer >= a_cmb_ptr->buffer_size){
        a_cmb_ptr->input_pointer = 0;
    }

    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] = f_remove_denormal(
        a_cmb_ptr->input_buffer[a_cmb_ptr->input_pointer]
    );
}

/*v_cmb_set_all(
 * t_comb_filter*,
 * SGFLT wet (decibels -20 to 0)
 * SGFLT feedback (decibels -20 to 0)
 * SGFLT pitch (midi note number, 20 to 120)
 * );
 *
 * Sets all parameters of the comb filter.
 */
void v_cmb_set_all(
    t_comb_filter* a_cmb_ptr,
    SGFLT a_wet_db,
    SGFLT a_feedback_db,
    SGFLT a_midi_note_number
){
    if((a_cmb_ptr->wet_db) != a_wet_db){
        a_cmb_ptr->wet_db = a_wet_db;
        a_cmb_ptr->wet_linear = f_db_to_linear_fast(a_wet_db);
    }

    if((a_cmb_ptr->feedback_db) != a_feedback_db){
        a_cmb_ptr->feedback_db = a_feedback_db;

        if(a_feedback_db > -0.05f){
            a_feedback_db = -0.05f;
        }

        a_cmb_ptr->feedback_linear = f_db_to_linear_fast(a_feedback_db);
    }

    if((a_cmb_ptr->midi_note_number) != a_midi_note_number){
        a_cmb_ptr->midi_note_number = a_midi_note_number;
        a_cmb_ptr->delay_samples = f_pit_midi_note_to_samples(
            a_midi_note_number,
            a_cmb_ptr->sr
        );
    }

}

void v_cmb_mc_set_all(
    t_comb_filter* a_cmb,
    SGFLT a_wet_db,
    SGFLT a_midi_note_number,
    SGFLT a_detune
){
    if(
        a_cmb->mc_detune != a_detune
        ||
        a_cmb->midi_note_number != a_midi_note_number
    ){
        a_cmb->mc_detune = a_detune;
        int f_i;

        for(f_i = 0; f_i < MC_CMB_COUNT; ++f_i){
            a_cmb->mc_delay_samples[f_i] = f_pit_midi_note_to_samples(
                a_midi_note_number + (a_detune * (SGFLT)f_i),
                a_cmb->sr
            );
        }
    }

    v_cmb_set_all(
        a_cmb,
        a_wet_db,
        a_wet_db - 13.0f,
        a_midi_note_number
    );
}

void g_cmb_init(
    t_comb_filter * f_result,
    SGFLT a_sr,
    int a_huge_pages
){
    int f_i = 0;

    //Allocate enough memory to accommodate 20hz filter frequency
    f_result->buffer_size = (int)((a_sr / 20.0f) + 300);

    if(a_huge_pages){
        hpalloc(
            (void**)(&(f_result->input_buffer)),
            sizeof(SGFLT) * (f_result->buffer_size)
        );
    } else {
        lmalloc(
            (void**)(&(f_result->input_buffer)),
            sizeof(SGFLT) * (f_result->buffer_size)
        );
    }

    for(f_i = 0; f_i < (f_result->buffer_size); ++f_i){
        f_result->input_buffer[f_i] = 0.0f;
    }

    f_result->input_pointer = 0;
    f_result->delay_pointer = 0;
    f_result->wet_sample = 0.0f;
    f_result->output_sample = 0.0f;
    f_result->wet_db = -1.0f;
    f_result->wet_linear = .75f;
    f_result->feedback_db = -6.0f;
    f_result->feedback_linear = 0.5f;
    f_result->midi_note_number = 60.0f;
    f_result->delay_samples = 150.0f;
    f_result->sr = a_sr;
    f_result->mc_detune = 999.999f;

    v_cmb_set_all(f_result,-6.0f, -6.0f, 66.0f);
    v_cmb_run(f_result, 0.0f);
}

void v_cmb_free(t_comb_filter * a_cmb){
    free(a_cmb->input_buffer);
    //free(a_cmb);
}

