#include <string.h>

#include "files.h"
#include "stargate.h"
#include "daw.h"


t_daw * DAW;

t_daw * g_daw_get(SGFLT sr){
    t_daw * f_result;
    clalloc((void**)&f_result, sizeof(t_daw));

    f_result->metronome_enabled = 0;
    metronome_init(&f_result->metronome, sr);
    if(!SG_OFFLINE_RENDER ){
        metronome_load(&f_result->metronome);
    }
    f_result->overdub_mode = 0;
    f_result->loop_mode = 0;

    f_result->en_song = NULL;
    f_result->is_soloed = 0;

    f_result->ts[0].samples_per_beat = 0;
    f_result->ts[0].sample_count = 0;
    f_result->ts[0].current_sample = 0;
    f_result->ts[0].ml_sample_period_inc_beats = 0.0f;
    f_result->ts[0].ml_current_beat = 0.0f;
    f_result->ts[0].ml_next_beat = 0.0f;
    f_result->ts[0].tempo = 128.0f;
    f_result->ts[0].f_next_current_sample = 0;
    f_result->ts[0].playback_inc = 0.0f;
    f_result->ts[0].is_looping = 0;
    f_result->ts[0].is_first_period = 0;
    f_result->ts[0].playback_mode = 0;
    f_result->ts[0].suppress_new_audio_items = 0;
    f_result->ts[0].input_buffer = NULL;
    f_result->ts[0].input_count = AUDIO_INPUT_TRACK_COUNT;

    int f_i;

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i){
        clalloc(
            (void**)&f_result->ts[f_i].input_index,
            sizeof(int) * MAX_AUDIO_INPUT_COUNT
        );
        //MAX_AUDIO_INPUT_COUNT is done for padding instead of
        //AUDIO_INPUT_TRACK_COUNT
    }

    sg_assert(
        AUDIO_INPUT_TRACK_COUNT < MAX_AUDIO_INPUT_COUNT,
        "g_daw_get: Too many audio input tracks, %i >= %i",
        AUDIO_INPUT_TRACK_COUNT,
        MAX_AUDIO_INPUT_COUNT
    );

    g_seq_event_result_init(&f_result->seq_event_result);

    f_result->routing_graph = NULL;

    for(f_i = 0; f_i < DAW_MAX_SONG_COUNT; ++f_i){
        f_result->song_pool[f_i] = (t_daw_song){};
    }

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        f_result->track_pool[f_i] = g_track_get(
            f_i,
            STARGATE->thread_storage[0].sample_rate
        );
    }

    for(f_i = 0; f_i < MAX_AUDIO_ITEM_COUNT; ++f_i){
        f_result->audio_glue_indexes[f_i] = 0;
    }

    for(f_i = 0; f_i < DN_MAX_ITEM_COUNT; ++f_i){
        f_result->item_pool[f_i] = NULL;
    }

    g_daw_midi_routing_list_init(&f_result->midi_routing);

    return f_result;
}

void g_daw_seq_pool_load(t_daw* self){
    int i;
    SGPATHSTR path[2048];
    for(i = 0; i < DAW_MAX_SONG_COUNT; ++i){
        sg_path_snprintf(
            path, 
            2048, 
#if SG_OS == _OS_WINDOWS
            L"%ls%i", 
#else
            "%s%i", 
#endif
            self->sequence_folder, 
            i
        );
        if(i_file_exists(path)){
            self->song_pool[i].sequences = g_daw_sequence_get(self, i);
            self->song_pool[i].sequences_atm = g_daw_atm_sequence_get(self, i);
        }
    }
}

void v_daw_open_project(int a_first_load){
    log_info("Setting DAW project folders");
    sg_path_snprintf(
        DAW->project_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/projects/daw",
#else
        "%s/projects/daw",
#endif
        STARGATE->project_folder
    );
    sg_path_snprintf(
        DAW->item_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/items/",
#else
        "%s/items/",
#endif
        DAW->project_folder
    );
    sg_path_snprintf(
        DAW->sequence_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/songs/",
#else
        "%s/songs/",
#endif
        DAW->project_folder
    );
    sg_path_snprintf(
        DAW->automation_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/automation/",
#else
        "%s/automation/",
#endif
        DAW->project_folder
    );
    sg_path_snprintf(
        DAW->tracks_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/tracks",
#else
        "%s/tracks",
#endif
        DAW->project_folder
    );
    sg_path_snprintf(
        DAW->seq_event_file,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/seq_event.txt",
#else
        "%s/seq_event.txt",
#endif
        DAW->project_folder
    );

    int f_i;

    log_info("Clearing item pool");
    for(f_i = 0; f_i < DN_MAX_ITEM_COUNT; ++f_i)
    {
        if(DAW->item_pool[f_i]){
            g_daw_item_free(DAW->item_pool[f_i]);
            DAW->item_pool[f_i] = NULL;
        }
    }

    log_info("Opening tracks");
    v_daw_open_tracks();

    log_info("Loading sequence pool");
    g_daw_seq_pool_load(DAW);

    log_info("Loading song");
    g_daw_song_get(DAW, 0);

    log_info("Updating track routing");
    v_daw_update_track_send(DAW, 0);

    v_daw_set_is_soloed(DAW);

    log_info("Setting up MIDI devices");
    v_daw_set_midi_devices();

    if(!a_first_load){
        log_info("Updating audio inputs");
        v_daw_update_audio_inputs();
    }

    //v_daw_set_playback_cursor(DAW, 0.0f);
}

void v_daw_audio_items_run(
    t_daw* self,
    t_daw_item_ref* a_item_ref,
    int a_sample_count,
    struct SamplePair* a_buff,
    struct SamplePair* a_sc_buff,
    int* a_sc_dirty,
    t_daw_thread_storage* daw_ts,
    t_sg_thread_storage*  sg_ts
){
    t_daw_item* f_item = self->item_pool[a_item_ref->item_uid];

    if(!f_item->audio_items->index_counts[0]){
        return;
    }

    int f_playback_mode = STARGATE->playback_mode;
    t_per_audio_item_fx* f_paif_item;
    t_papifx_controls* papifx_ctl;

    t_audio_items * f_sequence = f_item->audio_items;

    int f_i = 0;
    int f_index_pos = 0;
    int f_send_num = 0;
    t_mf3_multi* mf3 = NULL;

    while(f_index_pos < f_sequence->index_counts[0]){
        f_i = f_sequence->indexes[0][f_index_pos].item_num;
        //f_send_num = f_sequence->indexes[0][f_index_pos].send_num;
        ++f_index_pos;

        if(!f_sequence->items[f_i]){
            ++f_i;
            continue;
        }

        t_audio_item * f_audio_item = f_sequence->items[f_i];
        int f_output_mode = f_audio_item->outputs[0];
        t_audio_pool_item* ap_item = f_audio_item->audio_pool_item;

        if(f_output_mode > 0){
            *a_sc_dirty = 1;
        }

        if(
            daw_ts->suppress_new_audio_items
            &&
            f_audio_item->adsrs[f_send_num].stage == ADSR_STAGE_OFF
        ){
            ++f_i;
            continue;
        }

        if(
            f_playback_mode == PLAYBACK_MODE_OFF
            &&
            f_audio_item->adsrs[f_send_num].stage < ADSR_STAGE_RELEASE
        ){
            v_adsr_release(&f_audio_item->adsrs[f_send_num]);
        }

        double f_audio_start = f_audio_item->adjusted_start_beat +
            a_item_ref->start - a_item_ref->start_offset;

        if(f_audio_start >= daw_ts->ml_next_beat){
            ++f_i;
            continue;
        }

        int f_i2 = 0;
        int f_i3;

        if(
            f_playback_mode != PLAYBACK_MODE_OFF
            &&
            f_audio_start >= daw_ts->ml_current_beat
            &&
            f_audio_start < daw_ts->ml_next_beat
            &&
            f_audio_start < a_item_ref->end
        ){
            if(f_audio_item->is_reversed){
                v_ifh_retrigger(
                    &f_audio_item->sample_read_heads[f_send_num],
                    f_audio_item->sample_end_offset
                );
            } else {
                v_ifh_retrigger(
                    &f_audio_item->sample_read_heads[f_send_num],
                    f_audio_item->sample_start_offset
                );
            }

            v_svf_reset(&f_audio_item->lp_filters[f_send_num]);

            v_adsr_retrigger(&f_audio_item->adsrs[f_send_num]);

            double f_diff = (daw_ts->ml_next_beat - daw_ts->ml_current_beat);
            double f_distance = f_audio_start - daw_ts->ml_current_beat;

            f_i2 = (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            if(f_i2 < 0){
                f_i2 = 0;
            } else if(f_i2 >= a_sample_count){
                f_i2 = a_sample_count - 1;
            }
        }

        if((f_audio_item->adsrs[f_send_num].stage) != ADSR_STAGE_OFF){
            while(
                f_i2 < a_sample_count
                && (
                    (
                        !f_audio_item->is_reversed
                        && (
                            f_audio_item->sample_read_heads[
                                f_send_num
                            ].whole_number < f_audio_item->sample_end_offset
                        )
                    ) || (
                        f_audio_item->is_reversed
                        && (
                            f_audio_item->sample_read_heads[
                                f_send_num
                            ].whole_number > f_audio_item->sample_start_offset
                        )
                    )
                )
            ){
                sg_assert(
                    f_i2 < a_sample_count,
                    "v_daw_audio_items_run: f_i2 %i >= a_sample_count %i",
                    f_i2,
                    a_sample_count
                );
                v_audio_item_set_fade_vol(f_audio_item, f_send_num, sg_ts);

                if(f_audio_item->audio_pool_item->channels == 1){
                    SGFLT f_tmp_sample0 = f_cubic_interpolate_ptr_ifh(
                    (f_audio_item->audio_pool_item->samples[0]),
                    (f_audio_item->sample_read_heads[f_send_num].whole_number),
                    (f_audio_item->sample_read_heads[f_send_num].fraction)) *
                    (f_audio_item->adsrs[f_send_num].output) *
                    (f_audio_item->vols_linear[f_send_num]) *
                    (f_audio_item->fade_vols[f_send_num]);

                    f_tmp_sample0 *= f_audio_item->audio_pool_item->volume;
                    SGFLT f_tmp_sample1 = f_tmp_sample0;

                    if(ap_item->fx_controls.loaded){
                        for(f_i3 = 0; f_i3 < 8; ++f_i3){
                            papifx_ctl = &ap_item->fx_controls.controls[f_i3];
                            mf3 = f_audio_item->papifx.fx[f_i3];
                            v_mf3_set(
                                mf3,
                                papifx_ctl->knobs[0],
                                papifx_ctl->knobs[1],
                                papifx_ctl->knobs[2]
                            );
                            papifx_ctl->func_ptr(
                                mf3,
                                f_tmp_sample0,
                                f_tmp_sample1
                            );
                            f_tmp_sample0 = mf3->output0;
                            f_tmp_sample1 = mf3->output1;
                        }
                    }

                    if(f_audio_item->paif && f_audio_item->paif->loaded){
                        for(f_i3 = 0; f_i3 < 8; ++f_i3){
                            f_paif_item = f_audio_item->paif->items[f_i3];
                            f_paif_item->func_ptr(
                                f_paif_item->mf3,
                                f_tmp_sample0,
                                f_tmp_sample1
                            );
                            f_tmp_sample0 = f_paif_item->mf3->output0;
                            f_tmp_sample1 = f_paif_item->mf3->output1;
                        }
                    }

                    if(f_output_mode != 1){
                        a_buff[f_i2].left += f_tmp_sample0;
                        a_buff[f_i2].right += f_tmp_sample1;
                    }

                    if(f_output_mode > 0){
                        a_sc_buff[f_i2].left += f_tmp_sample0;
                        a_sc_buff[f_i2].right += f_tmp_sample1;
                    }
                } else if(f_audio_item->audio_pool_item->channels == 2){
                    sg_assert(
                        f_audio_item->sample_read_heads[f_send_num].whole_number
                        <=
                        f_audio_item->audio_pool_item->length,
                        "v_daw_audio_items_run: read head %i > length %i",
                        f_audio_item->sample_read_heads[f_send_num].whole_number,
                        f_audio_item->audio_pool_item->length
                    );

                    sg_assert(
                        f_audio_item->sample_read_heads[f_send_num].whole_number
                        >=
                        AUDIO_ITEM_PADDING_DIV2,
                        "v_daw_audio_items_run: read head %i < start padding %i",
                        f_audio_item->sample_read_heads[f_send_num].whole_number,
                        AUDIO_ITEM_PADDING_DIV2
                    );

                    SGFLT f_tmp_sample0 = f_cubic_interpolate_ptr_ifh(
                        f_audio_item->audio_pool_item->samples[0],
                        f_audio_item->sample_read_heads[
                            f_send_num].whole_number,
                        f_audio_item->sample_read_heads[f_send_num].fraction
                    ) *
                        f_audio_item->adsrs[f_send_num].output *
                        f_audio_item->vols_linear[f_send_num] *
                        f_audio_item->fade_vols[f_send_num];

                    f_tmp_sample0 *= f_audio_item->audio_pool_item->volume;
                    SGFLT f_tmp_sample1 = f_cubic_interpolate_ptr_ifh(
                        f_audio_item->audio_pool_item->samples[1],
                        f_audio_item->sample_read_heads[
                            f_send_num].whole_number,
                        f_audio_item->sample_read_heads[f_send_num].fraction
                    ) *
                        f_audio_item->adsrs[f_send_num].output *
                        f_audio_item->vols_linear[f_send_num] *
                        f_audio_item->fade_vols[f_send_num];

                    f_tmp_sample1 *= f_audio_item->audio_pool_item->volume;

                    if(ap_item->fx_controls.loaded){
                        for(f_i3 = 0; f_i3 < 8; ++f_i3){
                            papifx_ctl = &ap_item->fx_controls.controls[f_i3];
                            mf3 = f_audio_item->papifx.fx[f_i3];
                            v_mf3_set(
                                mf3,
                                papifx_ctl->knobs[0],
                                papifx_ctl->knobs[1],
                                papifx_ctl->knobs[2]
                            );
                            papifx_ctl->func_ptr(
                                mf3,
                                f_tmp_sample0,
                                f_tmp_sample1
                            );
                            f_tmp_sample0 = mf3->output0;
                            f_tmp_sample1 = mf3->output1;
                        }
                    }

                    if(f_audio_item->paif && f_audio_item->paif->loaded){
                        for(f_i3 = 0; f_i3 < 8; ++f_i3){
                            f_paif_item = f_audio_item->paif->items[f_i3];
                            f_paif_item->func_ptr(f_paif_item->mf3,
                                f_tmp_sample0, f_tmp_sample1);
                            f_tmp_sample0 = f_paif_item->mf3->output0;
                            f_tmp_sample1 = f_paif_item->mf3->output1;
                        }
                    }

                    if(f_output_mode != 1){
                        a_buff[f_i2].left += f_tmp_sample0;
                        a_buff[f_i2].right += f_tmp_sample1;
                    }

                    if(f_output_mode > 0){
                        a_sc_buff[f_i2].left += f_tmp_sample0;
                        a_sc_buff[f_i2].right += f_tmp_sample1;
                    }

                } else {
                    // TODO:  Catch this during load and
                    // do something then...
                    sg_assert(
                        0,
                        "v_daw_audio_items_run: Invalid number of channels %i",
                        f_audio_item->audio_pool_item->channels
                    );
                }

                if(f_audio_item->is_reversed){
                    v_ifh_run_reverse(
                        &f_audio_item->sample_read_heads[f_send_num],
                        f_audio_item->ratio
                    );

                    if(
                        f_audio_item->sample_read_heads[f_send_num].whole_number
                        <
                        AUDIO_ITEM_PADDING_DIV2
                    ){
                        f_audio_item->adsrs[f_send_num].stage = ADSR_STAGE_OFF;
                    }
                } else {
                    v_ifh_run(
                        &f_audio_item->sample_read_heads[f_send_num],
                        f_audio_item->ratio
                    );

                    if(
                        f_audio_item->sample_read_heads[f_send_num].whole_number
                        >=
                        f_audio_item->audio_pool_item->length - 1
                    ){
                        f_audio_item->adsrs[f_send_num].stage = ADSR_STAGE_OFF;
                    }
                }


                if(f_audio_item->adsrs[f_send_num].stage == ADSR_STAGE_OFF){
                    break;
                }

                v_adsr_run(&f_audio_item->adsrs[f_send_num]);

                ++f_i2;
            }//while < sample count
        }  //if stage
        ++f_i;
    } //while < audio item count
}

void v_daw_run_engine(
    int a_sample_count,
    struct SamplePair* a_output,
    SGFLT *a_input_buffers
){
    t_daw * self = DAW;
    t_sg_seq_event_period * f_seq_period;
    int f_period, sample_count;
    struct SamplePair* output;
    if(STARGATE->playback_mode != PLAYBACK_MODE_OFF){
        v_sg_seq_event_list_set(
            &self->en_song->sequences->events,
            &self->seq_event_result,
            a_output,
            a_input_buffers,
            AUDIO_INPUT_TRACK_COUNT,
            a_sample_count,
            self->ts[0].current_sample,
            self->loop_mode
        );
    } else {
        self->seq_event_result.count = 1;
        f_seq_period = &self->seq_event_result.sample_periods[0];
        f_seq_period->is_looping = 0;
        v_sg_seq_event_result_set_default(
            &self->seq_event_result,
            &self->en_song->sequences->events,
            a_output,
            a_input_buffers,
            AUDIO_INPUT_TRACK_COUNT,
            a_sample_count,
            self->ts[0].current_sample
        );
    }

    for(f_period = 0; f_period < self->seq_event_result.count; ++f_period){
        f_seq_period = &self->seq_event_result.sample_periods[f_period];

        sample_count = f_seq_period->period.sample_count;
        output = f_seq_period->period.buffers;
        //notify the worker threads to wake up
        int f_i;
        struct SgWorkerThread* _thread;
        for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i){
            _thread = &STARGATE->worker_threads[f_i];
            pthread_spin_lock(&_thread->lock);
            pthread_mutex_lock(&_thread->track_block_mutex);
            pthread_cond_broadcast(&_thread->track_cond);
            pthread_mutex_unlock(&_thread->track_block_mutex);
        }

        long f_next_current_sample =
            DAW->ts[0].current_sample + sample_count;

        STARGATE->sample_count = sample_count;
        self->ts[0].f_next_current_sample = f_next_current_sample;

        self->ts[0].current_sample = f_seq_period->period.current_sample;
        self->ts[0].f_next_current_sample =
            f_seq_period->period.current_sample +
            f_seq_period->period.sample_count;

        self->ts[0].samples_per_beat = f_seq_period->samples_per_beat;
        self->ts[0].tempo = f_seq_period->tempo;
        self->ts[0].playback_inc = f_seq_period->playback_inc;
        self->ts[0].is_looping = f_seq_period->is_looping;
        self->ts[0].playback_mode = STARGATE->playback_mode;
        self->ts[0].sample_count = sample_count;
        self->ts[0].input_buffer = a_input_buffers;

        if(STARGATE->playback_mode > 0){
            self->ts[0].ml_sample_period_inc_beats =
                f_seq_period->period.period_inc_beats;
            self->ts[0].ml_current_beat = f_seq_period->period.start_beat;
            self->ts[0].ml_next_beat = f_seq_period->period.end_beat;

            v_sample_period_set_atm_events(
                &f_seq_period->period,
                &self->en_song->sequences->events,
                DAW->ts[0].current_sample,
                sample_count
            );

            self->ts[0].atm_tick_count = f_seq_period->period.atm_tick_count;
            memcpy(
                self->ts[0].atm_ticks,
                f_seq_period->period.atm_ticks,
                sizeof(t_atm_tick) * ATM_TICK_BUFFER_SIZE
            );
        } else {
            self->ts[0].atm_tick_count = 0;
        }

        for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
            self->track_pool[f_i]->status = STATUS_NOT_PROCESSED;
            self->track_pool[f_i]->bus_counter =
                self->routing_graph->bus_count[f_i];
            self->track_pool[f_i]->event_list->len = 0;
        }

        //unleash the hounds
        for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i){
            t_daw_thread_storage * ts = &DAW->ts[f_i];
            memcpy(ts, &DAW->ts[0], sizeof(t_daw_thread_storage));
            pthread_spin_unlock(&STARGATE->worker_threads[f_i].lock);
        }

        v_daw_process(0);  // From the audio thread

        t_track * f_main_track = self->track_pool[0];
        struct SamplePair* f_main_buff = f_main_track->plugin_plan.output;

        //wait for the other threads to finish
        v_wait_for_threads();

        v_daw_process_track(
            self,
            0,
            0,
            sample_count,
            STARGATE->playback_mode,
            &self->ts[0]
        );
        if(
            STARGATE->playback_mode != PLAYBACK_MODE_OFF 
            && 
            self->metronome_enabled
            &&
            !STARGATE->is_offline_rendering
        ){
            metronome_run(
                &self->metronome, 
                sample_count, 
                f_main_buff,
                self->ts[0].ml_current_beat,
                self->ts[0].ml_next_beat
            );
        }

        // TODO: Can this be eliminated somehow?
        for(f_i = 0; f_i < sample_count; ++f_i){
            output[f_i].left = f_main_buff[f_i].left;
            output[f_i].right = f_main_buff[f_i].right;
        }

        v_zero_buffer(f_main_buff, sample_count);

        DAW->ts[0].current_sample = f_next_current_sample;
        DAW->ts[0].is_first_period = 0;
    }
}

void v_daw_process(int thread_num){
    t_track * f_track;
    int f_track_index;
    t_daw * self = DAW;
    int f_i = thread_num;
    int f_sorted_count = self->routing_graph->track_pool_sorted_count;
    int * f_sorted =
        self->routing_graph->track_pool_sorted[thread_num];

    t_daw_thread_storage * f_ts = &DAW->ts[thread_num];

    int f_playback_mode = f_ts->playback_mode;
    int f_sample_count = f_ts->sample_count;

    while(f_i < f_sorted_count)
    {
        f_track_index = f_sorted[f_i];
        f_track = self->track_pool[f_track_index];

        if(f_track->status != STATUS_NOT_PROCESSED)
        {
            ++f_i;
            continue;
        }

        pthread_spin_lock(&f_track->lock);

        if(f_track->status == STATUS_NOT_PROCESSED)
        {
            f_track->status = STATUS_PROCESSING;
        }
        else
        {
            pthread_spin_unlock(&f_track->lock);
            ++f_i;
            continue;
        }

        pthread_spin_unlock(&f_track->lock);

        v_daw_process_track(
            self,
            f_track->track_num,
            thread_num,
            f_sample_count,
            f_playback_mode,
            f_ts
        );

        f_track->status = STATUS_PROCESSED;

        ++f_i;
    }
}


void v_daw_zero_all_buffers(t_daw * self){
    int i, j;
    struct SamplePair* buff;
    for(i = 0; i < DN_TRACK_COUNT; ++i){
        v_zero_buffer(
            self->track_pool[i]->input_buffer,
            FRAMES_PER_BUFFER
        );
        for(j = 0; j < MAX_PLUGIN_COUNT + 1; ++j){
            buff = self->track_pool[i]->audio[j];
            v_zero_buffer(buff, FRAMES_PER_BUFFER);
        }
    }
}

void v_daw_panic(t_daw * self){
    int f_i;
    int f_i2;
    t_track * f_track;
    t_plugin * f_plugin;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        f_track = self->track_pool[f_i];

        for(f_i2 = 0; f_i2 < MAX_PLUGIN_TOTAL_COUNT; ++f_i2){
            f_plugin = f_track->plugins[f_i2];
            if(f_plugin && f_plugin->descriptor->panic){
                f_plugin->descriptor->panic(f_plugin->plugin_handle);
            }
        }
    }
    v_daw_zero_all_buffers(self);
}

void g_daw_instantiate(SGFLT sr)
{
    DAW = g_daw_get(sr);
}

void daw_set_sequence(t_daw* self, int uid){
    sg_assert(
        uid >= 0 && uid < DAW_MAX_SONG_COUNT,
        "daw_set_sequence: uid %i out of range 0 to %i",
        uid,
        DAW_MAX_SONG_COUNT
    );
    // Must be loaded
    sg_assert_ptr(
        self->song_pool[uid].sequences,
        "daw_set_sequence: sequence uid %i not loaded",
        uid
    );
    // May actually not be loaded, especially in older projects, and that is OK
    /*
    sg_assert_ptr(
        self->song_pool[uid].sequences_atm,
        "daw_set_sequence: atm sequence uid %i not loaded",
        uid
    );
    */

    pthread_spin_lock(&STARGATE->main_lock);
    self->en_song = &self->song_pool[uid];
    pthread_spin_unlock(&STARGATE->main_lock);
}
