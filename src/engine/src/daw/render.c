#include "stargate.h"
#include "daw.h"
#include "files.h"


void v_daw_offline_render(
    t_daw * self,
    double a_start_beat,
    double a_end_beat,
    char * a_file_out,
    int a_create_file,
    int a_stem,
    int sequence_uid
){
    SNDFILE * f_sndfile = NULL;
    int f_stem_count = self->routing_graph->track_pool_sorted_count;
    SNDFILE * f_stems[f_stem_count];
    char f_file[2048];

    int * f_tps = self->routing_graph->track_pool_sorted[0];

    pthread_spin_lock(&STARGATE->main_lock);
    STARGATE->is_offline_rendering = 1;
    pthread_spin_unlock(&STARGATE->main_lock);

    SGFLT f_sample_rate = STARGATE->thread_storage[0].sample_rate;

    int f_i, f_i2;
    int f_beat_total = (int)(a_end_beat - a_start_beat);

    SGFLT f_sample_count =
        self->ts[0].samples_per_beat * ((SGFLT)f_beat_total);

    long f_size = 0;
    long f_block_size = (STARGATE->sample_count);

    SGFLT * f_output = (SGFLT*)malloc(sizeof(SGFLT) * (f_block_size * 2));

    SGFLT ** f_buffer;
    lmalloc((void**)&f_buffer, sizeof(SGFLT*) * 2);

    for(f_i = 0; f_i < 2; ++f_i){
        lmalloc((void**)&f_buffer[f_i], sizeof(SGFLT) * f_block_size);
    }

    //We must set it back afterwards, or the UI will be wrong...
    int f_old_loop_mode = self->loop_mode;
    v_daw_set_loop_mode(self, DN_LOOP_MODE_OFF);
    // Must call before v_daw_set_playback_mode
    // Otherwise it is rendered from beat 0 instead of a_start_beat
    daw_set_sequence(self, sequence_uid);
    v_daw_set_playback_mode(self, PLAYBACK_MODE_PLAY, a_start_beat, 0);

    log_info("Opening SNDFILE with sample rate %i", (int)f_sample_rate);

    SF_INFO f_sf_info;
    f_sf_info.channels = 2;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = (int)(f_sample_rate);

    if(a_stem){
        for(f_i = 0; f_i < f_stem_count; ++f_i){
            snprintf(
                f_file,
                2048,
                "%s%s%i.wav",
                a_file_out,
                REAL_PATH_SEP,
                f_tps[f_i]
            );
            f_stems[f_i] = sf_open(f_file, SFM_WRITE, &f_sf_info);
            log_info("Successfully opened %s", f_file);
        }

        snprintf(f_file, 2048, "%s%s0.wav", a_file_out, REAL_PATH_SEP);
    } else {
        snprintf(f_file, 2048, "%s", a_file_out);
    }

    f_sndfile = sf_open(f_file, SFM_WRITE, &f_sf_info);
    log_info("Successfully opened SNDFILE");

#if SG_OS == _OS_LINUX
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    while(self->ts[0].ml_current_beat < a_end_beat)
    {
        for(f_i = 0; f_i < f_block_size; ++f_i)
        {
            f_buffer[0][f_i] = 0.0f;
            f_buffer[1][f_i] = 0.0f;
        }

        v_daw_run_engine(f_block_size, f_buffer, NULL);

        if(a_stem){
            for(f_i2 = 0; f_i2 < f_stem_count; ++f_i2){
                f_size = 0;
                int f_track_num = f_tps[f_i2];
                SGFLT ** f_track_buff = self->track_pool[f_track_num]->buffers;
                /*Interleave the samples...*/
                for(f_i = 0; f_i < f_block_size; ++f_i){
                    f_output[f_size] = f_track_buff[0][f_i];
                    ++f_size;
                    f_output[f_size] = f_track_buff[1][f_i];
                    ++f_size;
                }

                if(a_create_file){
                    sg_write_audio(f_stems[f_i2], f_output, f_block_size);
                }
            }
        }

        f_size = 0;
        /*Interleave the samples...*/
        for(f_i = 0; f_i < f_block_size; ++f_i){
            f_output[f_size] = f_buffer[0][f_i];
            ++f_size;
            f_output[f_size] = f_buffer[1][f_i];
            ++f_size;
        }

        if(a_create_file){
            sg_write_audio(f_sndfile, f_output, f_block_size);
        }

        v_daw_zero_all_buffers(self);
    }

#if SG_OS == _OS_LINUX

    clock_gettime(CLOCK_REALTIME, &f_finish);
    SGFLT f_elapsed = (SGFLT)v_print_benchmark(
        "v_daw_offline_render", f_start, f_finish);
    SGFLT f_realtime = f_sample_count / f_sample_rate;

    log_info("Realtime: %f", f_realtime);

    if(f_elapsed > 0.0f){
        log_info("Ratio:  %f : 1", f_realtime / f_elapsed);
    } else {
        log_info("Ratio:  infinity : 1");
    }

#endif

    v_daw_set_playback_mode(self, PLAYBACK_MODE_OFF, a_start_beat, 0);
    v_daw_set_loop_mode(self, f_old_loop_mode);

    if(a_stem){
        for(f_i2 = 0; f_i2 < f_stem_count; ++f_i2){
            sf_close(f_stems[f_i2]);
        }
    }

    sf_close(f_sndfile);

    free(f_buffer[0]);
    free(f_buffer[1]);
    free(f_buffer);
    free(f_output);

    char f_tmp_finished[1024];

    if(a_stem){
        sprintf(f_tmp_finished, "%s/finished", a_file_out);
    } else {
        sprintf(f_tmp_finished, "%s.finished", a_file_out);
    }

    v_write_to_file(f_tmp_finished, "finished");

    v_daw_panic(self);  //ensure all notes are off before returning

    pthread_spin_lock(&STARGATE->main_lock);
    STARGATE->is_offline_rendering = 0;
    pthread_spin_unlock(&STARGATE->main_lock);
}

void v_daw_offline_render_prep(t_daw * self){
    log_info("Warming up plugins for offline rendering...");
    int f_i;
    int f_i2;
    t_pytrack * f_track;
    t_plugin * f_plugin;
    SGFLT sample_rate = STARGATE->thread_storage[0].sample_rate;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        f_track = self->track_pool[f_i];
        for(f_i2 = 0; f_i2 < MAX_PLUGIN_TOTAL_COUNT; ++f_i2){
            f_plugin = f_track->plugins[f_i2];
            if(f_plugin && f_plugin->descriptor->offline_render_prep){
                f_plugin->descriptor->offline_render_prep(
                    f_plugin->plugin_handle,
                    sample_rate
                );
            }
        }
    }
    log_info("Finished warming up plugins");
}

