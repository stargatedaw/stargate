#include "stargate.h"
#include "daw.h"


void v_daw_process_track(
    t_daw * self,
    int a_global_track_num,
    int a_thread_num,
    int a_sample_count,
    int a_playback_mode,
    t_daw_thread_storage * a_ts
){
    int f_i, f_i2;
    double f_current_beat, f_next_beat;
    t_pytrack * f_track = self->track_pool[a_global_track_num];
    t_daw_track_seq * f_seq =
        &self->en_song->sequences->tracks[a_global_track_num];
    int f_item_ref_count = 0;
    int f_item_ref_index = 0;
    t_daw_item_ref * f_item_ref[3] = {NULL, NULL, NULL};
    t_plugin * f_plugin;

    if(a_ts->is_looping)
    {
        f_seq->pos = 0;
    }

    while(1)
    {
        if(!f_seq->refs)
        {
            break;
        }

        f_item_ref_index = f_seq->pos + f_item_ref_count;
        if(f_item_ref_index >= f_seq->count ||
        f_seq->refs[f_item_ref_index].start > a_ts->ml_next_beat)
        {
            break;
        }

        if(f_item_ref_count == 0)
        {
            if(f_seq->refs[f_item_ref_index].end > a_ts->ml_current_beat)
            {
                f_item_ref[f_item_ref_count] = &f_seq->refs[f_item_ref_index];
                ++f_item_ref_count;
            }
            else if(f_seq->refs[f_seq->pos].end <= a_ts->ml_current_beat)
            {
                ++f_seq->pos;
            }
            else
            {
                break;
            }
        }
        else if(f_item_ref_count == 1)
        {
            if(f_seq->refs[f_item_ref_index].start < a_ts->ml_next_beat)
            {
                if(f_seq->refs[f_item_ref_index].start ==
                        f_seq->refs[f_seq->pos].end)
                {
                    f_item_ref[f_item_ref_count] =
                        &f_seq->refs[f_item_ref_index];
                    ++f_item_ref_count;
                }
                else
                {
                    f_item_ref[2] = &f_seq->refs[f_item_ref_index];
                    f_item_ref_count = 3;
                }
                break;
            }
            else
            {
                break;
            }
        }
        else
        {
            assert(0);
        }
    }

    switch(f_item_ref_count)
    {
        case 0:   //set it out of range
            f_current_beat = a_ts->ml_next_beat + 1.0f;
            f_next_beat = a_ts->ml_next_beat + 2.0f;
            break;
        case 1:
            f_current_beat = f_item_ref[0]->start;
            f_next_beat = f_item_ref[0]->end;

            if(f_current_beat >= a_ts->ml_current_beat &&
            f_current_beat < a_ts->ml_next_beat)
            {
                f_track->item_event_index = 0;
            }

            break;
        case 2:
            f_current_beat = f_item_ref[0]->end;
            f_next_beat = f_item_ref[0]->end; //f_item_ref[1]->start;
            break;
        case 3:
            f_current_beat = f_item_ref[0]->end;
            f_next_beat = f_item_ref[2]->start;
            break;
        default:
            assert(0);
    }

    v_sample_period_split(&f_track->splitter, f_track->buffers,
        f_track->sc_buffers, a_sample_count,
        a_ts->ml_current_beat, a_ts->ml_next_beat,
        f_current_beat, f_next_beat, a_ts->current_sample,
        NULL, 0);

    if(a_ts->is_looping || a_ts->is_first_period)
    {
        f_track->item_event_index = 0;
        if(f_item_ref[0])
        {
            t_daw_item * f_item = self->item_pool[f_item_ref[0]->item_uid];
            v_daw_reset_audio_item_read_heads(
                self, f_item->audio_items,
                f_item_ref[0]->start_offset +
                (a_ts->ml_current_beat - f_item_ref[0]->start));
        }

        t_daw_atm_plugin * atm_plugins = self->en_song->sequences_atm->plugins;

        if(atm_plugins)
        {
            t_daw_atm_plugin * current_atm_plugin;

            for(f_i = 0; f_i < MAX_PLUGIN_TOTAL_COUNT; ++f_i)
            {
                if(f_track->plugins[f_i])
                {
                    current_atm_plugin =
                        &atm_plugins[f_track->plugins[f_i]->pool_uid];
                    for(f_i2 = 0; f_i2 < current_atm_plugin->port_count; ++f_i2)
                    {
                        current_atm_plugin->ports[f_i2].atm_pos = 0;
                    }
                }
            }
        }
    }

    int f_is_recording = 0;
    if(a_ts->playback_mode == PLAYBACK_MODE_REC &&
       f_track->midi_device)
    {
        f_is_recording = 1;
    }

    v_daw_wait_for_bus(f_track);

    for(f_i = 0; f_i < a_ts->input_count; ++f_i)
    {
        if(a_ts->input_index[f_i] == a_global_track_num)
        {
            v_audio_input_run(f_i, f_track->buffers, f_track->sc_buffers,
                a_ts->input_buffer, a_ts->sample_count,
                &f_track->sc_buffers_dirty);
            if(a_ts->playback_mode == PLAYBACK_MODE_REC)
            {
                f_is_recording = 1;
            }
        }
    }

    if(a_ts->playback_mode == PLAYBACK_MODE_PLAY || !f_is_recording)
    {
        for(f_i = 0; f_i < f_track->splitter.count; ++f_i)
        {
            if(f_i > 0)
            {
                f_track->item_event_index = 0;
            }

            if(f_item_ref[f_i])
            {
                v_daw_process_midi(self, f_item_ref[f_i], a_global_track_num,
                    f_track->splitter.periods[f_i].sample_count,
                    a_playback_mode,
                    f_track->splitter.periods[f_i].current_sample, a_ts);
            }
        }
    }
    else
    {
        f_track->item_event_index = 0;
    }

    v_daw_process_external_midi(self, f_track, a_sample_count,
        a_thread_num, a_ts);

    v_daw_process_note_offs(self, a_global_track_num, a_ts);

    if(!f_is_recording)
    {
        for(f_i = 0; f_i < f_track->splitter.count; ++f_i)
        {
            if(f_item_ref[f_i])
            {
                if(a_playback_mode > 0 &&
                   f_item_ref[f_i]->start >= a_ts->ml_current_beat &&
                   f_item_ref[f_i]->start < a_ts->ml_next_beat)
                {
                    t_daw_item * f_item =
                        self->item_pool[f_item_ref[0]->item_uid];
                    v_daw_reset_audio_item_read_heads(
                        self, f_item->audio_items,
                        f_item_ref[0]->start_offset +
                        (a_ts->ml_current_beat - f_item_ref[0]->start));
                }

                v_daw_audio_items_run(
                    self,
                    f_item_ref[f_i],
                    a_sample_count,
                    f_track->buffers,
                    f_track->sc_buffers,
                    &f_track->sc_buffers_dirty,
                    a_ts
                );
            }
        }
    }

    for(f_i = 0; f_i < MAX_PLUGIN_COUNT; ++f_i)
    {
        f_plugin = f_track->plugins[f_i];
        if(f_plugin && f_plugin->power)
        {
            v_daw_process_atm(self, a_global_track_num,
                f_i, a_sample_count, a_playback_mode, a_ts);
            f_plugin->descriptor->run_replacing(
                f_plugin->plugin_handle, a_sample_count,
                f_track->event_list, f_plugin->atm_list);
        }
    }

    if(a_global_track_num)
    {
        v_daw_sum_track_outputs(
            self,
            f_track,
            a_sample_count,
            a_playback_mode,
            a_ts
        );
    }

    v_pkm_run(f_track->peak_meter, f_track->buffers[0],
        f_track->buffers[1], a_sample_count);

    if(a_global_track_num && !SG_OFFLINE_RENDER)
    {
        v_zero_buffer(f_track->buffers, a_sample_count);
    }

    if(f_track->sc_buffers_dirty)
    {
        f_track->sc_buffers_dirty = 0;
        v_zero_buffer(f_track->sc_buffers, a_sample_count);
    }
}

void v_daw_wait_for_bus(t_pytrack * a_track)
{
    int f_bus_count = DAW->routing_graph->bus_count[a_track->track_num];
    int f_i;

    if(a_track->track_num && f_bus_count)
    {
        for(f_i = 0; f_i < 100000000; ++f_i)
        {
            pthread_spin_lock(&a_track->lock);

            if(a_track->bus_counter <= 0)
            {
                pthread_spin_unlock(&a_track->lock);
                break;
            }

            pthread_spin_unlock(&a_track->lock);
        }

        if(f_i == 100000000)
        {
            printf("Detected deadlock waiting for bus %i\n",
                a_track->track_num);
        }

        if(a_track->bus_counter < 0)
        {
            printf("Bus %i had bus_counter < 0: %i\n",
                a_track->track_num, a_track->bus_counter);
        }
    }
}

void v_daw_sum_track_outputs(
    t_daw * self,
    t_pytrack * a_track,
    int a_sample_count,
    int a_playback_mode,
    t_daw_thread_storage * a_ts
){
    int f_bus_num;
    int f_i2;
    t_pytrack * f_bus;
    t_pytrack_routing * f_route;
    t_plugin * f_plugin = 0;
    SGFLT ** f_buff;
    SGFLT ** f_track_buff = a_track->buffers;

    if(
        !a_track->mute
        &&
        (
            !self->is_soloed
            ||
            (self->is_soloed && a_track->solo)
        )
    ){
        if(a_track->fade_state == FADE_STATE_FADED)
        {
            a_track->fade_state = FADE_STATE_RETURNING;
            v_rmp_retrigger(&a_track->fade_env, 0.1f, 1.0f);
        }
        else if(a_track->fade_state == FADE_STATE_FADING)
        {
            a_track->fade_env.output = 1.0f - a_track->fade_env.output;
            a_track->fade_state = FADE_STATE_RETURNING;
        }
    }
    else
    {
        if(a_track->fade_state == FADE_STATE_OFF)
        {
            a_track->fade_state = FADE_STATE_FADING;
            v_rmp_retrigger(&a_track->fade_env, 0.1f, 1.0f);
        }
        else if(a_track->fade_state == FADE_STATE_RETURNING)
        {
            a_track->fade_env.output = 1.0f - a_track->fade_env.output;
            a_track->fade_state = FADE_STATE_FADING;
        }
    }

    f_i2 = 0;

    if(a_track->fade_state == FADE_STATE_OFF)
    {

    }
    else if(a_track->fade_state == FADE_STATE_FADING)
    {
        while(f_i2 < a_sample_count)
        {
            f_rmp_run_ramp(&a_track->fade_env);

            f_track_buff[0][f_i2] *= (1.0f - a_track->fade_env.output);
            f_track_buff[1][f_i2] *= (1.0f - a_track->fade_env.output);
            ++f_i2;
        }

        if(a_track->fade_env.output >= 1.0f)
        {
            a_track->fade_state = FADE_STATE_FADED;
        }
    }
    else if(a_track->fade_state == FADE_STATE_RETURNING)
    {
        while(f_i2 < a_sample_count)
        {
            f_rmp_run_ramp(&a_track->fade_env);
            f_track_buff[0][f_i2] *= a_track->fade_env.output;
            f_track_buff[1][f_i2] *= a_track->fade_env.output;
            ++f_i2;
        }

        if(a_track->fade_env.output >= 1.0f)
        {
            a_track->fade_state = FADE_STATE_OFF;
        }
    }


    int f_i3;

    for(f_i3 = 0; f_i3 < MAX_ROUTING_COUNT; ++f_i3)
    {
        f_route = &self->routing_graph->routes[a_track->track_num][f_i3];

        if(!f_route->active)
        {
            continue;
        }

        f_bus_num = f_route->output;

        if(f_bus_num < 0)
        {
            continue;
        }

        f_bus = self->track_pool[f_bus_num];

        if(f_route->type == ROUTE_TYPE_MIDI){
            for(f_i2 = 0; f_i2 < a_track->event_list->len; ++f_i2){
                shds_list_append(
                    f_bus->event_list,
                    a_track->event_list->data[f_i2]
                );
            }

            pthread_spin_lock(&f_bus->lock);
            --f_bus->bus_counter;
            pthread_spin_unlock(&f_bus->lock);

            continue;
        }

        int f_plugin_index = MAX_PLUGIN_COUNT + f_i3;

        if(a_track->plugins[f_plugin_index])
        {
            f_plugin = a_track->plugins[f_plugin_index];
        }
        else
        {
            f_plugin = 0;
        }

        if(f_route->type == ROUTE_TYPE_SIDECHAIN)
        {
            f_buff = f_bus->sc_buffers;
            f_bus->sc_buffers_dirty = 1;
        }
        else
        {
            f_buff = f_bus->buffers;
        }

        if(a_track->fade_state != FADE_STATE_FADED)
        {
            if(f_plugin && f_plugin->power)
            {
                v_daw_process_atm(self, a_track->track_num,
                    f_plugin_index, a_sample_count, a_playback_mode, a_ts);

                pthread_spin_lock(&f_bus->lock);

                f_plugin->descriptor->run_mixing(
                    f_plugin->plugin_handle, a_sample_count,
                    f_buff, 2, a_track->event_list, f_plugin->atm_list);
            }
            else
            {
                pthread_spin_lock(&f_bus->lock);

                v_buffer_mix(a_sample_count, f_track_buff, f_buff);
            }
        }
        else
        {
            pthread_spin_lock(&f_bus->lock);
        }

        --f_bus->bus_counter;
        pthread_spin_unlock(&f_bus->lock);
    }
}

