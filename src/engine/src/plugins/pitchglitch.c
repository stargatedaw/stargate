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
#include "plugins/pitchglitch.h"


void run_pitchglitch_voice(
    t_pitchglitch *plugin_data,
    t_voc_single_voice * a_poly_voice,
    struct PitchGlitchPolyVoice *a_voice,
    struct SamplePair* out,
    int a_i,
    int a_no_events
);

void v_cleanup_pitchglitch(PluginHandle instance){
    free(instance);
}

void v_pitchglitch_set_cc_map(PluginHandle instance, char * a_msg){
    t_pitchglitch *plugin = (t_pitchglitch *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void pitchglitchPanic(PluginHandle instance){
    t_pitchglitch *plugin = (t_pitchglitch*)instance;
    for(int i = 0; i < PITCHGLITCH_POLYPHONY; ++i){
        plugin->voices.voices[i].n_state = note_state_off;
    }
}

void v_pitchglitch_on_stop(PluginHandle instance){
    t_pitchglitch *plugin = (t_pitchglitch *)instance;

    for(int i = 0; i < PITCHGLITCH_POLYPHONY; ++i){
        plugin->voices.voices[i].n_state = note_state_off;
    }
    plugin->sv_pitch_bend_value = 0.0f;
}

void v_pitchglitch_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_pitchglitch* plugin = (t_pitchglitch*)instance;

    switch (port){
        case PITCHGLITCH_MODE: plugin->controls.mode = data; break;
        case PITCHGLITCH_PITCHBEND: plugin->controls.pitchbend = data; break;
        case PITCHGLITCH_DRY_WET: plugin->controls.dry_wet = data; break;
        case PITCHGLITCH_VEL_MIN: plugin->controls.vel_min = data; break;
        case PITCHGLITCH_VEL_MAX: plugin->controls.vel_max = data; break;
        case PITCHGLITCH_PAN: plugin->controls.pan = data; break;
        case PITCHGLITCH_PITCH: plugin->controls.pitch = data; break;
        case PITCHGLITCH_GLIDE: plugin->controls.glide = data; break;
        default:
            sg_abort(
                "v_pitchglitch_connect_port: unknown port %i",
                port
            );
            break;
    }
}

NO_OPTIMIZATION PluginHandle g_pitchglitch_instantiate(
    PluginDescriptor * descriptor,
    int a_sr,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_pitchglitch *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_pitchglitch));
    plugin_data->fs = a_sr;

    g_voc_voices_init(
        &plugin_data->voices,
        PITCHGLITCH_POLYPHONY,
        PITCHGLITCH_POLYPHONY_THRESH
    );

    for(int i = 0; i < PITCHGLITCH_POLYPHONY; ++i){
        g_pitchglitch_poly_init(&plugin_data->voice_data[i], a_sr, i);
        plugin_data->voice_data[i].note_f = i;
    }

    plugin_data->sampleNo = 0;

    plugin_data->sv_pitch_bend_value = 0.0f;
    plugin_data->sv_last_note = -1.0f;  //For glide

    PitchGlitchMonoInit(&plugin_data->mono_modules, plugin_data->fs);

    g_get_port_table((void**)plugin_data, descriptor);
    plugin_data->descriptor = descriptor;

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle)plugin_data;
}

void v_pitchglitch_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
){
    t_pitchglitch *plugin_data = (t_pitchglitch*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_pitchglitch_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_pitchglitch *plugin_data = (t_pitchglitch*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void pitchglitch_note_on(
    t_pitchglitch * plugin_data,
    t_seq_event * a_event,
    int f_poly_mode
){
    int f_voice_num = i_pick_voice(
        &plugin_data->voices,
        a_event->note,
        plugin_data->sampleNo,
        a_event->tick
    );

    struct PitchGlitchPolyVoice* f_voice =
        &plugin_data->voice_data[f_voice_num];
    poly_glitch_trigger(&f_voice->glitch);
    v_pn2_set_normalize(
        &f_voice->panner,
        a_event->pan,
        -3.0
    );

    //-20db to 0db, + main volume (0 to -60)
    f_voice->amp = f_db_to_linear_fast(
        ((a_event->velocity * 0.094488) - 12.0f)
    );

    SGFLT f_main_pitch = (*plugin_data->controls.pitch);

    f_voice->note_f = (SGFLT)a_event->note + f_main_pitch +
        a_event->pitch_fine;
    f_voice->note = a_event->note + (int)(f_main_pitch);

    f_voice->target_pitch = f_voice->note_f;

    if(plugin_data->sv_last_note < 0.0f){
        f_voice->last_pitch = (f_voice->note_f);
    } else {
        f_voice->last_pitch = (plugin_data->sv_last_note);
    }

    v_rmp_retrigger_glide_t(
        &f_voice->glide_env,
        (*(plugin_data->controls.glide) * 0.01f),
        f_voice->last_pitch,
        f_voice->target_pitch
    );

    plugin_data->sv_last_note = f_voice->note_f;
}

void v_pitchglitch_process_midi_event(
    t_pitchglitch * plugin_data,
    t_seq_event * a_event,
    int f_poly_mode,
    int midi_channel
){
    int is_in_channel = midi_event_is_in_channel(
        a_event->channel,
        midi_channel
    );
    if(!is_in_channel){
        return;
    }
    if (a_event->type == EVENT_NOTEON){
        if (a_event->velocity > 0){
            pitchglitch_note_on(plugin_data, a_event, f_poly_mode);
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
            a_event->param >= 1 && a_event->param <= 127,
            "v_pitchglitch_process_midi_event: param %i out of range 1 to 127",
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

void v_run_pitchglitch(
    PluginHandle instance,
    enum PluginRunMode run_mode,
    int sample_count,
    struct SamplePair* input_buffer,
    struct SamplePair* sc_buffer,
    struct SamplePair* output_buffer,
    struct ShdsList* midi_events,
    struct ShdsList* atm_events,
    t_pkm_peak_meter* peak_meter,
    int midi_channel
){
    t_pitchglitch* plugin_data = (t_pitchglitch*) instance;
    struct SamplePair sample;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    v_plugin_event_queue_reset(&plugin_data->midi_queue);

    int midi_event_pos = 0;

    plugin_data->voices.poly_mode = POLY_MODE_RETRIG;

    for(int i = 0; i < event_count; ++i){
        v_pitchglitch_process_midi_event(
            plugin_data,
            events[i],
            POLY_MODE_RETRIG,
            midi_channel
        );
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_seq_event * ev_tmp;
    for(int i = 0; i < atm_events->len; ++i){
        ev_tmp = (t_seq_event*)atm_events->data[i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue,
            ev_tmp->type,
            ev_tmp->tick,
            ev_tmp->value,
            ev_tmp->port
        );
    }

    t_plugin_event_queue_item * f_midi_item;

    for(int i = 0; i < sample_count; ++i){
        sample = (struct SamplePair){};
        while(1){
            f_midi_item = v_plugin_event_queue_iter(
                &plugin_data->midi_queue,
                i
            );
            if(!f_midi_item){
                break;
            }

            if(f_midi_item->type == EVENT_PITCHBEND){
                plugin_data->sv_pitch_bend_value =
                    f_midi_item->value * (*plugin_data->controls.pitchbend);
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
            i,
            plugin_data->port_table
        );

        v_sml_run(
            &plugin_data->mono_modules.pitchbend_smoother,
            plugin_data->sv_pitch_bend_value
        );
        v_sml_run(
            &plugin_data->mono_modules.dry_wet_smoother,
            (*plugin_data->controls.dry_wet) * 0.01
        );

        int has_voices = 0;
        for(int j = 0; j < PITCHGLITCH_POLYPHONY; ++j){
            if(plugin_data->voices.voices[j].n_state != note_state_off){
                has_voices = 1;
                v_run_pitchglitch_voice(
                    plugin_data,
                    &plugin_data->voices.voices[j],
                    &plugin_data->voice_data[j],
                    input_buffer[i],
                    &sample
                );
            }
        }
        if(has_voices){
            sample = stereo_dc_filter_run(
                &plugin_data->mono_modules.dc_filter,
                sample
            );

            v_axf_set_xfade(
                &plugin_data->mono_modules.dry_wet,
                plugin_data->mono_modules.dry_wet_smoother.last_value
            );
            sample.left = f_axf_run_xfade(
                &plugin_data->mono_modules.dry_wet,
                input_buffer[i].left,
                sample.left
            );
            sample.right = f_axf_run_xfade(
                &plugin_data->mono_modules.dry_wet,
                input_buffer[i].right,
                sample.right
            );
        } else {
            sample = input_buffer[i];
            stereo_dc_filter_reset(&plugin_data->mono_modules.dc_filter);
        }
        _plugin_mix(
            run_mode,
            i,
            output_buffer,
            sample.left,
            sample.right
        );

        ++plugin_data->sampleNo;
    }
}

void v_run_pitchglitch_voice(
    t_pitchglitch *plugin_data,
    t_voc_single_voice * a_poly_voice,
    struct PitchGlitchPolyVoice *a_voice,
    struct SamplePair input,
    struct SamplePair* out
){
    if((plugin_data->sampleNo) < (a_poly_voice->on)){
        return;
        //i_voice =  (a_poly_voice.on) - (plugin_data->sampleNo);
    }

    if(plugin_data->sampleNo == a_poly_voice->off){
        a_poly_voice->n_state = note_state_off;
    }

    struct SamplePair current_sample = {};

    f_rmp_run_ramp(&a_voice->glide_env);
    SGFLT f_pb = plugin_data->mono_modules.pitchbend_smoother.last_value;

    a_voice->base_pitch =
        a_voice->glide_env.output_multiplied +
        a_voice->pitch_env.output_multiplied +
        a_voice->last_pitch;

    poly_glitch_set(&a_voice->glitch, a_voice->base_pitch + f_pb);
    current_sample = poly_glitch_run(&a_voice->glitch, input);

    out->left += current_sample.left * a_voice->panner.gainL * a_voice->amp;
    out->right += current_sample.right * a_voice->panner.gainR * a_voice->amp;
}

SGFLT* pitchglitch_get_port_table(PluginHandle instance){
    t_pitchglitch* plugin_data = (t_pitchglitch*)instance;
    return plugin_data->port_table;
}

PluginDescriptor* PitchGlitchPluginDescriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(PITCHGLITCH_COUNT);

    set_plugin_port(f_result, PITCHGLITCH_MODE, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, PITCHGLITCH_PITCHBEND, 12.0f, 0.0f, 36.0f);
    set_plugin_port(f_result, PITCHGLITCH_DRY_WET, 100.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, PITCHGLITCH_VEL_MIN, -12.0f, -36.0f, 0.0f);
    set_plugin_port(f_result, PITCHGLITCH_VEL_MAX, 6.0f, 0.0f, 12.0f);
    set_plugin_port(f_result, PITCHGLITCH_PAN, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, PITCHGLITCH_PITCH, 0.0f, -36.0f, 36.0f);
    set_plugin_port(f_result, PITCHGLITCH_GLIDE, 0.0f, 0.0f, 100.0f);

    f_result->cleanup = v_cleanup_pitchglitch;
    f_result->connect_port = v_pitchglitch_connect_port;
    f_result->get_port_table = pitchglitch_get_port_table;
    f_result->instantiate = g_pitchglitch_instantiate;
    f_result->panic = pitchglitchPanic;
    f_result->load = v_pitchglitch_load;
    f_result->set_port_value = v_pitchglitch_set_port_value;
    f_result->set_cc_map = v_pitchglitch_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_run_pitchglitch;
    f_result->offline_render_prep = NULL;
    f_result->on_stop = v_pitchglitch_on_stop;

    return f_result;
}

void g_pitchglitch_poly_init(
    struct PitchGlitchPolyVoice* f_voice,
    SGFLT a_sr,
    int voice_num
){
    poly_glitch_init(&f_voice->glitch, a_sr);
    g_pn2_init(&f_voice->panner);

    g_rmp_init(&f_voice->glide_env, a_sr);
    g_rmp_init(&f_voice->pitch_env, a_sr);

    f_voice->target_pitch = 66.0f;
    f_voice->last_pitch = 66.0f;
    f_voice->base_pitch = 66.0f;

    f_voice->amp = 1.0f;
    f_voice->note_f = 1.0f;
}

/*Initialize any modules that will be run monophonically*/
void PitchGlitchMonoInit(
    struct PitchGlitchMonoModules* self,
    SGFLT a_sr
){
    g_sml_init(&self->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    //To prevent low volume and brightness at the first note-on(s)
    self->pan_smoother.last_value = 0.0f;
    g_sml_init(&self->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.1f);
    g_pn2_init(&self->panner);
    stereo_dc_filter_init(&self->dc_filter, a_sr);
    g_axf_init(&self->dry_wet, -2.0);
    g_sml_init(&self->dry_wet_smoother, a_sr, 1.0f, 0.0f, 1.0f);
}

