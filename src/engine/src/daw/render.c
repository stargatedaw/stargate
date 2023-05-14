#include "stargate.h"
#include "daw.h"
#include "files.h"


void v_daw_offline_render(
    t_daw * self,
    double a_start_beat,
    double a_end_beat,
    SGPATHSTR* a_file_out,
    int a_create_file,
    int a_stem,
    int sequence_uid,
    int print_progress
){
    SNDFILE * f_sndfile = NULL;
    int f_stem_count = self->routing_graph->track_pool_sorted_count;
    SNDFILE * f_stems[f_stem_count];
    SGPATHSTR f_file[2048];

    int * f_tps = self->routing_graph->track_pool_sorted[0];

    pthread_spin_lock(&STARGATE->main_lock);
    STARGATE->is_offline_rendering = 1;
    pthread_spin_unlock(&STARGATE->main_lock);

    SGFLT f_sample_rate = STARGATE->thread_storage[0].sample_rate;

    int f_i, f_i2;

    long f_sample_count = 0;

    long f_size = 0;
    long f_block_size = (STARGATE->sample_count);

    SGFLT * f_output = (SGFLT*)malloc(sizeof(SGFLT) * (f_block_size * 2));

    struct SamplePair* f_buffer;

    lmalloc((void**)&f_buffer, sizeof(struct SamplePair) * f_block_size);

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
            sg_path_snprintf(
                f_file,
                2048,
#if SG_OS == _OS_WINDOWS
                L"%ls/%i.wav",
#else
                "%s/%i.wav",
#endif
                a_file_out,
                f_tps[f_i]
            );

            f_stems[f_i] = SG_SF_OPEN(f_file, SFM_WRITE, &f_sf_info);

        }

        sg_path_snprintf(
            f_file, 
            2048,
#if SG_OS == _OS_WINDOWS
            L"%ls/0.wav", 
#else
            "%s/0.wav", 
#endif
            a_file_out
        );
    } else {
        sg_path_snprintf(
            f_file, 
            2048, 
#if SG_OS == _OS_WINDOWS
            L"%ls", 
#else
            "%s", 
#endif
            a_file_out
        );
    }

    f_sndfile = SG_SF_OPEN(f_file, SFM_WRITE, &f_sf_info);
    log_info("Successfully opened SNDFILE");

#if SG_OS == _OS_LINUX
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
    int current_beat, last_beat;
    if(print_progress){
        current_beat = (int)self->ts[0].ml_current_beat;
        printf("Beat %i of %i", current_beat, (int)a_end_beat);
        last_beat = current_beat;
    }
#endif
    while(self->ts[0].ml_current_beat < a_end_beat){
#if SG_OS == _OS_LINUX
        if(print_progress){
            current_beat = (int)self->ts[0].ml_current_beat;
            if(current_beat > last_beat){
                last_beat = current_beat;
                printf("\rBeat %i of %i", current_beat, (int)a_end_beat);
                fflush(stdout);
            }
        }
#endif
        if(self->ts[0].ml_next_beat > a_end_beat){
            f_block_size = 
                (a_end_beat - self->ts[0].ml_current_beat)
                /
                (self->ts[0].ml_next_beat - self->ts[0].ml_current_beat);
            if(f_block_size <= 0){
                break;
            }
        }

        for(f_i = 0; f_i < f_block_size; ++f_i){
            f_buffer[f_i].left = 0.0f;
            f_buffer[f_i].right = 0.0f;
        }

        v_daw_run_engine(f_block_size, f_buffer, NULL);

        if(a_stem){
            for(f_i2 = 0; f_i2 < f_stem_count; ++f_i2){
                f_size = 0;
                int f_track_num = f_tps[f_i2];
                struct SamplePair* f_track_buff =
                    self->track_pool[f_track_num]->plugin_plan.output;
                /*Interleave the samples...*/
                for(f_i = 0; f_i < f_block_size; ++f_i){
                    f_output[f_size] = f_track_buff[f_i].left;
                    ++f_size;
                    f_output[f_size] = f_track_buff[f_i].right;
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
            f_output[f_size] = f_buffer[f_i].left;
            ++f_size;
            f_output[f_size] = f_buffer[f_i].right;
            ++f_size;
        }

        if(a_create_file){
            sg_write_audio(f_sndfile, f_output, f_block_size);
        }

        v_daw_zero_all_buffers(self);
        f_sample_count += f_block_size;
    }

#if SG_OS == _OS_LINUX
    if(print_progress){
        printf("\n");
    }

    clock_gettime(CLOCK_REALTIME, &f_finish);
    double f_elapsed = v_print_benchmark(
        "v_daw_offline_render",
        f_start,
        f_finish
    );
    double f_realtime = (double)f_sample_count / (double)f_sample_rate;

    log_info("Song length: %f seconds", f_realtime);

    if(f_elapsed > 0.0f && f_realtime > 0.0f){
        log_info(
            "Ratio of render rate to real time (higher is better):  %f: 1",
            f_realtime / f_elapsed
        );
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

    free(f_buffer);
    free(f_output);

    SGPATHSTR f_tmp_finished[1024];

    if(a_stem){
        sg_path_snprintf(
            f_tmp_finished, 
            1024, 
#if SG_OS == _OS_WINDOWS
            L"%ls/finished", 
#else
            "%s/finished", 
#endif
            a_file_out
        );
    } else {
        sg_path_snprintf(
            f_tmp_finished, 
            1024, 
#if SG_OS == _OS_WINDOWS
            L"%ls.finished", 
#else
            "%s.finished", 
#endif
            a_file_out
        );
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
    t_track * f_track;
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

