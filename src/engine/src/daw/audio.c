#include "audiodsp/modules/multifx/multifx3knob.h"
#include "stargate.h"
#include "daw.h"


void v_daw_update_audio_inputs()
{
    v_update_audio_inputs(DAW->project_folder);

    pthread_spin_lock(&STARGATE->main_lock);

    int f_i;
    for(f_i = 0; f_i < AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        DAW->ts[0].input_index[f_i] =
            STARGATE->audio_inputs[f_i].output_track;
    }

    pthread_spin_unlock(&STARGATE->main_lock);
}

void v_daw_papifx_set_control(
    int ap_uid,
    int port_num,
    SGFLT port_val
){
    int fx_index = port_num / 4;
    int control_index = port_num % 4;
    t_audio_pool_item* ap_item = &STARGATE->audio_pool->items[ap_uid];

    pthread_spin_lock(&STARGATE->main_lock);

    t_papifx_controls* controls = &ap_item->fx_controls.controls[fx_index];
    if(control_index == 3){
        int fx_type = (int)port_val;
        sg_assert(
            fx_type >= 0 && fx_type < MULTIFX3KNOB_MAX_INDEX,
            "v_daw_papifx_set_control: invalid fx type %i, range 0 to %i",
            fx_type,
            MULTIFX3KNOB_MAX_INDEX
        );
        controls->fx_type = fx_type;
        controls->func_ptr = g_mf3_get_function_pointer(fx_type);
    } else {
        sg_assert(
            port_val >= 0. && port_val <= 127.,
            "v_daw_papifx_set_control: port %f out of range 0 to 127",
            port_val
        );
        controls->knobs[control_index] = port_val;
    }
    ap_item->fx_controls.loaded = 1;

    pthread_spin_unlock(&STARGATE->main_lock);
}

void v_daw_paif_set_control(
    t_daw * self,
    int a_item_index,
    int a_audio_item_index,
    int a_port,
    SGFLT a_val
){
    int f_effect_index = a_port / 4;
    int f_control_index = a_port % 4;

    t_audio_item * f_audio_item = self->item_pool[
        a_item_index]->audio_items->items[a_audio_item_index];

    t_paif * f_sequence = f_audio_item->paif;
    t_per_audio_item_fx * f_item;

    SGFLT f_sr = STARGATE->thread_storage[0].sample_rate;

    if(!f_sequence){
        f_sequence = g_paif8_get();
        pthread_spin_lock(&STARGATE->main_lock);
        f_audio_item->paif = f_sequence;
        pthread_spin_unlock(&STARGATE->main_lock);
    }

    if(!f_sequence->loaded){
        t_per_audio_item_fx * f_items[8];
        int f_i;
        for(f_i = 0; f_i < 8; ++f_i){
            f_items[f_i] = g_paif_get(f_sr);
        }
        pthread_spin_lock(&STARGATE->main_lock);
        for(f_i = 0; f_i < 8; ++f_i){
            f_sequence->items[f_i] = f_items[f_i];
        }
        f_sequence->loaded = 1;
        pthread_spin_unlock(&STARGATE->main_lock);
    }

    f_item = f_sequence->items[f_effect_index];

    pthread_spin_lock(&STARGATE->main_lock);

    if(f_control_index == 3){
        int f_fx_index = (int)a_val;
        f_item->fx_type = f_fx_index;
        f_item->func_ptr = g_mf3_get_function_pointer(f_fx_index);

        v_mf3_set(
            f_item->mf3,
            f_item->a_knobs[0],
            f_item->a_knobs[1],
            f_item->a_knobs[2]
        );
    } else {
        f_sequence->items[
            f_effect_index]->a_knobs[f_control_index] = a_val;

        v_mf3_set(f_item->mf3, f_item->a_knobs[0],
            f_item->a_knobs[1], f_item->a_knobs[2]);
    }

    pthread_spin_unlock(&STARGATE->main_lock);

}

void v_daw_reset_audio_item_read_heads(
    t_daw * self,
    t_audio_items * f_audio_items,
    double a_start_offset
){
    if(!f_audio_items){
        return;
    }

    int f_i;
    int f_i2;
    SGFLT sr;
    t_audio_item * f_audio_item;
    SGFLT f_tempo = self->ts[0].tempo;

    for(f_i = 0; f_i < MAX_AUDIO_ITEM_COUNT; ++f_i){
        if(f_audio_items->items[f_i]){
            f_audio_item = f_audio_items->items[f_i];
            sr = f_audio_item->audio_pool_item->sample_rate;
            double f_start_beat = a_start_offset - f_audio_item->start_beat;

            // TODO: This has bugs when tempo changes happen during the
            // audio item
            double f_end_beat = f_start_beat + f_samples_to_beat_count_sr(
                f_audio_item->sample_end_offset -
                    f_audio_item->sample_start_offset,
                f_tempo,
                sr
            );

            if(f_start_beat < f_end_beat){
                int f_sample_start = i_beat_count_to_samples(
                    f_start_beat,
                    f_tempo,
                    sr
                );

                if(f_sample_start < 0){
                    f_sample_start = 0;
                }

                for(f_i2 = 0; f_i2 < SG_AUDIO_ITEM_SEND_COUNT; ++f_i2){
                    if(f_audio_item->is_reversed){
                        v_ifh_retrigger(
                            &f_audio_item->sample_read_heads[f_i2],
                            f_audio_item->sample_end_offset - f_sample_start
                        );
                    } else {
                        v_ifh_retrigger(
                            &f_audio_item->sample_read_heads[f_i2],
                            f_audio_item->sample_start_offset +
                            f_sample_start
                        );
                    }

                    v_adsr_retrigger(&f_audio_item->adsrs[f_i2]);
                }

            }
        }
    }
}

