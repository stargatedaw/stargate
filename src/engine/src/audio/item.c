#include "plugin.h"
#include "audio/item.h"


void v_audio_item_free(t_audio_item* a_audio_item)
{
    //TODO:  Create a free method for these...
    //if(a_audio_item->adsr)
    //{ }
    //if(a_audio_item->sample_read_head)
    //{}
    if(!a_audio_item){
        return;
    }

    if(a_audio_item->paif){
        v_paif_free(a_audio_item->paif);
    }
    papifx_free(&a_audio_item->papifx, 0);

    if(a_audio_item){
        free(a_audio_item);
    }
}

t_audio_item * g_audio_item_get(SGFLT a_sr){
    int f_i;
    t_audio_item * f_result;

    lmalloc((void**)&f_result, sizeof(t_audio_item));

    f_result->ratio = 1.0f;
    f_result->paif = NULL;
    papifx_init(&f_result->papifx, a_sr);
    f_result->uid = -1;
    g_pit_ratio_init(&f_result->pitch_ratio_ptr);

    for(f_i = 0; f_i < SG_AUDIO_ITEM_SEND_COUNT; ++f_i){
        g_adsr_init(&f_result->adsrs[f_i], a_sr);
        v_adsr_set_adsr(&f_result->adsrs[f_i], 0.003f, 0.1f, 1.0f, 0.2f);
        v_adsr_retrigger(&f_result->adsrs[f_i]);
        f_result->adsrs[f_i].stage = ADSR_STAGE_OFF;
        g_ifh_init(&f_result->sample_read_heads[f_i]);
        g_svf_init(&f_result->lp_filters[f_i], a_sr);
        v_svf_set_cutoff_base(
            &f_result->lp_filters[f_i],
            f_pit_hz_to_midi_note(7200.0f)
        );
        v_svf_set_res(&f_result->lp_filters[f_i], -15.0f);
        v_svf_set_cutoff(&f_result->lp_filters[f_i]);
        f_result->vols[f_i] = 0.0f;
        f_result->vols_linear[f_i] = 1.0f;
    }

    return f_result;
}

t_audio_items * g_audio_items_get(int a_sr){
    t_audio_items * f_result;

    lmalloc((void**)&f_result, sizeof(t_audio_items));

    f_result->sample_rate = a_sr;

    int f_i, f_i2;

    for(f_i = 0; f_i < MAX_AUDIO_ITEM_COUNT; ++f_i){
        f_result->items[f_i] = 0; //g_audio_item_get((SGFLT)(a_sr));
    }

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i){
        f_result->index_counts[f_i] = 0;

        for(f_i2 = 0; f_i2 < MAX_AUDIO_ITEM_COUNT; ++f_i2){
            f_result->indexes[f_i][f_i2].item_num = 0;
            f_result->indexes[f_i][f_i2].send_num = 0;
        }
    }
    return f_result;
}

t_audio_item * g_audio_item_load_single(
    SGFLT a_sr,
    t_2d_char_array * f_current_string,
    t_audio_items * a_items,
    t_audio_pool * a_audio_pool,
    t_audio_pool_item * a_wav_item
){
    t_audio_item * f_result;

    v_iterate_2d_char_array(f_current_string);

    if(f_current_string->eof){
        return 0;
    }

    int f_index = atoi(f_current_string->current_str);

    if(a_items){
        f_result = a_items->items[f_index];
    } else {
        f_result = g_audio_item_get(a_sr);
    }

    f_result->index = f_index;

    v_iterate_2d_char_array(f_current_string);
    f_result->uid = atoi(f_current_string->current_str);

    if(a_wav_item){
        f_result->audio_pool_item = a_wav_item;
    } else {
        f_result->audio_pool_item = g_audio_pool_get_item_by_uid(
            a_audio_pool,
            f_result->uid
        );

        if(!f_result->audio_pool_item){
            log_error(
                "g_audio_item_load_single failed for uid %i, "
                "not found",
                f_result->uid
            );
            return 0;
        }
    }
    v_iterate_2d_char_array(f_current_string);
    SGFLT f_sample_start = atof(f_current_string->current_str) * 0.001f;

    if(f_sample_start < 0.0f){
        f_sample_start = 0.0f;
    } else if(f_sample_start > 0.999f){
        f_sample_start = 0.999f;
    }

    f_result->sample_start = f_sample_start;

    f_result->sample_start_offset =
        (int)((f_result->sample_start *
        ((SGFLT)f_result->audio_pool_item->length))) +
        AUDIO_ITEM_PADDING_DIV2;

    v_iterate_2d_char_array(f_current_string);
    SGFLT f_sample_end = atof(f_current_string->current_str) * 0.001f;

    if(f_sample_end < 0.001f){
        f_sample_end = 0.001f;
    } else if(f_sample_end > 1.0f){
        f_sample_end = 1.0f;
    }

    f_result->sample_end = f_sample_end;

    f_result->sample_end_offset = (int)((f_result->sample_end *
        ((SGFLT)f_result->audio_pool_item->length)));

    v_iterate_2d_char_array(f_current_string);
    f_result->start_bar = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->start_beat = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->timestretch_mode = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->pitch_shift = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->outputs[0] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->vols[0] = atof(f_current_string->current_str);
    f_result->vols_linear[0] = f_db_to_linear_fast(f_result->vols[0]);

    v_iterate_2d_char_array(f_current_string);
    f_result->timestretch_amt = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->sample_fade_in = atof(f_current_string->current_str) * 0.001f;

    v_iterate_2d_char_array(f_current_string);
    f_result->sample_fade_out = atof(f_current_string->current_str) * 0.001f;

    //lane, not used by the back-end
    v_iterate_2d_char_array(f_current_string);

    v_iterate_2d_char_array(f_current_string);
    f_result->pitch_shift_end = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->timestretch_amt_end = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->is_reversed = atoi(f_current_string->current_str);

    //crispness, Not used in the back-end
    v_iterate_2d_char_array(f_current_string);

    //These are multiplied by -1.0f to work correctly with
    //v_audio_item_set_fade_vol()
    v_iterate_2d_char_array(f_current_string);
    f_result->fadein_vol = atof(f_current_string->current_str) * -1.0f;

    v_iterate_2d_char_array(f_current_string);
    f_result->fadeout_vol = atof(f_current_string->current_str) * -1.0f;

    v_iterate_2d_char_array(f_current_string);
    f_result->paif_automation_uid = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->outputs[1] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->vols[1] = atof(f_current_string->current_str);
    f_result->vols_linear[1] = f_db_to_linear_fast(f_result->vols[1]);

    v_iterate_2d_char_array(f_current_string);
    f_result->outputs[2] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->vols[2] = atof(f_current_string->current_str);
    f_result->vols_linear[2] = f_db_to_linear_fast(f_result->vols[2]);

    v_iterate_2d_char_array(f_current_string);
    f_result->sidechain[0] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->sidechain[1] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->sidechain[2] = atoi(f_current_string->current_str);

    if(f_result->sample_start_offset < AUDIO_ITEM_PADDING_DIV2){
        log_info(
            "f_result->sample_start_offset <= AUDIO_ITEM_PADDING_DIV2"
            " %i %i",
            f_result->sample_start_offset,
            AUDIO_ITEM_PADDING_DIV2
        );
        f_result->sample_start_offset = AUDIO_ITEM_PADDING_DIV2;
    }

    if(f_result->sample_end_offset < AUDIO_ITEM_PADDING_DIV2){
        log_info(
            "f_result->sample_end_offset <= AUDIO_ITEM_PADDING_DIV2"
            " %i %i",
            f_result->sample_end_offset,
            AUDIO_ITEM_PADDING_DIV2
        );
        f_result->sample_end_offset = AUDIO_ITEM_PADDING_DIV2;
    }

    if(f_result->sample_start_offset > f_result->audio_pool_item->length){
        log_info(
            "f_result->sample_start_offset >= "
            "f_result->audio_pool_item->length %i %i",
            f_result->sample_start_offset,
            f_result->audio_pool_item->length
        );
        f_result->sample_start_offset = f_result->audio_pool_item->length;
    }

    if(f_result->sample_end_offset > f_result->audio_pool_item->length){
        log_info(
            "f_result->sample_end_offset >= f_result->audio_pool_item->length"
            " %i %i",
            f_result->sample_end_offset,
            f_result->audio_pool_item->length
        );
        f_result->sample_end_offset = f_result->audio_pool_item->length;
    }

    if(f_result->is_reversed){
        int f_old_start = f_result->sample_start_offset;
        int f_old_end = f_result->sample_end_offset;
        f_result->sample_start_offset =
            f_result->audio_pool_item->length - f_old_end;
        f_result->sample_end_offset =
            f_result->audio_pool_item->length - f_old_start;
    }

    // TODO: Convert fade in start/end to SGFLT, and use iter_beat instead
    // of raw sample numbers, convert percentages to percentages of length in
    // beats, update set_fade_vol if needed
    // OR: Maybe the front of the sample is 0..1, and the back is musical
    f_result->sample_fade_in_end =
        f_result->sample_end_offset - f_result->sample_start_offset;
    f_result->sample_fade_in_end =
        f_result->sample_start_offset +
        ((int)((SGFLT)(f_result->sample_fade_in_end) *
        f_result->sample_fade_in)) + AUDIO_ITEM_PADDING_DIV2;

    // Anything less than this will use a linear fade
    int max_linear = f_result->audio_pool_item->sample_rate / 10;

    if(f_result->sample_fade_in_end < max_linear){
        f_result->is_linear_fade_in = 1;
    } else {
        log_info("Non-linear fade in");
        f_result->is_linear_fade_in = 0;
    }

    f_result->sample_fade_out_start =
        f_result->sample_end_offset - f_result->sample_start_offset;
    f_result->sample_fade_out_start =
        f_result->sample_start_offset +
        ((int)((SGFLT)(f_result->sample_fade_out_start) *
        f_result->sample_fade_out)) + AUDIO_ITEM_PADDING_DIV2;

    int f_fade_diff = (f_result->sample_fade_in_end -
        f_result->sample_start_offset - (AUDIO_ITEM_PADDING_DIV2));

    if(f_fade_diff > 0){
        f_result->sample_fade_in_divisor = 1.0f / (SGFLT)f_fade_diff;
    } else {
        f_result->sample_fade_in_divisor = 0.0f;
    }

    f_fade_diff =
        (f_result->sample_end_offset - f_result->sample_fade_out_start);

    if(f_fade_diff < max_linear){
        f_result->is_linear_fade_out = 1;
    } else {
        log_info("Non-linear fade out");
        f_result->is_linear_fade_out = 0;
    }

    if(f_fade_diff > 0){
        f_result->sample_fade_out_divisor = 1.0f / (SGFLT)f_fade_diff;
    } else {
        f_result->sample_fade_out_divisor = 0.0f;
    }

    f_result->adjusted_start_beat =
        ((SGFLT)f_result->start_bar * 4) + f_result->start_beat;

    if(f_result->is_reversed){
        f_result->sample_fade_in_end =
                f_result->sample_end_offset - (f_result->sample_fade_in_end -
                f_result->sample_start_offset);
        f_result->sample_fade_out_start =
                f_result->sample_start_offset + (f_result->sample_end_offset -
                f_result->sample_fade_out_start);
    }

    f_result->ratio = f_result->audio_pool_item->ratio_orig;

    switch(f_result->timestretch_mode){
        //case 0:  //None
        //    break;
        case 1:  //Pitch affecting time
        {
            //Otherwise, it's already been stretched offline
            if(f_result->pitch_shift == f_result->pitch_shift_end){
                if((f_result->pitch_shift) >= 0.0f){
                    f_result->ratio *= f_pit_midi_note_to_ratio_fast(
                        0.0f,
                        f_result->pitch_shift,
                        &f_result->pitch_ratio_ptr
                    );
                } else {
                    f_result->ratio *= f_pit_midi_note_to_ratio_fast(
                        f_result->pitch_shift * -1.0f,
                        0.0f,
                        &f_result->pitch_ratio_ptr
                    );
                }
            }
        }
            break;
        case 2:  //Time affecting pitch
        {
            //Otherwise, it's already been stretched offline
            if(f_result->timestretch_amt == f_result->timestretch_amt_end)
            {
                f_result->ratio *= (1.0f / (f_result->timestretch_amt));
            }
        }
            break;
        /*
        //Don't have to do anything with these, they comes pre-stretched...
        case 3:  //Rubberband
        case 4:  //Rubberband (preserving formants)
        case 5:  //SBSMS
        case 6: Paulstretch
        */
    }

    return f_result;
}

void v_audio_item_set_fade_vol(
    t_audio_item *self,
    int a_send_num,
    t_sg_thread_storage* sg_ts
){
    t_int_frac_read_head* read_head = &self->sample_read_heads[a_send_num];

    if(self->is_reversed){
        if(
            read_head->whole_number > self->sample_fade_in_end
            &&
            self->sample_fade_in_divisor != 0.0f
        ){
            self->fade_vols[a_send_num] =
                ((SGFLT)(read_head->whole_number) -
                self->sample_fade_in_end - AUDIO_ITEM_PADDING_DIV2)
                * self->sample_fade_in_divisor;

            if(self->is_linear_fade_in){
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            } else {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num]) * self->fadein_vol)
                    - self->fadein_vol;
                //self->fade_vol = (self->fade_vol * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
            }
        } else if(
            read_head->whole_number <= self->sample_fade_out_start
            &&
            self->sample_fade_out_divisor != 0.0f
        ){
            self->fade_vols[a_send_num] = ((SGFLT)(
                self->sample_fade_out_start - read_head->whole_number
            )) * self->sample_fade_out_divisor;

            if(self->is_linear_fade_out){
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            } else {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num])
                    * self->fadeout_vol) - self->fadeout_vol;
                //self->fade_vol =
                //  ((self->fade_vol) * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
            }
        } else {
            self->fade_vols[a_send_num] = 1.0f;
        }
    } else {
        if(
            read_head->whole_number < self->sample_fade_in_end
            &&
            self->sample_fade_in_divisor != 0.0f
        ){
            self->fade_vols[a_send_num] =
                ((SGFLT)(self->sample_fade_in_end -
                read_head->whole_number - AUDIO_ITEM_PADDING_DIV2))
                * self->sample_fade_in_divisor;

            if(self->is_linear_fade_in){
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            } else {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num])
                    * self->fadein_vol) - self->fadein_vol;
                //self->fade_vol =
                //  ((self->fade_vol) * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
                self->fade_vols[a_send_num] =
                    v_svf_run_2_pole_lp(&self->lp_filters[a_send_num],
                    self->fade_vols[a_send_num]);
            }
        } else if(
            read_head->whole_number >= self->sample_fade_out_start
            &&
            self->sample_fade_out_divisor != 0.0f
        ){
            self->fade_vols[a_send_num] =
                ((SGFLT)(read_head->whole_number -
                self->sample_fade_out_start)) * self->sample_fade_out_divisor;
            if(self->fade_vols[a_send_num] == 0.0){
                v_svf_set_output(
                    &self->lp_filters[a_send_num],
                    1.0
                );
            }

            if(
                self->is_linear_fade_out
                || (
                    read_head->whole_number
                    >
                    self->sample_end_offset - sg_ts->five_ms
                )
            ){
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            } else {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num]) *
                    self->fadeout_vol) - self->fadeout_vol;
                //self->fade_vol = (self->fade_vol * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] = f_db_to_linear_fast(
                    self->fade_vols[a_send_num]
                );
                self->fade_vols[a_send_num] = v_svf_run_2_pole_lp(
                    &self->lp_filters[a_send_num],
                    self->fade_vols[a_send_num]
                );
            }
        } else {
            self->fade_vols[a_send_num] = 1.0f;
        }
    }
}

void v_audio_items_free(t_audio_items *a_audio_items){
    int f_i;
    for(f_i = 0; f_i < MAX_AUDIO_ITEM_COUNT; ++f_i){
        v_audio_item_free(a_audio_items->items[f_i]);
        a_audio_items->items[f_i] = NULL;
    }

    free(a_audio_items);
}


