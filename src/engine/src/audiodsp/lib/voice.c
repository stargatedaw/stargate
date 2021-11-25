#include <limits.h>
#include <stdlib.h>

#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/voice.h"
#include "compiler.h"


void g_voc_single_init(
    t_voc_single_voice* f_result,
    int a_voice_number
){
    f_result->voice_number = a_voice_number;
    f_result->note = -1;
    f_result->n_state = note_state_off;
    f_result->on = -1;
    f_result->off = -1;
}

void g_voc_voices_init(
    t_voc_voices* voices,
    int a_count,
    int a_thresh
){
    sg_assert(
        (int)(a_thresh < a_count),
        "a_thresh %i >= a_count %i",
        a_thresh,
        a_count
    );

    voices->count = a_count;
    voices->thresh = a_thresh;
    voices->poly_mode = POLY_MODE_RETRIG;

    hpalloc((void**)&voices->voices, sizeof(t_voc_single_voice) * a_count);

    int f_i;

    for(f_i = 0; f_i < a_count; ++f_i){
        g_voc_single_init(&voices->voices[f_i], f_i);
    }
}

t_voc_voices * g_voc_get_voices(int a_count, int a_thresh){
    t_voc_voices * f_result;
    hpalloc((void**)&f_result, sizeof(t_voc_voices));
    g_voc_voices_init(f_result, a_count, a_thresh);
    return f_result;
}

int i_get_oldest_voice(
    t_voc_voices *data,
    int a_running,
    int a_note_num
){
    int f_i;
    long oldest_tick = LONG_MAX;
    int oldest_tick_voice = -1;

    for(f_i = 0; f_i < data->count; ++f_i){
        if(a_note_num < 0 || a_note_num == data->voices[f_i].note){
            if(
                data->voices[f_i].on < oldest_tick
                &&
                data->voices[f_i].on > -1
            ){
                if(
                    !a_running
                    ||
                    data->voices[f_i].n_state != note_state_off
                ){
                    oldest_tick = data->voices[f_i].on;
                    oldest_tick_voice = f_i;
                }
            }
        }
    }

    sg_assert(
        (int)(oldest_tick_voice != -1),
        "oldest_tick_voice == -1"
    );
    return oldest_tick_voice;
}

/* int i_pick_voice(
 * t_voc_voices *data,
 * int a_current_note)
 *
 */
int i_pick_voice(
    t_voc_voices *data,
    int a_current_note,
    long a_current_sample,
    long a_tick
){
    int f_i;

    if(data->poly_mode == POLY_MODE_MONO){
        data->voices[0].on = a_current_sample + a_tick;
        data->voices[0].off = -1;
        data->voices[0].note = a_current_note;
        data->voices[0].n_state = note_state_running;
        return 0;
    } else if(data->poly_mode == POLY_MODE_MONO2){
        for(f_i = 0; f_i < data->count; ++f_i){
            if(
                data->voices[f_i].n_state == note_state_running
                ||
                data->voices[f_i].n_state == note_state_releasing
            ){
                data->voices[f_i].n_state = note_state_killed;
                data->voices[f_i].off = a_current_sample + a_tick;
            }
        }

        for(f_i = 0; f_i < data->count; ++f_i){
            if(data->voices[f_i].n_state == note_state_off){
                data->voices[f_i].note = a_current_note;
                data->voices[f_i].n_state = note_state_running;
                data->voices[f_i].on = a_current_sample + a_tick;

                return f_i;
            }
        }

        data->voices[0].note = a_current_note;
        data->voices[0].n_state = note_state_running;
        data->voices[0].on = a_current_sample + a_tick;
        return 0;
    }


    /* Look for a duplicate note */
    int f_note_count = 0;
    int f_active_count = 0;

    for(f_i = 0; f_i < data->count; ++f_i){
        //if ((data->voices[f_i].note == a_current_note) &&
        //(data->voices[f_i].n_state == note_state_running))
        if(data->voices[f_i].note == a_current_note){
            if(
                data->voices[f_i].n_state == note_state_releasing
                ||
                data->voices[f_i].n_state == note_state_running
            ){
                data->voices[f_i].n_state = note_state_killed;
                data->voices[f_i].off = a_current_sample;
                ++f_note_count;
            }
            else if(data->voices[f_i].n_state == note_state_killed){
                ++f_note_count;
            }
            //do not allow more than 2 voices for any note, at any time...
            if(f_note_count > 2){
                int f_steal_voice = i_get_oldest_voice(
                    data,
                    1,
                    a_current_note
                );
                data->voices[f_steal_voice].on = a_current_sample + a_tick;
                data->voices[f_steal_voice].note = a_current_note;
                data->voices[f_steal_voice].off = -1;
                data->voices[f_steal_voice].n_state = note_state_running;
                return f_steal_voice;
            }
        }
    }

    f_i = 0;
    /* Look for an inactive voice */
    while (f_i < (data->count))
    {
        if (data->voices[f_i].n_state == note_state_off)
        {
            data->voices[f_i].note = a_current_note;
            data->voices[f_i].n_state = note_state_running;
            data->voices[f_i].on = a_current_sample + a_tick;

            return f_i;
        }
        else
        {
            ++f_active_count;

            if(f_active_count >= data->thresh)
            {
                int f_voice_to_kill = i_get_oldest_voice(data, 1, -1);
                data->voices[f_voice_to_kill].n_state = note_state_killed;
                data->voices[f_voice_to_kill].off = a_current_sample;
                --f_active_count;
            }
        }

        ++f_i;
    }

    int oldest_tick_voice = i_get_oldest_voice(data, 0, -1);

    data->voices[oldest_tick_voice].note = a_current_note;
    data->voices[oldest_tick_voice].on = a_current_sample + a_tick;
    data->voices[oldest_tick_voice].n_state = note_state_running;
    data->voices[oldest_tick_voice].off = -1;

    return oldest_tick_voice;
}

/* void v_voc_note_off(t_voc_voices * a_voc, int a_note,
 * long a_current_sample, long a_tick)
 */
void v_voc_note_off(
    t_voc_voices* a_voc,
    int a_note,
    long a_current_sample,
    long a_tick
){
    if(a_voc->poly_mode == POLY_MODE_MONO)
    {
        //otherwise it's from an old note and should be ignored
        if(a_note == a_voc->voices[0].note)
        {
            a_voc->voices[0].n_state = note_state_releasing;
            a_voc->voices[0].off = a_current_sample + a_tick;
        }
    }
    else
    {
        int f_i = 0;

        while(f_i < (a_voc->count))
        {
            if(((a_voc->voices[f_i].note) == a_note) &&
               ((a_voc->voices[f_i].n_state) == note_state_running))
            {
                a_voc->voices[f_i].n_state = note_state_releasing;
                a_voc->voices[f_i].off = a_current_sample + a_tick;
            }
            ++f_i;
        }
    }
}

