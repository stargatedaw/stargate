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

#include "plugin.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/filter/nosvf.h"
#include "audiodsp/lib/math.h"
#include "plugins/va1.h"


void v_run_va1_voice(
    t_va1 *plugin_data,
    t_voc_single_voice * a_poly_voice,
    t_va1_poly_voice *a_voice,
    PluginData *out,
    int a_i,
    int a_no_events
);

void v_cleanup_va1(PluginHandle instance){
    free(instance);
}

void v_va1_or_prep(PluginHandle instance, SGFLT sample_rate){
    t_va1 *plugin = (t_va1*)instance;
    int f_i, f_i2;
    for(f_i2 = 0; f_i2 < VA1_POLYPHONY; ++f_i2){
        t_va1_poly_voice* f_voice = &plugin->data[f_i2];
        for(f_i = 0; f_i < (int)(sample_rate * 3); ++f_i){
            f_osc_run_unison_osc_core_only(&f_voice->osc_unison1);
            f_osc_run_unison_osc_core_only(&f_voice->osc_unison2);
        }
    }
}

void v_va1_set_cc_map(PluginHandle instance, char * a_msg){
    t_va1 *plugin = (t_va1 *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void va1Panic(PluginHandle instance){
    t_va1 *plugin = (t_va1*)instance;
    int f_i;
    for(f_i = 0; f_i < VA1_POLYPHONY; ++f_i){
        v_adsr_kill(&plugin->data[f_i].adsr_amp);
    }
}

void v_va1_on_stop(PluginHandle instance){
    t_va1 *plugin = (t_va1 *)instance;
    int f_i = 0;
    while(f_i < VA1_POLYPHONY){
        v_va1_poly_note_off(&plugin->data[f_i], 0);
        ++f_i;
    }
    plugin->sv_pitch_bend_value = 0.0f;
}

void v_va1_connect_buffer(
    PluginHandle instance,
    int a_index,
    SGFLT * DataLocation,
    int a_is_sidechain
){
    if(a_is_sidechain)
    {
        return;
    }

    t_va1 *plugin = (t_va1*)instance;

    switch(a_index)
    {
        case 0:
            plugin->output0 = DataLocation;
            break;
        case 1:
            plugin->output1 = DataLocation;
            break;
        default:
            sg_assert(
                0,
                "v_va1_connect_buffer: port out of range: %i",
                a_index
            );
            break;
    }
}

void v_va1_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_va1* plugin = (t_va1*)instance;

    switch (port)
    {
        case VA1_ATTACK: plugin->attack = data; break;
        case VA1_DECAY: plugin->decay = data; break;
        case VA1_SUSTAIN: plugin->sustain = data; break;
        case VA1_RELEASE: plugin->release = data; break;
        case VA1_TIMBRE: plugin->timbre = data; break;
        case VA1_RES: plugin->res = data; break;
        case VA1_DIST: plugin->dist = data; break;
        case VA1_FILTER_ATTACK:
            plugin->attack_f = data;
            break;
        case VA1_FILTER_DECAY:
            plugin->decay_f = data;
            break;
        case VA1_FILTER_SUSTAIN:
            plugin->sustain_f = data;
            break;
        case VA1_FILTER_RELEASE:
            plugin->release_f = data;
            break;
        case VA1_NOISE_AMP:
            plugin->noise_amp = data;
            break;
        case VA1_DIST_WET:
            plugin->dist_wet = data;
            break;
        case VA1_FILTER_ENV_AMT:
            plugin->filter_env_amt = data;
            break;
        case VA1_MAIN_VOLUME:
            plugin->main_vol = data;
            break;
        case VA1_OSC1_PITCH:
            plugin->osc1pitch = data;
            break;
        case VA1_OSC1_TUNE:
            plugin->osc1tune = data;
            break;
        case VA1_OSC1_TYPE:
            plugin->osc1type = data;
            break;
        case VA1_OSC1_VOLUME:
            plugin->osc1vol = data;
            break;
        case VA1_OSC2_PITCH:
            plugin->osc2pitch = data;
            break;
        case VA1_OSC2_TUNE:
            plugin->osc2tune = data;
            break;
        case VA1_OSC2_TYPE:
            plugin->osc2type = data;
            break;
        case VA1_OSC2_VOLUME:
            plugin->osc2vol = data;
            break;
        case VA1_UNISON_VOICES1:
            plugin->uni_voice1 = data;
            break;
        case VA1_UNISON_VOICES2:
            plugin->uni_voice2 = data;
            break;
        case VA1_UNISON_SPREAD1:
            plugin->uni_spread1 = data;
            break;
        case VA1_UNISON_SPREAD2:
            plugin->uni_spread2 = data;
            break;
        case VA1_MAIN_GLIDE:
            plugin->main_glide = data;
            break;
        case VA1_MAIN_PITCHBEND_AMT:
            plugin->main_pb_amt = data;
            break;
        case VA1_PITCH_ENV_AMT:
            plugin->pitch_env_amt = data;
            break;
        case VA1_PITCH_ENV_TIME:
            plugin->pitch_env_time = data;
            break;
        case VA1_LFO_FREQ:
            plugin->lfo_freq = data;
            break;
        case VA1_LFO_TYPE:
            plugin->lfo_type = data;
            break;
        case VA1_LFO_AMP:
            plugin->lfo_amp = data;
            break;
        case VA1_LFO_PITCH:
            plugin->lfo_pitch = data;
            break;
        case VA1_LFO_FILTER:
            plugin->lfo_filter = data;
            break;
        case VA1_OSC_HARD_SYNC:
            plugin->sync_hard = data;
            break;
        case VA1_RAMP_CURVE:
            plugin->ramp_curve = data;
            break;
        case VA1_FILTER_KEYTRK:
            plugin->filter_keytrk = data;
            break;
        case VA1_MONO_MODE:
            plugin->mono_mode = data;
            break;
        case VA1_LFO_PHASE:
            plugin->lfo_phase = data;
            break;
        case VA1_LFO_PITCH_FINE:
            plugin->lfo_pitch_fine = data;
            break;
        case VA1_ADSR_PREFX:
            plugin->adsr_prefx = data;
            break;
        case VA1_MIN_NOTE:
            plugin->min_note = data;
            break;
        case VA1_MAX_NOTE:
            plugin->max_note = data;
            break;
        case VA1_MAIN_PITCH:
            plugin->main_pitch = data;
            break;
        case VA1_NOISE_TYPE: plugin->noise_type = data; break;
        case VA1_FILTER_TYPE: plugin->filter_type = data; break;
        case VA1_FILTER_VELOCITY: plugin->filter_vel = data; break;
        case VA1_DIST_OUTGAIN: plugin->dist_out_gain = data; break;
        case VA1_OSC1_PB: plugin->osc1pb = data;  break;
        case VA1_OSC2_PB: plugin->osc2pb = data; break;
        case VA1_DIST_TYPE: plugin->dist_type = data; break;
        case VA1_ADSR_LIN_MAIN: plugin->adsr_lin_main = data; break;
        case VA1_PAN: plugin->pan = data; break;
        default:
            sg_assert(
                0,
                "v_va1_connect_port: unknown port %i",
                port
            );
            break;
    }
}

NO_OPTIMIZATION PluginHandle g_va1_instantiate(
    PluginDescriptor * descriptor,
    int a_sr,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_va1 *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_va1));
    if(a_sr >= 170000){
        plugin_data->oversample = 1;
        plugin_data->os_recip = 1.0f;
    } else {
        plugin_data->oversample = 192000 / a_sr;
        if(plugin_data->oversample <= 1)
        {
            plugin_data->oversample = 2;
        }
        a_sr *= plugin_data->oversample;
        plugin_data->os_recip = 1.0f / (SGFLT)plugin_data->oversample;
    }

    plugin_data->fs = a_sr;
    hpalloc(
        (void**)&plugin_data->os_buffer,
        sizeof(SGFLT) * 4096 * plugin_data->oversample
    );

    int f_i;

    g_voc_voices_init(
        &plugin_data->voices,
        VA1_POLYPHONY,
        VA1_POLYPHONY_THRESH
    );

    for (f_i = 0; f_i < VA1_POLYPHONY; ++f_i){
        g_va1_poly_init(&plugin_data->data[f_i], a_sr, f_i);
        plugin_data->data[f_i].note_f = f_i;
    }

    plugin_data->sampleNo = 0;

    plugin_data->sv_pitch_bend_value = 0.0f;
    plugin_data->sv_last_note = -1.0f;  //For glide

    //initialize all monophonic modules
    v_va1_mono_init(&plugin_data->mono_modules, plugin_data->fs);

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data,
        descriptor
    );
    plugin_data->descriptor = descriptor;

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}


void v_va1_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    char * a_file_path
){
    t_va1 *plugin_data = (t_va1*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

void v_va1_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_va1 *plugin_data = (t_va1*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_va1_process_midi_event(
    t_va1 * plugin_data,
    t_seq_event * a_event,
    int f_poly_mode
){
    int f_min_note = (int)*plugin_data->min_note;
    int f_max_note = (int)*plugin_data->max_note;

    if (a_event->type == EVENT_NOTEON)
    {
        if (a_event->velocity > 0)
        {
            if(a_event->note > f_max_note ||
                a_event->note < f_min_note)
            {
                return;
            }
            int f_voice_num = i_pick_voice(
                &plugin_data->voices,
                a_event->note,
                plugin_data->sampleNo,
                a_event->tick
            );

            t_va1_poly_voice* f_voice = &plugin_data->data[f_voice_num];

            int f_adsr_main_lin = (int)(*plugin_data->adsr_lin_main);
            f_voice->adsr_run_func = FP_ADSR_RUN[f_adsr_main_lin];

            //-20db to 0db, + main volume (0 to -60)
            f_voice->amp = f_db_to_linear_fast(
                ((a_event->velocity * 0.094488) - 12.0f)
            );
            v_nosvf_velocity_mod(
                &f_voice->svf_filter,
                a_event->velocity,
                (*plugin_data->filter_vel) * 0.01f
            );

            SGFLT f_main_pitch = (*plugin_data->main_pitch);

            f_voice->note_f = (SGFLT)a_event->note + f_main_pitch;
            f_voice->note = a_event->note + (int)(f_main_pitch);

            f_voice->filter_keytrk =
                (*plugin_data->filter_keytrk) * 0.01f * (f_voice->note_f);

            f_voice->target_pitch = (f_voice->note_f);
            f_voice->osc1pb =
                (*plugin_data->main_pb_amt) + (*plugin_data->osc1pb);
            f_voice->osc2pb =
                (*plugin_data->main_pb_amt) + (*plugin_data->osc2pb);

            f_voice->dist_out_gain = f_db_to_linear_fast(
                (*plugin_data->dist_out_gain) * 0.01f);

            f_voice->mdist_fp = g_mds_get_fp((int)(*plugin_data->dist_type));

            if(plugin_data->sv_last_note < 0.0f){
                f_voice->last_pitch = (f_voice->note_f);
            } else {
                f_voice->last_pitch = (plugin_data->sv_last_note);
            }

            f_voice->osc1_pitch_adjust =
                (*plugin_data->osc1pitch) + ((*plugin_data->osc1tune) * 0.01f);
            f_voice->osc2_pitch_adjust =
                (*plugin_data->osc2pitch) + ((*plugin_data->osc2tune) * 0.01f);

            v_rmp_retrigger_glide_t(
                &f_voice->glide_env,
                (*(plugin_data->main_glide) * 0.01f),
                f_voice->last_pitch,
                f_voice->target_pitch
            );

            f_voice->osc1_linamp =
                f_db_to_linear_fast(*(plugin_data->osc1vol));
            f_voice->osc2_linamp =
                f_db_to_linear_fast(*(plugin_data->osc2vol));
            f_voice->noise_linamp =
                f_db_to_linear_fast(*(plugin_data->noise_amp));

            f_voice->noise_func_ptr = fp_get_noise_func_ptr(
                (int)(*(plugin_data->noise_type))
            );

            f_voice->unison_spread1 = (*plugin_data->uni_spread1) * 0.01f;
            f_voice->unison_spread2 = (*plugin_data->uni_spread2) * 0.01f;

            v_adsr_retrigger(&f_voice->adsr_amp);
            v_adsr_retrigger(&f_voice->adsr_filter);

            v_lfs_sync(
                &f_voice->lfo1,
                *plugin_data->lfo_phase * 0.01f,
                *plugin_data->lfo_type
            );

            SGFLT f_attack = *(plugin_data->attack) * .01;
            f_attack = (f_attack) * (f_attack);
            SGFLT f_decay = *(plugin_data->decay) * .01;
            f_decay = (f_decay) * (f_decay);
            SGFLT f_release = *(plugin_data->release) * .01;
            f_release = (f_release) * (f_release);

            FP_ADSR_SET[f_adsr_main_lin](
                &f_voice->adsr_amp,
                f_attack,
                f_decay,
                *(plugin_data->sustain),
                f_release
            );

            SGFLT f_attack_f = *(plugin_data->attack_f) * .01;
            f_attack_f = (f_attack_f) * (f_attack_f);
            SGFLT f_decay_f = *(plugin_data->decay_f) * .01;
            f_decay_f = (f_decay_f) * (f_decay_f);
            SGFLT f_release_f = *(plugin_data->release_f) * .01;
            f_release_f = (f_release_f) * (f_release_f);

            v_adsr_set_adsr(
                &f_voice->adsr_filter,
                f_attack_f, f_decay_f,
                *(plugin_data->sustain_f) * 0.01f,
                f_release_f
            );

            v_rmp_retrigger_curve(
                &f_voice->pitch_env,
                *(plugin_data->pitch_env_time) * 0.01f,
                *(plugin_data->pitch_env_amt),
                *(plugin_data->ramp_curve) * 0.01f
            );

            v_mds_set_gain(&f_voice->mdist, *plugin_data->dist);

            int f_filter_type = (int)*plugin_data->filter_type;
            f_voice->svf_function = NOSVF_TYPES[f_filter_type];

            f_voice->noise_amp = f_db_to_linear(*(plugin_data->noise_amp));

            v_axf_set_xfade(
                &f_voice->mdist.dist_dry_wet,
                *(plugin_data->dist_wet) * 0.01f
            );

            f_voice->hard_sync = (int)(*plugin_data->sync_hard);

            v_osc_set_simple_osc_unison_type_v2(
                &f_voice->osc_unison1,
                (int)(*plugin_data->osc1type)
            );
            v_osc_set_simple_osc_unison_type_v2(
                &f_voice->osc_unison2,
                (int)(*plugin_data->osc2type)
            );

            v_nosvf_reset(&f_voice->svf_filter);

            if(f_poly_mode == POLY_MODE_RETRIG){
                v_osc_note_on_sync_phases(&f_voice->osc_unison1);
                v_osc_note_on_sync_phases(&f_voice->osc_unison2);
            }

            v_osc_set_uni_voice_count(
                &f_voice->osc_unison1,
                *plugin_data->uni_voice1
            );

            if(f_voice->hard_sync){
                v_osc_set_uni_voice_count(&f_voice->osc_unison2, 1);
            } else {
                v_osc_set_uni_voice_count(
                    &f_voice->osc_unison2,
                    *plugin_data->uni_voice2
                );
            }

            f_voice->adsr_prefx = (int)*plugin_data->adsr_prefx;

            plugin_data->sv_last_note = f_voice->note_f;
        } else {
            // 0 velocity, the same as note-off
            v_voc_note_off(
                &plugin_data->voices,
                a_event->note,
                plugin_data->sampleNo,
                a_event->tick
            );
        }
    } else if (a_event->type == EVENT_NOTEOFF){
        v_voc_note_off(
            &plugin_data->voices,
            a_event->note,
            plugin_data->sampleNo,
            a_event->tick
        );
    } else if (a_event->type == EVENT_CONTROLLER){
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_va1_process_midi_event: param %i out of range 1 to 128",
            a_event->param
        );

        v_plugin_event_queue_add(
            &plugin_data->midi_queue,
            EVENT_CONTROLLER,
            a_event->tick,
            a_event->value,
            a_event->param
        );

    } else if (a_event->type == EVENT_PITCHBEND){
        v_plugin_event_queue_add(
            &plugin_data->midi_queue,
            EVENT_PITCHBEND,
            a_event->tick,
            a_event->value * 0.00012207f,
            0
        );
    }
}

void v_run_va1(
    PluginHandle instance,
    int sample_count,
    struct ShdsList * midi_events,
    struct ShdsList * atm_events
){
    t_va1 *plugin_data = (t_va1 *) instance;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    v_plugin_event_queue_reset(&plugin_data->midi_queue);

    int f_poly_mode = (int)(*plugin_data->mono_mode);

    int midi_event_pos = 0;

    if(
        f_poly_mode == POLY_MODE_MONO
        &&
        plugin_data->voices.poly_mode != POLY_MODE_MONO
    ){
        va1Panic(instance);  //avoid hung notes
    }

    plugin_data->voices.poly_mode = f_poly_mode;

    int f_i;

    for(f_i = 0; f_i < event_count; ++f_i){
        v_va1_process_midi_event(plugin_data, events[f_i], f_poly_mode);
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_seq_event * ev_tmp;
    for(f_i = 0; f_i < atm_events->len; ++f_i){
        ev_tmp = (t_seq_event*)atm_events->data[f_i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue, ev_tmp->type,
            ev_tmp->tick, ev_tmp->value, ev_tmp->port);
    }

    plugin_data->main_vol_lin = f_db_to_linear_fast(*plugin_data->main_vol);

    int f_i2, f_i3;
    t_plugin_event_queue_item * f_midi_item;

    memset(
        plugin_data->os_buffer,
        0,
        sizeof(SGFLT) * sample_count * plugin_data->oversample
    );

    for(f_i = 0; f_i < sample_count; ++f_i){
        while(1){
            f_midi_item = v_plugin_event_queue_iter(
                &plugin_data->midi_queue,
                f_i
            );
            if(!f_midi_item){
                break;
            }

            if(f_midi_item->type == EVENT_PITCHBEND){
                plugin_data->sv_pitch_bend_value = f_midi_item->value;
            } else if(f_midi_item->type == EVENT_CONTROLLER){
                v_cc_map_translate(
                    &plugin_data->cc_map,
                    plugin_data->descriptor,
                    plugin_data->port_table,
                    f_midi_item->port,
                    f_midi_item->value
                );
            }

            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue,
            f_i,
            plugin_data->port_table
        );

        v_sml_run(
            &plugin_data->mono_modules.lfo_smoother,
            *plugin_data->lfo_freq
        );
        v_sml_run(
            &plugin_data->mono_modules.filter_smoother,
            *plugin_data->timbre
        );
        v_sml_run(
            &plugin_data->mono_modules.pitchbend_smoother,
            plugin_data->sv_pitch_bend_value
        );

        for(f_i2 = 0; f_i2 < VA1_POLYPHONY; ++f_i2){
            if(plugin_data->data[f_i2].adsr_amp.stage != ADSR_STAGE_OFF){
                for(f_i3 = 0; f_i3 < plugin_data->oversample; ++f_i3){
                    v_run_va1_voice(
                        plugin_data,
                        &plugin_data->voices.voices[f_i2],
                        &plugin_data->data[f_i2],
                        plugin_data->os_buffer,
                        f_i,
                        f_i3
                    );
                }
            } else {
                plugin_data->voices.voices[f_i2].n_state = note_state_off;
            }
        }

        ++plugin_data->sampleNo;
    }

    SGFLT f_avg;
    SGFLT *f_os_buffer = plugin_data->os_buffer;
    SGFLT *f_output0 = plugin_data->output0;
    SGFLT *f_output1 = plugin_data->output1;
    const int os_count = plugin_data->oversample;
    const SGFLT os_recip = plugin_data->os_recip;

    for(f_i = f_i2 = 0; f_i < sample_count; ++f_i){
        f_avg = 0.0f;
        for(f_i3 = 0; f_i3 < os_count; ++f_i3){
            f_avg += v_nosvf_run_6_pole_lp(
                &plugin_data->mono_modules.aa_filter,
                f_os_buffer[f_i2 + f_i3]
            );
        }

        v_sml_run(
            &plugin_data->mono_modules.pan_smoother,
            (*plugin_data->pan * 0.01f)
        );

        v_pn2_set(
            &plugin_data->mono_modules.panner,
            plugin_data->mono_modules.pan_smoother.last_value,
            -3.0
        );

        f_avg = f_avg * os_recip * 1.412429;
        f_output0[f_i] += f_avg * plugin_data->mono_modules.panner.gainL;
        f_output1[f_i] += f_avg * plugin_data->mono_modules.panner.gainR;
        f_i2 += os_count;
    }
}

void v_run_va1_voice(
    t_va1 *plugin_data,
    t_voc_single_voice * a_poly_voice,
    t_va1_poly_voice *a_voice,
    PluginData *out,
    int a_i,
    int a_no_events
){
    if((plugin_data->sampleNo) < (a_poly_voice->on))
    {
        return;
        //i_voice =  (a_poly_voice.on) - (plugin_data->sampleNo);
    }

    if (!a_no_events &&
       (plugin_data->sampleNo == a_poly_voice->off) &&
       ((a_voice->adsr_amp.stage) < ADSR_STAGE_RELEASE))
    {
        if(a_poly_voice->n_state == note_state_killed)
        {
            v_va1_poly_note_off(a_voice, 1);
        }
        else
        {
            v_va1_poly_note_off(a_voice, 0);
        }
    }

    SGFLT current_sample = 0.0f;

    f_rmp_run_ramp_curve(&a_voice->pitch_env);
    f_rmp_run_ramp(&a_voice->glide_env);

    v_lfs_set(
        &a_voice->lfo1,
        (plugin_data->mono_modules.lfo_smoother.last_value) * 0.01f
    );
    v_lfs_run(&a_voice->lfo1);
    a_voice->lfo_amp_output =
        f_db_to_linear_fast((((*plugin_data->lfo_amp) *
        (a_voice->lfo1.output)) - (f_sg_abs((*plugin_data->lfo_amp)) * 0.5)));
    a_voice->lfo_filter_output =
        (*plugin_data->lfo_filter) * (a_voice->lfo1.output);
    a_voice->lfo_pitch_output =
        (*plugin_data->lfo_pitch + (*plugin_data->lfo_pitch_fine * 0.01f))
        * (a_voice->lfo1.output);

    SGFLT f_pb = plugin_data->mono_modules.pitchbend_smoother.last_value;

    a_voice->base_pitch =
        (a_voice->glide_env.output_multiplied) +
        (a_voice->pitch_env.output_multiplied) +
        (a_voice->last_pitch) + (a_voice->lfo_pitch_output);

    if(a_voice->hard_sync)
    {
        v_osc_set_unison_pitch(
            &a_voice->osc_unison1,
            a_voice->unison_spread1,
            ((a_voice->target_pitch) + (a_voice->osc1_pitch_adjust) +
            (a_voice->osc1pb * f_pb))
        );
        v_osc_set_unison_pitch(
            &a_voice->osc_unison2,
            a_voice->unison_spread2,
            ((a_voice->base_pitch) + (a_voice->osc2_pitch_adjust) +
            (a_voice->osc2pb * f_pb))
        );

        current_sample += f_osc_run_unison_osc_sync(&a_voice->osc_unison2);

        if(a_voice->osc_unison2.is_resetting){
            v_osc_note_on_sync_phases_hard(&a_voice->osc_unison1);
        }

        current_sample += f_osc_run_unison_osc(
            &a_voice->osc_unison1
        ) * a_voice->osc1_linamp;

    } else {
        v_osc_set_unison_pitch(
            &a_voice->osc_unison1,
            (*plugin_data->uni_spread1) * 0.01f,
            ((a_voice->base_pitch) + (a_voice->osc1_pitch_adjust) +
            (a_voice->osc1pb * f_pb))
        );
        v_osc_set_unison_pitch(
            &a_voice->osc_unison2,
            (*plugin_data->uni_spread2) * 0.01f,
            ((a_voice->base_pitch) + (a_voice->osc2_pitch_adjust) +
            (a_voice->osc2pb * f_pb))
        );

        current_sample += f_osc_run_unison_osc(
            &a_voice->osc_unison1
        ) * a_voice->osc1_linamp;
        current_sample += f_osc_run_unison_osc(
            &a_voice->osc_unison2
        ) * a_voice->osc2_linamp;
    }

    current_sample += a_voice->noise_func_ptr(
        &a_voice->white_noise1
    ) * a_voice->noise_linamp;

    a_voice->adsr_run_func(&a_voice->adsr_amp);

    if(a_voice->adsr_prefx){
        current_sample *= (a_voice->adsr_amp.output);
    }

    v_adsr_run(&a_voice->adsr_filter);

    v_nosvf_set_cutoff_base(
        &a_voice->svf_filter,
        plugin_data->mono_modules.filter_smoother.last_value
    );

    v_nosvf_set_res(&a_voice->svf_filter, (*plugin_data->res) * 0.1f);

    v_nosvf_add_cutoff_mod(
        &a_voice->svf_filter,
        (
            (a_voice->adsr_filter.output * (*plugin_data->filter_env_amt)) +
            a_voice->lfo_filter_output + a_voice->filter_keytrk
        )
    );

    v_nosvf_set_cutoff(&a_voice->svf_filter);

    current_sample = a_voice->svf_function(
        &a_voice->svf_filter,
        current_sample
    );

    current_sample = a_voice->mdist_fp(
        &a_voice->mdist,
        current_sample,
        a_voice->dist_out_gain
    );

    current_sample = current_sample * a_voice->amp * a_voice->lfo_amp_output *
        plugin_data->main_vol_lin;

    if(!a_voice->adsr_prefx){
        current_sample *= a_voice->adsr_amp.output;
    }

    out[(a_i * plugin_data->oversample) + a_no_events] += current_sample;
}

PluginDescriptor *va1_plugin_descriptor(){
    PluginDescriptor *f_result = get_pyfx_descriptor(VA1_COUNT);

    set_pyfx_port(f_result, VA1_ATTACK, 10.0f, 0.0f, 200.0f);
    set_pyfx_port(f_result, VA1_DECAY, 10.0f, 10.0f, 200.0f);
    set_pyfx_port(f_result, VA1_SUSTAIN, 0.0f, -60.0f, 0.0f);
    set_pyfx_port(f_result, VA1_RELEASE, 50.0f, 10.0f, 400.0f);
    set_pyfx_port(f_result, VA1_TIMBRE, 124.0f, 20.0f, 124.0f);
    set_pyfx_port(f_result, VA1_RES, -120.0f, -300.0f, 0.0f);
    set_pyfx_port(f_result, VA1_DIST, 15.0f, 0.0f, 48.0f);
    set_pyfx_port(f_result, VA1_FILTER_ATTACK, 10.0f, 0.0f, 200.0f);
    set_pyfx_port(f_result, VA1_FILTER_DECAY, 50.0f, 10.0f, 200.0f);
    set_pyfx_port(f_result, VA1_FILTER_SUSTAIN, 100.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_FILTER_RELEASE, 50.0f, 10.0f, 400.0f);
    set_pyfx_port(f_result, VA1_NOISE_AMP, -30.0f, -60.0f, 0.0f);
    set_pyfx_port(f_result, VA1_FILTER_ENV_AMT, 0.0f, -100.0f, 100.0f);
    set_pyfx_port(f_result, VA1_DIST_WET, 0.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_OSC1_TYPE, 1.0f, 0.0f, 7.0f);
    set_pyfx_port(f_result, VA1_OSC1_PITCH, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_OSC1_TUNE, 0.0f, -100.0f, 100.0f);
    set_pyfx_port(f_result, VA1_OSC1_VOLUME, -6.0f, -30.0f, 0.0f);
    set_pyfx_port(f_result, VA1_OSC2_TYPE, 0.0f, 0.0f, 7.0f);
    set_pyfx_port(f_result, VA1_OSC2_PITCH, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_OSC2_TUNE, 0.0f, -100.0f, 100.0f);
    set_pyfx_port(f_result, VA1_OSC2_VOLUME, -6.0f, -30.0f, 0.0f);
    set_pyfx_port(f_result, VA1_MAIN_VOLUME, -6.0f, -30.0f, 12.0f);
    set_pyfx_port(f_result, VA1_UNISON_VOICES1, 1.0f, 1.0f, 7.0f);
    set_pyfx_port(f_result, VA1_UNISON_VOICES2, 1.0f, 1.0f, 7.0f);
    set_pyfx_port(f_result, VA1_UNISON_SPREAD1, 50.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_UNISON_SPREAD2, 50.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_MAIN_GLIDE, 0.0f,  0.0f, 200.0f);
    set_pyfx_port(f_result, VA1_MAIN_PITCHBEND_AMT, 18.0f, 0.0f,  36.0f);
    set_pyfx_port(f_result, VA1_PITCH_ENV_AMT, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_PITCH_ENV_TIME, 100.0f, 1.0f, 600.0f);
    set_pyfx_port(f_result, VA1_LFO_FREQ, 200.0f, 10.0f, 1600.0f);
    set_pyfx_port(f_result, VA1_LFO_TYPE, 0.0f, 0.0f, 2.0f);
    set_pyfx_port(f_result, VA1_LFO_AMP, 0.0f, -24.0f, 24.0f);
    set_pyfx_port(f_result, VA1_LFO_PITCH, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_LFO_FILTER, 0.0f, -48.0f, 48.0f);
    set_pyfx_port(f_result, VA1_OSC_HARD_SYNC, 0.0f, 0.0f, 1.0f);
    set_pyfx_port(f_result, VA1_RAMP_CURVE, 50.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_FILTER_KEYTRK, 0.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_MONO_MODE, 0.0f, 0.0f, 3.0f);
    set_pyfx_port(f_result, VA1_LFO_PHASE, 0.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_LFO_PITCH_FINE, 0.0f, -100.0f, 100.0f);
    set_pyfx_port(f_result, VA1_ADSR_PREFX, 0.0f, 0.0f, 1.0f);
    set_pyfx_port(f_result, VA1_MIN_NOTE, 0.0f, 0.0f, 120.0f);
    set_pyfx_port(f_result, VA1_MAX_NOTE, 120.0f, 0.0f, 120.0f);
    set_pyfx_port(f_result, VA1_MAIN_PITCH, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_NOISE_TYPE, 0.0f, 0.0f, 2.0f);
    set_pyfx_port(f_result, VA1_FILTER_TYPE, 0.0f, 0.0f, 8.0f);
    set_pyfx_port(f_result, VA1_FILTER_VELOCITY, 0.0f, 0.0f, 100.0f);
    set_pyfx_port(f_result, VA1_DIST_OUTGAIN, 0.0f, -1800.0f, 0.0f);
    set_pyfx_port(f_result, VA1_OSC1_PB, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_OSC2_PB, 0.0f, -36.0f, 36.0f);
    set_pyfx_port(f_result, VA1_DIST_TYPE, 0.0f, 0.0f, 2.0f);
    set_pyfx_port(f_result, VA1_ADSR_LIN_MAIN, 1.0f, 0.0f, 1.0f);
    set_pyfx_port(f_result, VA1_PAN, 0.0f, -100.0f, 100.0f);


    f_result->cleanup = v_cleanup_va1;
    f_result->connect_port = v_va1_connect_port;
    f_result->connect_buffer = v_va1_connect_buffer;
    f_result->instantiate = g_va1_instantiate;
    f_result->panic = va1Panic;
    f_result->load = v_va1_load;
    f_result->set_port_value = v_va1_set_port_value;
    f_result->set_cc_map = v_va1_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_run_va1;
    f_result->offline_render_prep = v_va1_or_prep;
    f_result->on_stop = v_va1_on_stop;

    return f_result;
}

void g_va1_poly_init(
    t_va1_poly_voice* f_voice,
    SGFLT a_sr,
    int voice_num
){
    g_osc_simple_unison_init(&f_voice->osc_unison1, a_sr, voice_num);
    g_osc_simple_unison_init(&f_voice->osc_unison2, a_sr, voice_num);

    f_voice->osc1_pitch_adjust = 0.0f;
    f_voice->osc2_pitch_adjust = 0.0f;

    g_nosvf_init(&f_voice->svf_filter, a_sr);

    g_mds_init(&f_voice->mdist);
    f_voice->mdist_fp = g_mds_get_fp(0);

    f_voice->filter_keytrk = 0.0f;

    g_adsr_init(&f_voice->adsr_amp, a_sr);
    g_adsr_init(&f_voice->adsr_filter, a_sr);

    g_white_noise_init(&f_voice->white_noise1, a_sr);
    f_voice->noise_amp = 0;
    f_voice->noise_func_ptr = f_run_noise_off;

    g_rmp_init(&f_voice->glide_env, a_sr);
    g_rmp_init(&f_voice->pitch_env, a_sr);

    //f_voice->real_pitch = 60.0f;

    f_voice->target_pitch = 66.0f;
    f_voice->last_pitch = 66.0f;
    f_voice->base_pitch = 66.0f;

    g_rmp_init(&f_voice->glide_env, a_sr);
    g_lfs_init(&f_voice->lfo1, a_sr);

    f_voice->lfo_amp_output = 0.0f;
    f_voice->lfo_filter_output = 0.0f;
    f_voice->lfo_pitch_output = 0.0f;

    f_voice->amp = 1.0f;
    f_voice->note_f = 1.0f;
    f_voice->osc1_linamp = 1.0f;
    f_voice->osc2_linamp = 1.0f;
    f_voice->noise_linamp = 1.0f;

    f_voice->hard_sync = 0;
    f_voice->adsr_prefx = 0;
    f_voice->unison_spread1 = 0.5f;
    f_voice->unison_spread2 = 0.5f;
}

void v_va1_poly_note_off(t_va1_poly_voice * a_voice, int a_fast){
    if(a_fast){
        v_adsr_set_fast_release(&a_voice->adsr_amp);
    } else {
        v_adsr_release(&a_voice->adsr_amp);
    }

    v_adsr_release(&a_voice->adsr_filter);
}

/*Initialize any modules that will be run monophonically*/
void v_va1_mono_init(t_va1_mono_modules* a_mono, SGFLT a_sr){
    g_sml_init(&a_mono->filter_smoother, a_sr, 124.0f, 20.0f, 0.2f);
    g_sml_init(&a_mono->lfo_smoother, a_sr, 1600.0f, 10.0f, 0.2f);
    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    //To prevent low volume and brightness at the first note-on(s)
    a_mono->filter_smoother.last_value = 100.0f;
    a_mono->pan_smoother.last_value = 0.0f;
    g_sml_init(&a_mono->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.1f);
    g_pn2_init(&a_mono->panner);
    g_nosvf_init(&a_mono->aa_filter, a_sr);

    v_nosvf_set_cutoff_base(&a_mono->aa_filter, 120.0f);
    v_nosvf_add_cutoff_mod(&a_mono->aa_filter, 0.0f);
    v_nosvf_set_res(&a_mono->aa_filter, -6.0f);
    v_nosvf_set_cutoff(&a_mono->aa_filter);
}
