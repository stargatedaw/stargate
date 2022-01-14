#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/delay/delay.h"


void v_dly_set_delay_seconds(
    t_delay_simple* a_dly,
    t_delay_tap* a_tap,
    SGFLT a_seconds
){
    if((a_tap->delay_seconds) != a_seconds){
        a_tap->delay_seconds = a_seconds;
        a_tap->delay_samples = (int)((a_dly->sample_rate) * a_seconds);
    }
}

/*
 * This must be run if running the tap as linear, otherwise you will segfault
 */
void v_dly_set_delay_lin(
    t_delay_simple* a_dly,
    t_delay_tap* a_tap,
    SGFLT a_seconds
){
    if((a_tap->delay_seconds) != a_seconds){
        a_tap->delay_seconds = a_seconds;
        a_tap->delay_samples = (int)((a_dly->sample_rate) * a_seconds);
        a_tap->fraction = ((a_dly->sample_rate) * a_seconds) -
            (a_tap->delay_samples);
    }
}


/*
 * a_beats //Delay time in beats.  Typical value:  .25, .5, 1, 2....
 */
void v_dly_set_delay_tempo(
    t_delay_simple* a_dly,
    t_delay_tap* a_tap,
    SGFLT a_beats
){
    if((a_tap->delay_beats) != a_beats){
        a_tap->delay_beats = a_beats;
        a_tap->delay_samples = (a_dly->tempo_recip) * a_beats *
            (a_dly->sample_rate);
    }
}

/*void v_dly_set_delay_pitch(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * SGFLT a_pitch)  //Pitch in MIDI note number
 *
 * This method is very slow because it calculates a more accurate result
 * that the fast method, it should only be used in things like reverbs, where
 * feedback and pitch are tightly coupled together, and
 * require accuracy.
 */
void v_dly_set_delay_pitch(
    t_delay_simple* a_dly,
    t_delay_tap* a_tap,
    SGFLT a_pitch
){
    if((a_tap->delay_pitch) != a_pitch)
    {
        a_tap->delay_pitch = a_pitch;
        a_tap->delay_samples =
            ((a_dly->sample_rate) / (f_pit_midi_note_to_hz(a_pitch)));
    }
}



/*void v_dly_set_delay_pitch(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * SGFLT a_pitch)  //Pitch in MIDI note number
 *
 * This method is very slow because it calculates a more accurate result
 * that the fast method, it should only be used in things like reverbs,
 * where feedback and pitch are tightly coupled together, and
 * require accuracy.
 */
void v_dly_set_delay_pitch_fast(
    t_delay_simple* a_dly,
    t_delay_tap* a_tap,
    SGFLT a_pitch
){
    if((a_tap->delay_pitch) != a_pitch)
    {
        a_tap->delay_pitch = a_pitch;
        a_tap->delay_samples =
            ((a_dly->sample_rate) / (f_pit_midi_note_to_hz(a_pitch)));
    }
}


/*void v_dly_set_delay_hz(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * SGFLT a_hz)  //Frequency in hz.  1.0f/a_hz == the delay time
 *
 */
void v_dly_set_delay_hz(
    t_delay_simple* a_dly,
    t_delay_tap* a_tap,
    SGFLT a_hz
){
    if((a_tap->delay_hz) != a_hz){
        a_tap->delay_hz = a_hz;
        a_tap->delay_samples = ((a_dly->sample_rate)/(a_hz));
    }
}

void v_dly_run_delay(t_delay_simple* a_dly,SGFLT a_input){
    a_dly->buffer[(a_dly->write_head)] = f_remove_denormal(a_input);

    ++a_dly->write_head;
    if(unlikely(a_dly->write_head >= a_dly->sample_count)){
        a_dly->write_head = 0;
    }

}

void v_dly_run_tap(t_delay_simple* a_dly,t_delay_tap* a_tap){
    a_tap->read_head = (a_dly->write_head) - (a_tap->delay_samples);

    if((a_tap->read_head) < 0){
        a_tap->read_head = (a_tap->read_head) + (a_dly->sample_count);
    }

    a_tap->output = (a_dly->buffer[(a_tap->read_head)]);
}


void v_dly_run_tap_lin(t_delay_simple* a_dly,t_delay_tap* a_tap){
    a_tap->read_head = (a_dly->write_head) - (a_tap->delay_samples);

    if((a_tap->read_head) < 0){
        a_tap->read_head = (a_tap->read_head) + (a_dly->sample_count);
    }

    ++a_tap->read_head_p1;

    if(unlikely(a_tap->read_head_p1 >= a_dly->sample_count)){
        a_tap->read_head_p1 -= a_dly->sample_count;
    }

    a_tap->output = f_linear_interpolate(
        a_dly->buffer[(a_tap->read_head)],
        a_dly->buffer[(a_tap->read_head_p1)],
        a_tap->fraction
    );
}

void g_dly_init(t_delay_simple * self, SGFLT a_max_size, SGFLT a_sr){
    int f_i;
    //add 2400 samples to ensure we don't overrun our buffer
    int sample_count = (int)((a_max_size * a_sr) + 2400);
    SGFLT* buffer;

    hpalloc(
        (void**)&buffer,
        sizeof(SGFLT) * sample_count
    );

    for(f_i = 0; f_i < sample_count; ++f_i){
        buffer[f_i] = 0.0f;
    }
    g_dly_init_buffer(self, a_sr, buffer, sample_count);
}

void g_dly_init_buffer(
    t_delay_simple * self,
    SGFLT a_sr,
    SGFLT* buffer,
    int sample_count
){
    self->buffer = buffer;
    self->sample_count = sample_count;
    self->write_head = 0;
    self->sample_rate = a_sr;
    self->tempo = 999;
    self->tempo_recip = 999;
}

void g_dly_tap_init(t_delay_tap * f_result){
    f_result->read_head = 0;
    f_result->delay_samples = 0;
    f_result->delay_seconds  = 0.0f;
    f_result->delay_beats = 0.0f;
    f_result->output = 0.0f;
    f_result->delay_pitch = 20.0123f;
    f_result->delay_hz = 20.2021f;
}

t_delay_tap * g_dly_get_tap(){
    t_delay_tap * f_result;
    hpalloc((void**)&f_result, sizeof(t_delay_tap));
    g_dly_tap_init(f_result);
    return f_result;
}

