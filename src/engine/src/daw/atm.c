#include "audiodsp/lib/clip.h"
#include "daw.h"
#include "files.h"


t_daw_atm_sequence * g_daw_atm_sequence_get(t_daw * self, int song_uid){
    int f_i2;
    t_daw_atm_sequence * f_result = NULL;
    t_daw_atm_plugin * current_plugin = NULL;
    t_daw_atm_port * current_port = NULL;
    t_daw_atm_point * f_point = NULL;
    t_daw_atm_point * last_point = NULL;

#if SG_OS == _OS_WINDOWS
    SGPATHSTR f_file[1024] = L"\0";
#else
    SGPATHSTR f_file[1024] = "\0";
#endif
    sg_path_snprintf(
        f_file,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls%i",
#else
        "%s%i",
#endif
        self->automation_folder,
        song_uid
    );

    if(i_file_exists(f_file)){
        lmalloc((void**)&f_result, sizeof(t_daw_atm_sequence));

        for(f_i2 = 0; f_i2 < MAX_PLUGIN_POOL_COUNT; ++f_i2)
        {
            f_result->plugins[f_i2].port_count = 0;
            f_result->plugins[f_i2].ports = NULL;
        }

        t_2d_char_array * f_current_string = g_get_2d_array_from_file(
            f_file, XLARGE_STRING); //TODO:  1MB big enough???

        int f_pos = 0;
        /* Port position in the array, since port num does not map
         * to array index. */
        int f_port_pos = 0;
        int f_plugin_uid = -1;

        while(1){
            v_iterate_2d_char_array(f_current_string);
            if(f_current_string->eof)
            {
                break;
            }

            if(f_current_string->current_str[0] == 'p')
            {
                v_iterate_2d_char_array(f_current_string);
                f_plugin_uid = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_port_count = atoi(f_current_string->current_str);

                //sanity check
                sg_assert(
                    f_port_count >= 1 && f_port_count < 100000,
                    "g_daw_atm_sequence_get: port count %i is not in "
                    "range 1 to 180000",
                    f_port_count
                );

                current_plugin = &f_result->plugins[f_plugin_uid];
                current_plugin->port_count = f_port_count;

                lmalloc(
                    (void**)&current_plugin->ports,
                    sizeof(t_daw_atm_port) * f_port_count
                );

                for(f_i2 = 0; f_i2 < f_port_count; ++f_i2){
                    current_plugin->ports[f_i2].atm_pos = 0;
                    current_plugin->ports[f_i2].point_count = 0;
                    current_plugin->ports[f_i2].points = NULL;
                    current_plugin->ports[f_i2].port = -1;
                    current_plugin->ports[f_i2].last_val = 0.0f;
                }

                f_pos = 0;
                f_port_pos = 0;
            } else if(f_current_string->current_str[0] == 'q'){
                v_iterate_2d_char_array(f_current_string);
                int f_port_num = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_point_count = atoi(f_current_string->current_str);

                //sanity check
                sg_assert(
                    f_point_count >= 1 && f_point_count < 100000,
                    "g_daw_atm_sequence_get: point count %i not in "
                    "range 1 to 100000",
                    f_point_count
                );
                sg_assert(
                    f_port_pos < current_plugin->port_count,
                    "g_daw_atm_sequence_get: port pos %i > %i",
                    f_port_pos,
                    current_plugin->port_count
                );
                current_port = &current_plugin->ports[f_port_pos];

                current_port->port = f_port_num;
                current_port->point_count = f_point_count;
                lmalloc(
                    (void**)&current_port->points,
                    sizeof(t_daw_atm_point) * f_point_count
                );
                ++f_port_pos;
                f_pos = 0;
            } else {
                double f_beat = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_port = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                SGFLT f_val = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_index = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_plugin = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_break_after = atoi(f_current_string->current_str);

                /* Automation curve, this isn't actually implemented yet
                   , but I'm adding it to the file format to avoid having
                   to do hackery later to preserve backwards compatibility
                */
                v_iterate_2d_char_array(f_current_string);

                sg_assert(
                    f_port == current_port->port,
                    "g_daw_atm_sequence_get: port %i != current port %i",
                    f_port,
                    current_port->port
                );
                sg_assert(
                    f_pos < current_port->point_count,
                    "g_daw_atm_sequence_get: point pos %i >= %i",
                    f_pos,
                    current_port->point_count
                );
                sg_assert_ptr(
                    current_port->points,
                    "g_daw_atm_sequence_get: current port has no points"
                );
                sg_assert(
                    f_break_after == 0 || f_break_after == 1,
                    "g_daw_atm_sequence_get: invalid f_break_after value %i",
                    f_break_after
                );

                f_point = &current_port->points[f_pos];

                f_point->beat = f_beat;
                f_point->tick = (int)(
                    (f_beat / SG_AUTOMATION_RESOLUTION) + 0.5f
                );
                f_point->port = f_port;
                f_point->val = f_val;
                f_point->index = f_index;
                f_point->plugin = f_plugin;
                f_point->break_after = f_break_after;

                if(f_pos == current_port->point_count - 1){
                    f_point->recip = 0.0f;
                }

                if(f_pos > 0){
                    last_point = &current_port->points[f_pos - 1];
                    last_point->recip =
                        1.0f / (f_point->beat - last_point->beat);
                }

                ++f_pos;
            }
        }

        g_free_2d_char_array(f_current_string);
    }

    return f_result;
}

void v_daw_atm_sequence_free(t_daw_atm_sequence * self){
    int f_i, f_i2;
    t_daw_atm_plugin * current_plugin = NULL;
    t_daw_atm_port * current_port = NULL;

    for(f_i = 0; f_i < MAX_PLUGIN_TOTAL_COUNT; ++f_i){
        current_plugin = &self->plugins[f_i];

        if(current_plugin->ports)
        {
            for(f_i2 = 0; f_i2 < current_plugin->port_count; ++f_i2)
            {
                current_port = &self->plugins[f_i].ports[f_i2];

                if(current_port->points)
                {
                    free(current_port->points);
                }
            }

            free(current_plugin->ports);
        }
    }

    free(self);
}

void v_daw_process_atm(
    t_daw * self,
    int f_track_num,
    t_plugin * f_plugin,
    int sample_count,
    int a_playback_mode,
    t_daw_thread_storage * a_ts
){
    int f_i, f_i2;
    t_track * f_track = self->track_pool[f_track_num];
    t_atm_tick * tick;
    t_daw_atm_port * current_port;

    int f_pool_index = f_plugin->pool_uid;

    f_plugin->atm_count = 0;

    if(a_ts->playback_mode == PLAYBACK_MODE_OFF){
        return;
    }

    if(
        !self->overdub_mode
        &&
        a_playback_mode == 2
        &&
        f_track->extern_midi
    ){
        return;
    }

    if(!self->en_song->sequences_atm){
        return;
    }
    t_daw_atm_plugin * f_current_item =
        &self->en_song->sequences_atm->plugins[f_pool_index];

    if(!f_current_item->port_count){
        return;
    }

    for(f_i = 0; f_i < a_ts->atm_tick_count; ++f_i){
        tick = &a_ts->atm_ticks[f_i];

        for(f_i2 = 0; f_i2 < f_current_item->port_count; ++f_i2){
            current_port = &f_current_item->ports[f_i2];

            while(1){
                t_daw_atm_point * f_point =
                    &current_port->points[current_port->atm_pos];
                t_daw_atm_point * next_point = NULL;

                int is_last_tick =
                    current_port->atm_pos == (current_port->point_count - 1);

                if(
                    !is_last_tick
                    &&
                    f_point->tick < tick->tick
                    &&
                    tick->tick
                    >=
                    current_port->points[current_port->atm_pos + 1].tick
                ){
                    ++current_port->atm_pos;
                    continue;
                }

                t_seq_event * f_buff_ev =
                    &f_plugin->atm_buffer[f_plugin->atm_count];
                SGFLT val;

                if(
                    is_last_tick
                    ||
                    f_point->break_after
                    || (
                        current_port->atm_pos == 0
                        &&
                        tick->tick < f_point->tick
                    ) ||
                    tick->tick == f_point->tick
                ){
                    val = f_point->val;
                } else {
                    next_point =
                        &current_port->points[current_port->atm_pos + 1];
                    SGFLT interpolate_pos =
                        (tick->beat - f_point->beat)
                        // / (next_point->beat - f_point->beat);
                        * f_point->recip;
                    val = f_linear_interpolate(
                        f_point->val,
                        next_point->val,
                        interpolate_pos
                    );
                }
                val = fclip(val, 0.0, 127.0);

                if(
                    f_plugin->uid == f_point->plugin
                    &&
                    (current_port->last_val != val || a_ts->is_first_period)
                ){
                    current_port->last_val = val;
                    SGFLT f_val = f_atm_to_ctrl_val(
                        f_plugin->descriptor,
                        f_point->port,
                        val
                    );
                    v_ev_clear(f_buff_ev);
                    v_ev_set_atm(f_buff_ev, f_point->port, f_val);
                    f_buff_ev->tick = tick->sample;
                    v_set_control_from_atm(
                        f_buff_ev,
                        f_plugin->pool_uid,
                        f_track
                    );
                    ++f_plugin->atm_count;
                }

                break;
            }
        }
    }

    f_plugin->atm_list->len = f_plugin->atm_count;
    for(f_i = 0; f_i < f_plugin->atm_count; ++f_i){
        f_plugin->atm_list->data[f_i] = &f_plugin->atm_buffer[f_i];
    }

    shds_list_isort(f_plugin->atm_list, seq_event_cmpfunc);
}

