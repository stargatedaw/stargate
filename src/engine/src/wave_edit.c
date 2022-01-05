/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/


#include "stargate.h"
#include "wave_edit.h"
#include "csv/1d.h"
#include "files.h"

t_wave_edit * wave_edit;

void g_wave_edit_get(){
    SGFLT f_sample_rate = STARGATE->thread_storage[0].sample_rate;
    clalloc((void**)&wave_edit, sizeof(t_wave_edit));
    wave_edit->ab_wav_item = 0;
    wave_edit->ab_audio_item = g_audio_item_get(f_sample_rate);
    wave_edit->tracks_folder = (char*)malloc(sizeof(char) * 1024);
    wave_edit->project_folder = (char*)malloc(sizeof(char) * 1024);
    int f_i = 0;
    while(f_i < 1)
    {
        wave_edit->track_pool[f_i] = g_track_get(f_i, f_sample_rate);
        ++f_i;
    }
}

void v_we_set_playback_mode(
    t_wave_edit * self,
    int a_mode,
    int a_lock
){
    stop_preview();
    switch(a_mode)
    {
        case 0: //stop
        {
            int f_old_mode = STARGATE->playback_mode;

            if(a_lock)
            {
                pthread_spin_lock(&STARGATE->main_lock);
            }

            STARGATE->playback_mode = a_mode;

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

            if(wave_edit->ab_wav_item)
            {
                v_ifh_retrigger(
                    &wave_edit->ab_audio_item->sample_read_heads[0],
                    wave_edit->ab_audio_item->sample_start_offset);
                v_adsr_retrigger(&wave_edit->ab_audio_item->adsrs[0]);
                v_svf_reset(&wave_edit->ab_audio_item->lp_filters[0]);
            }

            STARGATE->playback_mode = a_mode;

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

            STARGATE->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&STARGATE->main_lock);
            }
            break;
        default:
            sg_assert(
                0,
                "v_we_set_playback_mode: invalid playback mode %i",
                a_mode
            );
            break;
    }
}

void v_we_export(t_wave_edit * self, const char * a_file_out){
    pthread_spin_lock(&STARGATE->main_lock);
    STARGATE->is_offline_rendering = 1;
    pthread_spin_unlock(&STARGATE->main_lock);

    SGFLT f_sample_rate = STARGATE->thread_storage[0].sample_rate;

    long f_size = 0;
    long f_block_size = (STARGATE->sample_count);

    SGFLT * f_output = NULL;
    lmalloc((void**)&f_output, sizeof(SGFLT) * (f_block_size * 2));

    SGFLT ** f_buffer = NULL;
    lmalloc((void**)&f_buffer, sizeof(SGFLT*) * 2);

    int f_i = 0;
    while(f_i < 2)
    {
        lmalloc((void**)&f_buffer[f_i], sizeof(SGFLT) * f_block_size);
        ++f_i;
    }

    v_we_set_playback_mode(self, PLAYBACK_MODE_PLAY, 0);

    log_info("\nOpening SNDFILE with sample rate %f", f_sample_rate);

    SF_INFO f_sf_info;
    f_sf_info.channels = 2;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = (int)(f_sample_rate);

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    log_info("Successfully opened SNDFILE");

#if SG_OS == _OS_LINUX
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    while((self->ab_audio_item->sample_read_heads[0].whole_number) <
            (self->ab_audio_item->sample_end_offset))
    {
        int f_i = 0;
        f_size = 0;

        while(f_i < f_block_size)
        {
            f_buffer[0][f_i] = 0.0f;
            f_buffer[1][f_i] = 0.0f;
            ++f_i;
        }

        v_run_wave_editor(f_block_size, f_buffer, NULL);

        f_i = 0;
        /*Interleave the samples...*/
        while(f_i < f_block_size)
        {
            f_output[f_size] = f_buffer[0][f_i];
            ++f_size;
            f_output[f_size] = f_buffer[1][f_i];
            ++f_size;
            ++f_i;
        }

        sg_write_audio(f_sndfile, f_output, f_block_size);
    }

#if SG_OS == _OS_LINUX

    clock_gettime(CLOCK_REALTIME, &f_finish);

    v_print_benchmark("v_offline_render ", f_start, f_finish);
    log_info("f_size = %ld", f_size);

#endif

    v_we_set_playback_mode(self, PLAYBACK_MODE_OFF, 0);

    sf_close(f_sndfile);

    free(f_buffer[0]);
    free(f_buffer[1]);
    free(f_output);

    char f_tmp_finished[1024];

    sprintf(f_tmp_finished, "%s.finished", a_file_out);

    v_write_to_file(f_tmp_finished, "finished");

    pthread_spin_lock(&STARGATE->main_lock);
    STARGATE->is_offline_rendering = 0;
    pthread_spin_unlock(&STARGATE->main_lock);

#if SG_OS == _OS_LINUX
    chown_file(a_file_out);
#endif

}


void v_set_we_file(t_wave_edit * self, const char * a_uid){
    int uid = atoi(a_uid);

    t_audio_pool_item * f_result = g_audio_pool_get_item_by_uid(
        STARGATE->audio_pool,
        uid
    );

    if(
        f_result->is_loaded
        ||
        i_audio_pool_item_load(f_result, 1)
    ){
        pthread_spin_lock(&STARGATE->main_lock);

        self->ab_wav_item = f_result;

        self->ab_audio_item->ratio = self->ab_wav_item->ratio_orig;

        pthread_spin_unlock(&STARGATE->main_lock);
    } else {
        log_info("i_audio_pool_item_load failed in v_set_we_file");
    }
}

void v_we_open_tracks(){
    v_open_track(wave_edit->track_pool[0], wave_edit->tracks_folder, 0);
}

void v_we_open_project(){
    sprintf(wave_edit->project_folder, "%s%sprojects%swave_edit",
        STARGATE->project_folder, PATH_SEP, PATH_SEP);

    sprintf(wave_edit->tracks_folder, "%s%stracks",
        wave_edit->project_folder, PATH_SEP);
    v_we_open_tracks();
}

void v_set_wave_editor_item(
    t_wave_edit * self,
    const char * a_val
){
    t_2d_char_array * f_current_string = g_get_2d_array(MEDIUM_STRING);
    sprintf(f_current_string->array, "%s", a_val);
    t_audio_item * f_old = self->ab_audio_item;
    t_audio_item * f_result = g_audio_item_load_single(
        STARGATE->thread_storage[0].sample_rate,
        f_current_string,
        0,
        0,
        self->ab_wav_item
    );

    pthread_spin_lock(&STARGATE->main_lock);
    self->ab_audio_item = f_result;
    pthread_spin_unlock(&STARGATE->main_lock);

    g_free_2d_char_array(f_current_string);
    if(f_old){
        v_audio_item_free(f_old);
    }
}


void v_run_wave_editor(
    int sample_count,
    SGFLT **output,
    SGFLT * a_input
){
    int sent_stop = 0;
    t_wave_edit * self = wave_edit;
    t_plugin * f_plugin;

    int f_global_track_num = 0;
    t_track * f_track = self->track_pool[f_global_track_num];
    int f_i;

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        output[0][f_i] = 0.0f;
        output[1][f_i] = 0.0f;
    }

    if(a_input)
    {
        for(f_i = 0; f_i < AUDIO_INPUT_TRACK_COUNT; ++f_i)
        {
            v_audio_input_run(f_i, output, NULL, a_input, sample_count, NULL);
        }
    }

    if(STARGATE->playback_mode == PLAYBACK_MODE_PLAY)
    {
        for(f_i = 0; f_i < sample_count; ++f_i)
        {
            if(
                self->ab_audio_item->sample_read_heads[0].whole_number
                <
                self->ab_audio_item->sample_end_offset
            ){
                v_adsr_run(&self->ab_audio_item->adsrs[0]);
                v_audio_item_set_fade_vol(
                    self->ab_audio_item,
                    0,
                    &STARGATE->thread_storage[0]
                );

                if(self->ab_wav_item->channels == 1)
                {
                    SGFLT f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                        self->ab_wav_item->samples[0],
                        self->ab_audio_item->sample_read_heads[0].whole_number,
                        self->ab_audio_item->sample_read_heads[0].fraction
                    ) *
                    self->ab_audio_item->adsrs[0].output *
                    self->ab_audio_item->vols_linear[0] *
                    self->ab_audio_item->fade_vols[0];

                    output[0][f_i] = f_tmp_sample;
                    output[1][f_i] = f_tmp_sample;
                }
                else if(self->ab_wav_item->channels > 1)
                {
                    output[0][f_i] = f_cubic_interpolate_ptr_ifh(
                        self->ab_wav_item->samples[0],
                        self->ab_audio_item->sample_read_heads[0].whole_number,
                        self->ab_audio_item->sample_read_heads[0].fraction
                    ) *
                    self->ab_audio_item->adsrs[0].output *
                    self->ab_audio_item->vols_linear[0] *
                    self->ab_audio_item->fade_vols[0];

                    output[1][f_i] = f_cubic_interpolate_ptr_ifh(
                    (self->ab_wav_item->samples[1]),
                    (self->ab_audio_item->sample_read_heads[0].whole_number),
                    (self->ab_audio_item->sample_read_heads[0].fraction)) *
                    (self->ab_audio_item->adsrs[0].output) *
                    (self->ab_audio_item->vols_linear[0]) *
                    (self->ab_audio_item->fade_vols[0]);
                }

                v_ifh_run(
                    &self->ab_audio_item->sample_read_heads[0],
                    self->ab_audio_item->ratio
                );

                if(
                    STARGATE->playback_mode != PLAYBACK_MODE_PLAY
                    &&
                    self->ab_audio_item->adsrs[0].stage < ADSR_STAGE_RELEASE
                ){
                    v_adsr_release(&self->ab_audio_item->adsrs[0]);
                }
            } else {
                if(!sent_stop){
                    sent_stop = 1;
                    v_we_set_playback_mode(
                        self,
                        PLAYBACK_MODE_OFF,
                        0
                    );
                    v_queue_osc_message("stop", "");
                }
            }
        }
    }

    SGFLT ** f_buff = f_track->buffers;

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        f_buff[0][f_i] = output[0][f_i];
        f_buff[1][f_i] = output[1][f_i];
    }

    for(f_i = 0; f_i < MAX_PLUGIN_COUNT; ++f_i)
    {
        f_plugin = f_track->plugins[f_i];
        if(f_plugin && f_plugin->power)
        {
            f_plugin->descriptor->run_replacing(
                f_plugin->plugin_handle,
                sample_count,
                f_track->event_list,
                f_plugin->atm_list
            );
        }
    }

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        output[0][f_i] = f_buff[0][f_i];
        output[1][f_i] = f_buff[1][f_i];
    }

    v_pkm_run(
        f_track->peak_meter,
        f_buff[0],
        f_buff[1],
        STARGATE->sample_count
    );
}

void v_we_osc_send(t_osc_send_data * a_buffers){
    int f_i;

    f_i = 0;
    t_pkm_peak_meter * f_pkm = wave_edit->track_pool[0]->peak_meter;
    sprintf(
        a_buffers->f_tmp1,
        "%i:%f:%f",
        f_i,
        f_pkm->value[0],
        f_pkm->value[1]
    );
    v_pkm_reset(f_pkm);

    v_queue_osc_message("peak", a_buffers->f_tmp1);

    if(STARGATE->playback_mode == 1)
    {
        SGFLT f_frac =
        (SGFLT)(wave_edit->ab_audio_item->sample_read_heads[
            0].whole_number)
        / (SGFLT)(wave_edit->ab_audio_item->audio_pool_item->length);

        sprintf(a_buffers->f_msg, "%f", f_frac);
        v_queue_osc_message("wec", a_buffers->f_msg);
    }

    if(STARGATE->osc_queue_index > 0)
    {
        for(f_i = 0; f_i < STARGATE->osc_queue_index; ++f_i)
        {
            strcpy(
                a_buffers->osc_queue_keys[f_i],
                STARGATE->osc_queue_keys[f_i]
            );
            strcpy(
                a_buffers->osc_queue_vals[f_i],
                STARGATE->osc_queue_vals[f_i]
            );
        }

        pthread_spin_lock(&STARGATE->main_lock);

        //Now grab any that may have been written since the previous copy

        while(f_i < STARGATE->osc_queue_index)
        {
            strcpy(a_buffers->osc_queue_keys[f_i],
                STARGATE->osc_queue_keys[f_i]);
            strcpy(a_buffers->osc_queue_vals[f_i],
                STARGATE->osc_queue_vals[f_i]);
            ++f_i;
        }

        int f_index = STARGATE->osc_queue_index;
        STARGATE->osc_queue_index = 0;

        pthread_spin_unlock(&STARGATE->main_lock);

        a_buffers->f_tmp1[0] = '\0';

        for(f_i = 0; f_i < f_index; ++f_i)
        {
            sprintf(
                a_buffers->f_tmp2, "%s|%s\n",
                a_buffers->osc_queue_keys[f_i],
                a_buffers->osc_queue_vals[f_i]
            );
            strcat(
                a_buffers->f_tmp1,
                a_buffers->f_tmp2
            );
        }

        if(!STARGATE->is_offline_rendering)
        {
            v_ui_send("stargate/wave_edit", a_buffers->f_tmp1);
        }
    }
}

void v_we_update_audio_inputs(){
    v_update_audio_inputs(wave_edit->project_folder);
}

void v_we_configure(const char* a_key, const char* a_value){
    log_info("v_we_configure:  key: \"%s\", value: \"%s\"", a_key, a_value);

    if(!strcmp(a_key, WN_CONFIGURE_KEY_LOAD_AB_OPEN)){
        v_set_we_file(wave_edit, a_value);
    } else if(!strcmp(a_key, WN_CONFIGURE_KEY_AUDIO_INPUTS)){
        v_we_update_audio_inputs();
    } else if(!strcmp(a_key, WN_CONFIGURE_KEY_WE_SET)){
        v_set_wave_editor_item(wave_edit, a_value);
    } else if(!strcmp(a_key, WN_CONFIGURE_KEY_WE_EXPORT)){
        v_we_export(wave_edit, a_value);
    } else if(!strcmp(a_key, WN_CONFIGURE_KEY_WN_PLAYBACK)){
        int f_mode = atoi(a_value);
        sg_assert(
            f_mode >= 0 && f_mode <= 2,
            "v_we_configure: WN_CONFIGURE_KEY_WN_PLAYBACK invalid mode %i",
            f_mode
        );
        v_we_set_playback_mode(wave_edit, f_mode, 1);
    } else if(!strcmp(a_key, WN_CONFIGURE_KEY_PLUGIN_INDEX)){
        t_1d_char_array * f_val_arr = c_split_str(
            a_value,
            '|',
            5,
            TINY_STRING
        );
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_index = atoi(f_val_arr->array[1]);
        int f_plugin_index = atoi(f_val_arr->array[2]);
        int f_plugin_uid = atoi(f_val_arr->array[3]);
        int f_power = atoi(f_val_arr->array[4]);

        t_track * f_track = wave_edit->track_pool[f_track_num];

        v_set_plugin_index(
            f_track, f_index, f_plugin_index, f_plugin_uid, f_power, 1);

        g_free_1d_char_array(f_val_arr);
    } else {
        log_info("Unknown configure message key: %s, value %s", a_key, a_value);
    }
}

void v_we_test(){
    log_info("Begin Wave-Next test");

    STARGATE->sample_count = 512;

    v_set_host(SG_HOST_WAVE_EDIT);
    v_we_set_playback_mode(wave_edit, PLAYBACK_MODE_REC, 0);
    SGFLT * f_output_arr[2];

    int f_i, f_i2;

    for(f_i = 0; f_i < 2; ++f_i)
    {
        hpalloc((void**)&f_output_arr[f_i], sizeof(SGFLT) * 1024);

        for(f_i2 = 0; f_i2 < 1024; ++f_i2)
        {
            f_output_arr[f_i][f_i2] = 0.0f;
        }
    }

    SGFLT * f_input_arr;
    hpalloc((void**)&f_input_arr, sizeof(SGFLT) * (1024 * 1024));

    for(f_i = 0; f_i < (1024 * 1024); ++f_i)
    {
        f_input_arr[f_i] = 0.0f;
    }

    for(f_i = 0; f_i < 100000; ++f_i)
    {
        v_run_wave_editor(512, f_output_arr, f_input_arr);
    }

    v_we_set_playback_mode(wave_edit, PLAYBACK_MODE_OFF, 0);

    log_info("End Wave-Next test");
}


