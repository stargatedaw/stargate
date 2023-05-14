#include <pthread.h>

#include "stargate.h"
#include "daw.h"
#include "files.h"


void v_daw_set_is_soloed(t_daw * self){
    int f_i;
    self->is_soloed = 0;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        if(self->track_pool[f_i]->solo){
            self->is_soloed = 1;
            break;
        }
    }
}

void v_daw_set_loop_mode(t_daw * self, int a_mode){
    self->loop_mode = a_mode;
}

/* void v_daw_set_playback_mode(t_data * self,
 * int a_mode, //
 * int a_sequence, //The sequence index to start playback on
 * int a_bar) //The bar index (with a_sequence) to start playback on
 */
void v_daw_set_playback_mode(
    t_daw * self,
    int a_mode,
    double a_beat,
    int a_lock
){
    stop_preview();
    switch(a_mode)
    {
        case 0: //stop
        {
            int f_i = 0;
            int f_i2;
            t_track * f_track;
            int f_old_mode = STARGATE->playback_mode;

            if(a_lock)
            {
                pthread_spin_lock(&STARGATE->main_lock);
            }

            self->ts[0].suppress_new_audio_items = 1;

            STARGATE->playback_mode = a_mode;

            f_i = 0;

            t_plugin * f_plugin;

            while(f_i < DN_TRACK_COUNT)
            {
                f_i2 = 0;
                f_track = self->track_pool[f_i];

                f_track->period_event_index = 0;

                while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
                {
                    f_plugin = f_track->plugins[f_i2];
                    if(f_plugin)
                    {
                        f_plugin->descriptor->on_stop(f_plugin->plugin_handle);
                    }
                    ++f_i2;
                }

                f_track->item_event_index = 0;

                ++f_i;
            }

            if(a_lock)
            {
                pthread_spin_unlock(&STARGATE->main_lock);
            }

            if(f_old_mode == PLAYBACK_MODE_REC)
            {
                v_stop_record_audio();
            }

        }
            break;
        case 1:  //play
        {
            if(a_lock)
            {
                pthread_spin_lock(&STARGATE->main_lock);
            }

            v_daw_set_playback_cursor(self, a_beat);
            STARGATE->playback_mode = a_mode;
            DAW->ts[0].is_first_period = 1;
            self->ts[0].suppress_new_audio_items = 0;

            if(a_lock)
            {
                pthread_spin_unlock(&STARGATE->main_lock);
            }

            break;
        }
        case 2:  //record
            if(STARGATE->playback_mode == PLAYBACK_MODE_REC)
            {
                return;
            }

            v_prepare_to_record_audio();

            if(a_lock)
            {
                pthread_spin_lock(&STARGATE->main_lock);
            }

            v_daw_set_playback_cursor(self, a_beat);
            STARGATE->playback_mode = a_mode;
            DAW->ts[0].is_first_period = 1;
            self->ts[0].suppress_new_audio_items = 0;

            if(a_lock)
            {
                pthread_spin_unlock(&STARGATE->main_lock);
            }
            break;
    }
}

void v_daw_set_playback_cursor(t_daw * self, double a_beat)
{
    //self->current_sequence = a_sequence;
    self->ts[0].ml_current_beat = a_beat;
    self->ts[0].ml_next_beat = a_beat;
    t_daw_sequence * f_sequence = self->en_song->sequences;

    v_sg_set_playback_pos(
        &f_sequence->events,
        a_beat,
        self->ts[0].current_sample
    );

    int f_i;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        self->track_pool[f_i]->item_event_index = 0;
        if((self->is_soloed && !self->track_pool[f_i]->solo) ||
            (self->track_pool[f_i]->mute))
        {
            self->track_pool[f_i]->fade_state = FADE_STATE_FADED;
        }

        f_sequence->tracks[f_i].pos = 0;
    }

    f_i = 0;
}

int metronome_list_count(t_sg_seq_event_list * self){
    int result = 0;
    t_sg_seq_event* ev;
    for(int i = 0; i < self->count; ++i){
        ev = &self->events[i];
        if(ev->type == SEQ_EVENT_TEMPO_CHANGE){
            result = ev->beat;
        }
    }
    return result + 1000;
}

void metronome_beats_populate(
    struct MetronomeList* self, 
    t_sg_seq_event_list* events,
    int len_beats
){
    int beat = 0;
    int beat_count = 0;
    t_sg_seq_event* ev;
    t_sg_seq_event* ev_next;
    t_sg_seq_event* tempo_events[events->count];
    int tempo_events_count = 0;

    for(int i = 0; i < events->count; ++i){
        ev = &events->events[i];
        if(ev->type == SEQ_EVENT_TEMPO_CHANGE){
            tempo_events[tempo_events_count] = ev;
            ++tempo_events_count;
        }
    }

    // corner case of only 1 marker, ensure it is set
    ev_next = tempo_events[0];  

    for(int i = 1; i < tempo_events_count; ++i){
        ev = tempo_events[i - 1];
        ev_next = tempo_events[i];
        beat_count = ev->tsig.num;
        while(beat < ev_next->beat){
            for(int k = 0; k < beat_count && beat < ev_next->beat; ++k){
                self->beats[beat] = (struct MetronomeBeat){
                    .downbeat = (k == 0) ? 1: 0, 
                    .beat = (SGFLT)beat,
                };
                ++beat;
            }
        }
    }

    beat_count = ev_next->tsig.num;

    // Last marker gets 1000 beats of metronome
    for(; beat < len_beats;){
        for(int k = 0; k < beat_count && beat < len_beats; ++k){
            self->beats[beat] = (struct MetronomeBeat){
                .downbeat = (k == 0) ? 1: 0,
                .beat = (SGFLT)beat,
            };
            ++beat;
        }
    }
}

void metronome_list_factory(
    struct MetronomeList* self, 
    t_sg_seq_event_list* events
){
    int len_beats = metronome_list_count(events);
    lmalloc(
        (void**)&self->beats, 
        sizeof(struct MetronomeBeat) * len_beats
    );
    self->len = len_beats;
    metronome_beats_populate(self, events, len_beats);
}

t_daw_sequence * g_daw_sequence_get(t_daw* self, int uid){
    t_daw_sequence * f_result;
    int f_item_counters[DN_TRACK_COUNT];
    lmalloc((void**)&f_result, sizeof(t_daw_sequence));

    g_sg_seq_event_list_init(&f_result->events);

    int f_i = 0;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        f_result->tracks[f_i].refs = NULL;
        f_result->tracks[f_i].count = 0;
        f_result->tracks[f_i].pos = 0;
        f_item_counters[f_i] = 0;
    }

    SGPATHSTR f_full_path[TINY_STRING];
    sg_path_snprintf(
        f_full_path,
        TINY_STRING,
#if SG_OS == _OS_WINDOWS
        L"%ls/songs/%i",
#else
        "%s/songs/%i",
#endif
        self->project_folder,
        uid
    );

    t_2d_char_array * f_current_string = g_get_2d_array_from_file(
        f_full_path,
        LARGE_STRING
    );

    int f_ev_pos = 0;

    while(1){
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof){
            break;
        }

        char f_key = f_current_string->current_str[0];

        if(f_key == 'N'){  // name
            v_iterate_2d_char_array_to_next_line(f_current_string);
            continue;
        } else if(f_key == 'C'){
            v_iterate_2d_char_array(f_current_string);
            int f_track_num = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);

            f_result->tracks[f_track_num].count = atoi(
                f_current_string->current_str
            );

            sg_assert(
                !f_result->tracks[f_track_num].refs,
                "g_daw_sequence_get: track already has refs"
            );

            lmalloc(
                (void**)&f_result->tracks[f_track_num].refs,
                f_result->tracks[f_track_num].count * sizeof(t_daw_item_ref)
            );
        }
        else if(f_current_string->current_str[0] == 'M')  //marker count
        {
            sg_assert(
                !f_result->events.events,
                "g_daw_sequence_get: already has events"
            );
            v_iterate_2d_char_array(f_current_string);
            f_result->events.count = atoi(f_current_string->current_str);

            lmalloc(
                (void**)&f_result->events.events,
                sizeof(t_sg_seq_event) * f_result->events.count
            );
        } else if(f_current_string->current_str[0] == 'E'){  //sequencer event
            sg_assert_ptr(
                f_result->events.events,
                "g_daw_sequence_get: no events"
            );
            v_iterate_2d_char_array(f_current_string);
            int f_type = atoi(f_current_string->current_str);

            if(f_type == SEQ_EVENT_MARKER){  //the engine ignores these
                v_iterate_2d_char_array(f_current_string);  //beat
                //Marker text
                v_iterate_2d_char_array_to_next_line(f_current_string);
                continue;
            }

            t_sg_seq_event * f_ev = &f_result->events.events[f_ev_pos];
            ++f_ev_pos;

            f_ev->type = f_type;
            v_iterate_2d_char_array(f_current_string);
            f_ev->beat = atof(f_current_string->current_str);

            if(f_ev->type == SEQ_EVENT_LOOP){
                v_iterate_2d_char_array(f_current_string);
                f_ev->start_beat = atof(f_current_string->current_str);
            } else if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE){
                v_iterate_2d_char_array(f_current_string);
                f_ev->tempo = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int tsig_num = atoi(f_current_string->current_str);
                f_ev->tsig.num = tsig_num;

                v_iterate_2d_char_array(f_current_string);
                int tsig_den = atoi(f_current_string->current_str);
                f_ev->tsig.den = tsig_den;

                // TODO: Is this correct?
                f_ev->tempo *= ((float)tsig_den / 4.0);
            }
        } else {  //item reference
            int f_track_num = atoi(f_current_string->current_str);

            sg_assert_ptr(
                f_result->tracks[f_track_num].refs,
                "g_daw_sequence_get: no refs"
            );

            t_daw_item_ref * f_item_ref =
                &f_result->tracks[f_track_num].refs[
                    f_item_counters[f_track_num]];

            sg_assert(
                f_item_counters[f_track_num]
                <
                f_result->tracks[f_track_num].count,
                "g_daw_sequence_get: track counter %i >= %i",
                f_item_counters[f_track_num],
                f_result->tracks[f_track_num].count
            );

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->start = atof(f_current_string->current_str);

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->length = atof(f_current_string->current_str);

            f_item_ref->end = f_item_ref->start + f_item_ref->length;

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->item_uid = atoi(f_current_string->current_str);

            if(!DAW->item_pool[f_item_ref->item_uid])
            {
                g_daw_item_get(DAW, f_item_ref->item_uid);
            }

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->start_offset = atof(f_current_string->current_str);

            ++f_item_counters[f_track_num];
        }
    }
    metronome_list_factory(&f_result->metronome, &f_result->events);

    g_free_2d_char_array(f_current_string);

    //v_assert_memory_integrity(self);

    return f_result;
}


NO_OPTIMIZATION void v_daw_open_tracks(){
    SGPATHSTR f_file_name[1024];
    sg_path_snprintf(
        f_file_name,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/projects/daw/tracks.txt",
#else
        "%s/projects/daw/tracks.txt",
#endif
        STARGATE->project_folder
    );

    if(i_file_exists(f_file_name))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
            f_file_name,
            LARGE_STRING
        );

        while(1){
            v_iterate_2d_char_array(f_2d_array);

            if(f_2d_array->eof){
                break;
            }

            int f_track_index = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_solo = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array(f_2d_array);
            int f_mute = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array(f_2d_array);  //ignored
            v_iterate_2d_char_array(f_2d_array); //ignored

            // Important: If adding new field here, they will need to be
            // copied within daw_track_reload(), as the new tracks will
            // not automatically pick up the values

            sg_assert(
                f_track_index >= 0 && f_track_index < DN_TRACK_COUNT,
                "v_daw_open_tracks: track index %i out of range 0 to %i",
                f_track_index,
                DN_TRACK_COUNT
            );
            sg_assert(
                f_solo == 0 || f_solo == 1,
                "v_daw_open_tracks: invalid solo value: %i",
                f_solo
            );
            sg_assert(
                f_mute == 0 || f_mute == 1,
                "v_daw_open_tracks: invalid mute value: %i",
                f_mute
            );

            v_open_track(
                DAW->track_pool[f_track_index],
                DAW->tracks_folder,
                f_track_index
            );

            DAW->track_pool[f_track_index]->solo = f_solo;
            DAW->track_pool[f_track_index]->mute = f_mute;
        }

        g_free_2d_char_array(f_2d_array);
    } else {  //ensure everything is closed...
        int f_i;

        for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
            DAW->track_pool[f_i]->solo = 0;
            DAW->track_pool[f_i]->mute = 0;
            v_open_track(
                DAW->track_pool[f_i],
                DAW->tracks_folder,
                f_i
            );
        }
    }
}

void sequence_free(t_daw_sequence* self){
    if(!self || USE_HUGEPAGES){
        return;
    }
    if(self->metronome.beats){
        free(self->metronome.beats);
    }
    if(self->events.events){
        free(self->events.events);
    }
    free(self);
}

void sequence_atm_free(t_daw_atm_sequence* self){
    if(!self || USE_HUGEPAGES){
        return;
    }
    // TODO: Free the other pointers
    for(int i = 0; i < MAX_PLUGIN_POOL_COUNT; ++i){
        if(self->plugins[i].ports){
            free(self->plugins[i].ports);
        }
    }
    free(self);
}

void v_daw_song_free(t_daw_song* self){
    if(self->sequences){
    }
    if(self->sequences_atm){
        // TODO
    }
}

// Only called during start up.  This function has a number of issues,
// should eventually replace it completely and re-evaluate the start up
// sequence
void g_daw_song_get(t_daw* self, int a_lock){
    t_daw_song f_result;

    f_result.sequences_atm = g_daw_atm_sequence_get(self, 0);
    // Assumed to already be loaded
    f_result.sequences = self->song_pool[0].sequences;

    //t_daw_song * f_old = self->en_song;

    if(a_lock){
        pthread_spin_lock(&STARGATE->main_lock);
    }

    self->song_pool[0] = f_result;
    self->en_song = &self->song_pool[0];

    if(a_lock){
        pthread_spin_unlock(&STARGATE->main_lock);
    }

    //if(f_old){
    //    v_daw_song_free(f_old);
    //}
}

void v_daw_set_time_params(t_daw * self, int sample_count){
    self->ts[0].ml_sample_period_inc_beats =
        ((self->ts[0].playback_inc) * ((SGFLT)(sample_count)));
    self->ts[0].ml_current_beat =
        self->ts[0].ml_next_beat;
    self->ts[0].ml_next_beat = self->ts[0].ml_current_beat +
        self->ts[0].ml_sample_period_inc_beats;
}


