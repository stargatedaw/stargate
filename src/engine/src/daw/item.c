#include "audiodsp/modules/multifx/multifx3knob.h"
#include "stargate.h"
#include "audio/paifx.h"
#include "daw.h"
#include "files.h"


void g_daw_item_free(t_daw_item * self){
    if(self->events){
        free(self->events);
    }

    free(self);
}

void g_daw_item_get(t_daw* self, int a_uid){
    SGFLT f_sr = STARGATE->thread_storage[0].sample_rate;

    t_daw_item * f_result;
    lmalloc((void**)&f_result, sizeof(t_daw_item));

    f_result->event_count = 0;
    f_result->uid = a_uid;
    f_result->events = NULL;

    SGPATHSTR f_full_path[2048];
    sg_path_snprintf(
        f_full_path,
        2048,
#if SG_OS == _OS_WINDOWS
        L"%ls%i",
#else
        "%s%i",
#endif
        self->item_folder,
        a_uid
    );

    t_2d_char_array * f_current_string = g_get_2d_array_from_file(
        f_full_path,
        LARGE_STRING * 3
    );

    int f_event_pos = 0;

    f_result->audio_items = g_audio_items_get(
        STARGATE->thread_storage[0].sample_rate
    );

    while(1)
    {
        v_iterate_2d_char_array(f_current_string);

        if(f_current_string->eof)
        {
            break;
        }

        sg_assert(
            f_event_pos <= f_result->event_count,
            "g_daw_item_get: event pos %i > count %i",
            f_event_pos,
            f_result->event_count
        );

        char f_type = f_current_string->current_str[0];

        if(f_type == 'M')  //MIDI event count
        {
            sg_assert(!f_result->events, "g_daw_item_get: have events");
            v_iterate_2d_char_array(f_current_string);
            f_result->event_count = atoi(f_current_string->current_str);

            if(f_result->event_count){
                lmalloc(
                    (void**)&f_result->events,
                    sizeof(t_seq_event) * f_result->event_count
                );
            }
        } else if(f_type == 'n'){  //note
            v_iterate_2d_char_array(f_current_string);
            SGFLT f_start = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            SGFLT f_length = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_note = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_vel = atoi(f_current_string->current_str);
            SGFLT pan = 0.0;
            SGFLT attack = 0.0;
            SGFLT decay = 0.0;
            SGFLT sustain = 0.0;
            SGFLT release = 0.0;
            int channel = 0;
            SGFLT pitch_fine = 0.0;
            // TODO: Stargate v2: Remove if statement
            if(!f_current_string->eol){
                v_iterate_2d_char_array(f_current_string);
                pan = atof(f_current_string->current_str);
                if(!f_current_string->eol){
                    v_iterate_2d_char_array(f_current_string);
                    attack = atof(f_current_string->current_str);
                    v_iterate_2d_char_array(f_current_string);
                    decay = atof(f_current_string->current_str);
                    v_iterate_2d_char_array(f_current_string);
                    sustain = atof(f_current_string->current_str);
                    v_iterate_2d_char_array(f_current_string);
                    release = atof(f_current_string->current_str);
                }
                if(!f_current_string->eol){
                    v_iterate_2d_char_array(f_current_string);
                    channel = atoi(f_current_string->current_str);
                }
                if(!f_current_string->eol){
                    v_iterate_2d_char_array(f_current_string);
                    pitch_fine = atof(f_current_string->current_str);
                }
            }
            g_note_init(
                &f_result->events[f_event_pos],
                f_note,
                f_vel,
                f_start,
                f_length,
                pan,
                attack,
                decay,
                sustain,
                release,
                channel,
                pitch_fine
            );
            ++f_event_pos;
        }
        else if(f_type == 'c') //cc
        {
            v_iterate_2d_char_array(f_current_string);
            SGFLT f_start = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_cc_num = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            SGFLT f_cc_val = atof(f_current_string->current_str);
            int channel = 0;
            if(!f_current_string->eol){
                v_iterate_2d_char_array(f_current_string);
                channel = atoi(f_current_string->current_str);
            }

            g_cc_init(
                &f_result->events[f_event_pos],
                f_cc_num,
                f_cc_val,
                f_start,
                channel
            );
            ++f_event_pos;
        }
        else if(f_type == 'p') //pitchbend
        {
            v_iterate_2d_char_array(f_current_string);
            SGFLT f_start = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            SGFLT f_pb_val = atof(f_current_string->current_str) * 8192.0f;
            int channel = 0;
            if(!f_current_string->eol){
                v_iterate_2d_char_array(f_current_string);
                channel = atoi(f_current_string->current_str);
            }

            g_pitchbend_init(
                &f_result->events[f_event_pos],
                f_start,
                f_pb_val,
                channel
            );
            ++f_event_pos;
        }
        else if(f_type == 'a') //audio item
        {
            t_audio_item * f_new = g_audio_item_load_single(
                f_sr,
                f_current_string,
                0,
                STARGATE->audio_pool,
                0
            );
            if(!f_new)  //EOF'd...
            {
                break;
            }

            t_audio_items * f_audio_items = f_result->audio_items;

            int f_global_index = 0;
            int f_index_count = f_audio_items->index_counts[f_global_index];

            f_audio_items->indexes[
                f_global_index][f_index_count].item_num = f_new->index;
            f_audio_items->indexes[
                f_global_index][f_index_count].send_num = 0;
            ++f_audio_items->index_counts[f_global_index];

            f_audio_items->items[f_new->index] = f_new;
        } else if(f_type == 'f'){  // per-item-fx
            v_iterate_2d_char_array(f_current_string);
            int f_index = atoi(f_current_string->current_str);

            if(f_result->audio_items->items[f_index]){
                t_paif * f_paif = g_paif8_get();
                f_result->audio_items->items[f_index]->paif = f_paif;
                f_paif->loaded = 1;

                int f_i2 = 0;

                while(f_i2 < 8){
                    f_paif->items[f_i2] = g_paif_get(f_sr);
                    int f_i3 = 0;
                    while(f_i3 < 3){
                        v_iterate_2d_char_array(f_current_string);
                        SGFLT f_knob_val = atof(f_current_string->current_str);
                        f_paif->items[f_i2]->a_knobs[f_i3] = f_knob_val;
                        ++f_i3;
                    }
                    v_iterate_2d_char_array(f_current_string);
                    int f_type_val = atoi(f_current_string->current_str);
                    f_paif->items[f_i2]->fx_type = f_type_val;
                    f_paif->items[f_i2]->func_ptr = g_mf3_get_function_pointer(
                        f_type_val
                    );
                    v_mf3_set(
                        f_paif->items[f_i2]->mf3,
                        f_paif->items[f_i2]->a_knobs[0],
                        f_paif->items[f_i2]->a_knobs[1],
                        f_paif->items[f_i2]->a_knobs[2]
                    );
                    ++f_i2;
                }
            } else {
                log_error(
                    "per-audio-item-fx %i does not correspond to "
                    "an audio item, skipping.",
                    f_index
                );
                v_iterate_2d_char_array_to_next_line(f_current_string);
            }
        }
        else if(f_type == 'U')
        {
            v_iterate_2d_char_array(f_current_string);
            f_result->uid = atoi(f_current_string->current_str);
            sg_assert(
                f_result->uid == a_uid,
                "g_daw_item_get: file UID property %i does not "
                "match file name UID %i",
                f_result->uid,
                a_uid
            );
        }
        else
        {
            log_error(
                "g_daw_item_get: Invalid event type %c",
                f_type
            );
        }
    }

    g_free_2d_char_array(f_current_string);

    if(self->item_pool[a_uid])
    {
        g_daw_item_free(self->item_pool[a_uid]);
    }

    self->item_pool[a_uid] = f_result;
}
