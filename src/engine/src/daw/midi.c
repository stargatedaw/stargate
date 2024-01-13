#include <string.h>

#include "stargate.h"
#include "daw.h"
#include "files.h"

struct DawMidiQwertyDevice QWERTY_MIDI = {};

void v_daw_set_midi_devices(){
#ifndef NO_MIDI
    SGPATHSTR f_path[2048];
    int f_i, f_i2;
    int found_device;
    t_midi_device * f_device;
    char name[1024];

    if(!STARGATE->midi_devices){
        return;
    }

    sg_path_snprintf(
        f_path,
        2048,
#if SG_OS == _OS_WINDOWS
        L"%ls/projects/daw/midi_routing.txt",
#else
        "%s/projects/daw/midi_routing.txt",
#endif
        STARGATE->project_folder
    );

    if(!i_file_exists(f_path)){
#if SG_OS == _OS_WINDOWS
        log_warn(
            "Did not find MIDI device config file '%ls', not "
            "loading MIDI devices",
            f_path
        );
#else
        log_warn(
            "Did not find MIDI device config file '%s', not "
            "loading MIDI devices",
            f_path
        );
#endif
        return;
    }

    t_2d_char_array * f_current_string = g_get_2d_array_from_file(
        f_path,
        LARGE_STRING
    );

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof){
            break;
        }

        int f_on = atoi(f_current_string->current_str);

        v_iterate_2d_char_array(f_current_string);
        int f_track_num = atoi(f_current_string->current_str);

        v_iterate_2d_char_array(f_current_string);  // name
        strncpy(name, f_current_string->current_str, 1023);
        name[1023] = '\0';

        int channel = 0;
        // TODO Stargate v2: Remove if statement
        if(!f_current_string->eol){
            v_iterate_2d_char_array(f_current_string);
            channel = atoi(f_current_string->current_str);
        }

        //v_iterate_2d_char_array_to_next_line(f_current_string);

        found_device = 0;
        for(f_i2 = 0; f_i2 < STARGATE->midi_devices->count; ++f_i2){
            f_device = &STARGATE->midi_devices->devices[f_i2];
            if(!strcmp(name, f_device->name)){
                v_daw_set_midi_device(f_on, f_i2, f_track_num, channel);
                found_device = 1;
                break;
            }
        }
        if(!found_device){
            log_warn(
                "Did not find MIDI device '%s' in %i devices",
                f_current_string->current_str,
                STARGATE->midi_devices->count
            );
        }
    }

    g_free_2d_char_array(f_current_string);

#endif

}


#ifndef NO_MIDI

void v_daw_set_midi_device(
    int a_on,
    int a_device,
    int a_output,
    int channel
){
    log_info(
        "v_daw_set_midi_device: %i %i %i %i",
        a_on,
        a_device,
        a_output,
        channel
    );
    t_daw * self = DAW;
    /* Interim logic to get a minimum viable product working
     * TODO:  Make it modular and able to support multiple devices
     */
    t_daw_midi_routing_list * f_list = &self->midi_routing;
    t_midi_routing * f_route = &f_list->routes[a_device];
    t_track * f_track_old = NULL;
    t_track * f_track_new = self->track_pool[a_output];

    if(f_route->output_track != -1){
        f_track_old = self->track_pool[f_route->output_track];
    }

    if(
        f_track_old
        && (
            !f_route->on
            ||
            f_route->output_track != a_output
        )
    ){
        log_info(
            "v_daw_set_midi_device: Disabling midi device on track %i",
            f_track_old->track_num
        );
        f_track_old->extern_midi = 0;
        f_track_old->extern_midi_count = &ZERO;
        f_track_old->midi_device = 0;
    }

    f_route->on = a_on;
    f_route->output_track = a_output;
    f_route->channel = channel;

    if(f_route->on && STARGATE->midi_devices->devices[a_device].loaded){
        log_info(
            "v_daw_set_midi_device: Enabling midi device on track %i",
            f_track_new->track_num
        );
        f_track_new->midi_device = &STARGATE->midi_devices->devices[a_device];
        f_track_new->extern_midi =
            STARGATE->midi_devices->devices[a_device].instanceEventBuffers;
        f_track_new->midi_device->route = f_route;

        midiPoll(f_track_new->midi_device);
        midiDeviceRead(
            f_track_new->midi_device,
            STARGATE->thread_storage[0].sample_rate,
            512
        );

        STARGATE->midi_devices->devices[a_device].instanceEventCounts = 0;
        STARGATE->midi_devices->devices[a_device].midiEventReadIndex = 0;
        STARGATE->midi_devices->devices[a_device].midiEventWriteIndex = 0;

        f_track_new->extern_midi_count =
            &STARGATE->midi_devices->devices[a_device].instanceEventCounts;
    } else {
        log_info(
            "v_daw_set_midi_device: Disabling midi device on track %i",
            f_track_new->track_num
        );
        f_track_new->extern_midi = 0;
        f_track_new->extern_midi_count = &ZERO;
        f_track_new->midi_device = 0;
    }
}

#endif

void daw_process_qwerty_midi(
    t_daw * self,
    t_track * a_track,
    int sample_count,
    int a_thread_num,
    t_daw_thread_storage * a_ts
){
    if(a_track->track_num == QWERTY_MIDI.rack_num){
        int i;
        for(i = 0; i < 128; ++i){
            if(QWERTY_MIDI.note_offs[i].sample){
                --QWERTY_MIDI.note_offs[i].sample;
                if(!QWERTY_MIDI.note_offs[i].sample){
                    t_seq_event* ev =
                        &QWERTY_MIDI.events[QWERTY_MIDI.event_count];
                    ev->note = i;
                    ev->tick = 0;
                    ev->type = EVENT_NOTEOFF;
                    ev->velocity = 0;
                    ev->channel = QWERTY_MIDI.note_offs[i].channel;
                    ++QWERTY_MIDI.event_count;
                }
            }

        }

        if(QWERTY_MIDI.event_count){
            for(i = 0; i < QWERTY_MIDI.event_count; ++i){
                shds_list_append(
                    a_track->event_list,
                    &QWERTY_MIDI.events[i]
                );
            }
            QWERTY_MIDI.event_count = 0;
            shds_list_isort(a_track->event_list, seq_event_cmpfunc);
        }
    }
}

void v_daw_process_external_midi(
    t_daw * self,
    t_track * a_track,
    int sample_count,
    int a_thread_num,
    t_daw_thread_storage * a_ts
){
    if(!a_track->midi_device){
        return;
    }

    SGFLT f_sample_rate = STARGATE->thread_storage[a_thread_num].sample_rate;
    SGFLT sr_recip = STARGATE->thread_storage[a_thread_num].sr_recip;
    int f_playback_mode = STARGATE->playback_mode;
    int f_midi_learn = STARGATE->midi_learn;
    SGFLT f_tempo = self->ts[0].tempo;

    midiPoll(a_track->midi_device);
    midiDeviceRead(a_track->midi_device, f_sample_rate, sample_count);

    int f_extern_midi_count = *a_track->extern_midi_count;
    t_seq_event * events = a_track->extern_midi;

    sg_assert(
        f_extern_midi_count < 200,
        "v_daw_process_external_midi: external midi count %i out of "
        "range 0 to 200",
        f_extern_midi_count
    );

    int f_i2 = 0;

    int f_valid_type;

    char * f_osc_msg = a_track->osc_cursor_message;

    while(f_i2 < f_extern_midi_count){
        f_valid_type = 1;

        if(events[f_i2].tick >= sample_count){
            //Otherwise the event will be missed
            events[f_i2].tick = sample_count - 1;
        }

        if(events[f_i2].type == EVENT_NOTEON){
            if(f_playback_mode == PLAYBACK_MODE_REC){
                SGFLT f_beat = a_ts->ml_current_beat +
                    f_samples_to_beat_count(
                        events[f_i2].tick,
                        f_tempo,
                        sr_recip
                    );

                sg_snprintf(
                    f_osc_msg,
                    1024,
                    "on|%f|%i|%i|%i|%ld|%i",
                    f_beat,
                    a_track->track_num,
                    events[f_i2].note,
                    events[f_i2].velocity,
                    a_ts->current_sample + events[f_i2].tick,
                    events[f_i2].channel
                );
                v_queue_osc_message("mrec", f_osc_msg);
            }

            sg_snprintf(
                f_osc_msg,
                1024,
                "1|%i",
                events[f_i2].note
            );
            v_queue_osc_message("ne", f_osc_msg);

        } else if(events[f_i2].type == EVENT_NOTEOFF){
            if(f_playback_mode == PLAYBACK_MODE_REC){
                SGFLT f_beat = a_ts->ml_current_beat +
                    f_samples_to_beat_count(
                        events[f_i2].tick,
                        f_tempo,
                        sr_recip
                    );

                sg_snprintf(
                    f_osc_msg,
                    1024,
                    "off|%f|%i|%i|%ld|%i",
                    f_beat,
                    a_track->track_num,
                    events[f_i2].note,
                    a_ts->current_sample + events[f_i2].tick,
                    events[f_i2].channel
                );
                v_queue_osc_message("mrec", f_osc_msg);
            }

            sg_snprintf(
                f_osc_msg,
                1024,
                "0|%i",
                events[f_i2].note
            );
            v_queue_osc_message("ne", f_osc_msg);
        } else if(events[f_i2].type == EVENT_PITCHBEND){
            if(f_playback_mode == PLAYBACK_MODE_REC){
                SGFLT f_beat = a_ts->ml_current_beat +
                    f_samples_to_beat_count(
                        events[f_i2].tick,
                        f_tempo,
                        sr_recip
                    );

                sg_snprintf(
                    f_osc_msg,
                    1024,
                    "pb|%f|%i|%f|%ld|%i",
                    f_beat,
                    a_track->track_num,
                    events[f_i2].value,
                    a_ts->current_sample + events[f_i2].tick,
                    events[f_i2].channel
                );
                v_queue_osc_message("mrec", f_osc_msg);
            }
        } else if(events[f_i2].type == EVENT_CONTROLLER){
            int controller = events[f_i2].param;

            if(f_midi_learn){
                STARGATE->midi_learn = 0;
                f_midi_learn = 0;
                sg_snprintf(f_osc_msg, 1024, "%i", controller);
                v_queue_osc_message("ml", f_osc_msg);
            }

            /*SGFLT f_start =
                ((self->playback_cursor) +
                ((((SGFLT)(events[f_i2].tick)) / ((SGFLT)sample_count))
                * (self->playback_inc))) * 4.0f;*/
            v_set_control_from_cc(&events[f_i2], a_track);

            if(f_playback_mode == PLAYBACK_MODE_REC){
                SGFLT f_beat = a_ts->ml_current_beat +
                    f_samples_to_beat_count(
                        events[f_i2].tick,
                        f_tempo,
                        sr_recip
                    );

                sg_snprintf(
                    f_osc_msg,
                    1024,
                    "cc|%f|%i|%i|%f|%ld|%i",
                    f_beat,
                    a_track->track_num,
                    controller,
                    events[f_i2].value,
                    a_ts->current_sample + events[f_i2].tick,
                    events[f_i2].channel
                );
                v_queue_osc_message("mrec", f_osc_msg);
            }
        } else {
            f_valid_type = 0;
        }

        if(f_valid_type){
            shds_list_append(a_track->event_list, &events[f_i2]);
        }

        ++f_i2;
    }

    shds_list_isort(a_track->event_list, seq_event_cmpfunc);
}

void v_daw_process_note_offs(
    t_daw * self,
    int f_i,
    t_daw_thread_storage * a_ts
){
    int midi_channels[MIDI_CHANNEL_COUNT] = {};
    t_track * f_track = self->track_pool[f_i];
    long f_current_sample = a_ts->current_sample;
    long f_next_current_sample = a_ts->f_next_current_sample;

    int f_i2;
    int i, j;
    int channel;
    long note_off;
    long sample_count = f_next_current_sample - f_current_sample;

    for(i = 0; i < MAX_PLUGIN_COUNT; ++i){
        if(!f_track->plugins[i]){
            continue;
        }
        channel = f_track->plugins[i]->midi_channel;
        if(midi_channels[channel]){
            continue;
        }
        midi_channels[channel] = 1;
        if(channel == 16){
            for(j = 0; j < MIDI_CHANNEL_COUNT; ++j){
                if(midi_channels[j] && j != 16){
                    continue;
                }
                midi_channels[j] = 1;
                for(f_i2 = 0; f_i2 < MIDI_NOTE_COUNT; ++f_i2){
                    note_off = f_track->note_offs[j][f_i2];
                    if(
                        // f_note_off >= f_current_sample
                        note_off != -1
                        &&
                        note_off < f_next_current_sample
                    ){
                        t_seq_event * f_event =
                            &f_track->event_buffer[f_track->period_event_index];
                        v_ev_clear(f_event);

                        v_ev_set_noteoff(f_event, j, f_i2, 0);
                        f_event->tick = note_off - f_current_sample;
                        if(f_event->tick < 0){
                            f_event->tick = 0;
                        } else if(f_event->tick >= sample_count){
                            f_event->tick = sample_count - 1;
                        }
                        ++f_track->period_event_index;
                        f_track->note_offs[j][f_i2] = -1;

                        shds_list_append(f_track->event_list, f_event);
                    }
                }

            }
        } else {
            for(f_i2 = 0; f_i2 < MIDI_NOTE_COUNT; ++f_i2){
                note_off = f_track->note_offs[channel][f_i2];
                if(
                    // f_note_off >= f_current_sample
                    note_off != -1
                    &&
                    note_off < f_next_current_sample
                ){
                    t_seq_event * f_event =
                        &f_track->event_buffer[f_track->period_event_index];
                    v_ev_clear(f_event);

                    v_ev_set_noteoff(f_event, channel, f_i2, 0);
                    f_event->tick = note_off - f_current_sample;
                    if(f_event->tick < 0){
                        f_event->tick = 0;
                    } else if(f_event->tick >= sample_count){
                        f_event->tick = sample_count - 1;
                    }
                    ++f_track->period_event_index;
                    f_track->note_offs[channel][f_i2] = -1;

                    shds_list_append(f_track->event_list, f_event);
                }
                note_off = f_track->note_offs[16][f_i2];
                if(
                    // f_note_off >= f_current_sample
                    note_off != -1
                    &&
                    note_off < f_next_current_sample
                ){
                    t_seq_event * f_event =
                        &f_track->event_buffer[f_track->period_event_index];
                    v_ev_clear(f_event);

                    v_ev_set_noteoff(f_event, 16, f_i2, 0);
                    f_event->tick = note_off - f_current_sample;
                    if(f_event->tick < 0){
                        f_event->tick = 0;
                    } else if(f_event->tick >= sample_count){
                        f_event->tick = sample_count - 1;
                    }
                    ++f_track->period_event_index;
                    f_track->note_offs[16][f_i2] = -1;

                    shds_list_append(f_track->event_list, f_event);
                }
            }
        }
    }
    shds_list_isort(f_track->event_list, seq_event_cmpfunc);
}

void v_daw_process_midi(
    t_daw* self,
    t_daw_item_ref* a_item_ref,
    int a_track_num,
    int sample_count,
    int a_playback_mode,
    long a_current_sample,
    t_daw_thread_storage* a_ts
){
    t_daw_item * f_current_item;
    double f_adjusted_start;
    int f_i;
    t_track * f_track = self->track_pool[a_track_num];

    double f_track_current_period_beats = (a_ts->ml_current_beat);
    double f_track_next_period_beats = (a_ts->ml_next_beat);
    double f_track_beats_offset = 0.0f;

    if(
        !self->overdub_mode
        &&
        a_playback_mode == 2
        &&
        f_track->extern_midi
    ){
        // pass
    } else if(a_playback_mode > 0){
        while(1){
            f_current_item = self->item_pool[a_item_ref->item_uid];

            if(f_track->item_event_index >= f_current_item->event_count){
                break;
            }

            t_seq_event * f_event =
                &f_current_item->events[f_track->item_event_index];

            f_adjusted_start = f_event->start + a_item_ref->start -
                a_item_ref->start_offset;

            if(f_adjusted_start < f_track_current_period_beats){
                ++f_track->item_event_index;
                continue;
            }

            if(
                f_adjusted_start >= f_track_current_period_beats
                &&
                f_adjusted_start < f_track_next_period_beats
                &&
                f_adjusted_start < a_item_ref->end
            ){
                if(f_event->type == EVENT_NOTEON){
                    int f_note_sample_offset = 0;
                    double f_note_start_diff =
                        f_adjusted_start - f_track_current_period_beats +
                        f_track_beats_offset;
                    double f_note_start_frac = f_note_start_diff /
                        a_ts->ml_sample_period_inc_beats;
                    f_note_sample_offset =  (int)(f_note_start_frac *
                        ((SGFLT)sample_count));

                    if(
                        f_track->note_offs[f_event->channel][f_event->note]
                        >=
                        a_current_sample
                    ){
                        t_seq_event * f_buff_ev;

                        /*There's already a note_off scheduled ahead of
                         * this one, process it immediately to avoid
                         * hung notes*/
                        f_buff_ev = &f_track->event_buffer[
                            f_track->period_event_index
                        ];
                        v_ev_clear(f_buff_ev);
                        v_ev_set_noteoff(
                            f_buff_ev,
                            f_event->channel,
                            f_event->note,
                            0
                        );
                        f_buff_ev->tick = f_note_sample_offset;
                        ++f_track->period_event_index;
                    }
                    if(
                        f_track->note_offs[16][f_event->note]
                        >=
                        a_current_sample
                    ){
                        t_seq_event * f_buff_ev;

                        /*There's already a note_off scheduled ahead of
                         * this one, process it immediately to avoid
                         * hung notes*/
                        f_buff_ev = &f_track->event_buffer[
                            f_track->period_event_index
                        ];
                        v_ev_clear(f_buff_ev);
                        v_ev_set_noteoff(
                            f_buff_ev,
                            16,
                            f_event->note,
                            0
                        );
                        f_buff_ev->tick = f_note_sample_offset;
                        ++f_track->period_event_index;
                    }

                    t_seq_event * f_buff_ev =
                        &f_track->event_buffer[f_track->period_event_index];

                    v_ev_clear(f_buff_ev);

                    v_ev_set_noteon(
                        f_buff_ev,
                        f_event->channel,
                        f_event->note,
                        f_event->velocity,
                        f_event->pan,
                        f_event->attack,
                        f_event->decay,
                        f_event->sustain,
                        f_event->release,
                        f_event->pitch_fine
                    );

                    f_buff_ev->tick = f_note_sample_offset;

                    ++f_track->period_event_index;

                    long sample = a_current_sample + (
                        (int)(f_event->length * a_ts->samples_per_beat)
                    );
                    f_track->note_offs[f_event->channel][f_event->note] =
                        sample;
                } else if(f_event->type == EVENT_CONTROLLER){
                    int controller = f_event->param;

                    t_seq_event * f_buff_ev =
                        &f_track->event_buffer[f_track->period_event_index];

                    int f_note_sample_offset = 0;

                    double f_note_start_diff =
                        ((f_adjusted_start) - f_track_current_period_beats) +
                        f_track_beats_offset;
                    double f_note_start_frac = f_note_start_diff /
                        a_ts->ml_sample_period_inc_beats;
                    f_note_sample_offset =
                        (int)(f_note_start_frac * ((SGFLT)sample_count));

                    v_ev_clear(f_buff_ev);

                    v_ev_set_controller(
                        f_buff_ev,
                        f_event->channel,
                        controller,
                        f_event->value
                    );

                    v_set_control_from_cc(f_buff_ev, f_track);

                    f_buff_ev->tick = f_note_sample_offset;

                    ++f_track->period_event_index;
                } else if(f_event->type == EVENT_PITCHBEND){
                    int f_note_sample_offset = 0;
                    double f_note_start_diff = ((f_adjusted_start) -
                        f_track_current_period_beats) + f_track_beats_offset;
                    double f_note_start_frac = f_note_start_diff /
                        a_ts->ml_sample_period_inc_beats;
                    f_note_sample_offset =  (int)(f_note_start_frac *
                        ((SGFLT)sample_count));

                    t_seq_event * f_buff_ev =
                        &f_track->event_buffer[f_track->period_event_index];

                    v_ev_clear(f_buff_ev);
                    v_ev_set_pitchbend(
                        f_buff_ev,
                        f_event->channel,
                        f_event->value
                    );
                    f_buff_ev->tick = f_note_sample_offset;

                    ++f_track->period_event_index;
                }

                ++f_track->item_event_index;
            } else {
                break;
            }
        }
    }

    for(f_i = 0; f_i < f_track->period_event_index; ++f_i){
        shds_list_append(f_track->event_list, &f_track->event_buffer[f_i]);
    }
}

