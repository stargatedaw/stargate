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
#include "plugins/vocoder.h"


void v_sg_vocoder_cleanup(PluginHandle instance){
    free(instance);
}

void v_sg_vocoder_set_cc_map(PluginHandle instance, char * a_msg){
    t_sg_vocoder *plugin = (t_sg_vocoder *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sg_vocoder_panic(PluginHandle instance){
    //t_sg_vocoder *plugin = (t_sg_vocoder*)instance;
}

void v_sg_vocoder_on_stop(PluginHandle instance){
    //t_sg_vocoder *plugin = (t_sg_vocoder*)instance;
}

void v_sg_vocoder_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_sg_vocoder *plugin = (t_sg_vocoder*)instance;

    switch (port)
    {
        case SG_VOCODER_WET: plugin->wet = data; break;
        case SG_VOCODER_MODULATOR: plugin->modulator = data; break;
        case SG_VOCODER_CARRIER: plugin->carrier = data; break;
        default:
            sg_abort(
                "v_sg_vocoder_connect_port: unknown port %i",
                port
            );
            break;
    }
}

PluginHandle g_sg_vocoder_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sg_vocoder *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sg_vocoder));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_sg_vocoder_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sg_vocoder_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
){
    t_sg_vocoder *plugin_data = (t_sg_vocoder*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_sg_vocoder_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_sg_vocoder *plugin_data = (t_sg_vocoder*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_sg_vocoder_process_midi_event(
    t_sg_vocoder* plugin_data,
    t_seq_event* a_event,
    int midi_channel
){
    int is_in_channel = midi_event_is_in_channel(
        a_event->channel,
        midi_channel
    );
    if(!is_in_channel){
        return;
    }
    if (a_event->type == EVENT_CONTROLLER){
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_sg_vocoder_process_midi_event: param %i out of range",
            a_event->param
        );

        v_plugin_event_queue_add(
            &plugin_data->midi_queue,
            EVENT_CONTROLLER,
            a_event->tick,
            a_event->value,
            a_event->param
        );
    }
}


void v_sg_vocoder_process_midi(
    PluginHandle instance,
    struct ShdsList * events,
    struct ShdsList * atm_events,
    int midi_channel
){
    t_sg_vocoder *plugin_data = (t_sg_vocoder*)instance;
    int f_i = 0;
    v_plugin_event_queue_reset(&plugin_data->midi_queue);

    for(f_i = 0; f_i < events->len; ++f_i){
        v_sg_vocoder_process_midi_event(
            plugin_data,
            (t_seq_event*)events->data[f_i],
            midi_channel
        );
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_seq_event * ev_tmp;
    for(f_i = 0; f_i < atm_events->len; ++f_i){
        ev_tmp = (t_seq_event*)atm_events->data[f_i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue,
            ev_tmp->type,
            ev_tmp->tick,
            ev_tmp->value,
            ev_tmp->port
        );
    }
}

void v_sg_vocoder_run(
    PluginHandle instance,
    enum PluginRunMode run_mode,
    int sample_count,
    struct SamplePair* input_buffer,
    struct SamplePair* sc_buffer,
    struct SamplePair* output_buffer,
    struct ShdsList* midi_events,
    struct ShdsList * atm_events,
    t_pkm_peak_meter* peak_meter,
    int midi_channel
){
    t_sg_vocoder *plugin_data = (t_sg_vocoder*)instance;
    struct SamplePair sample;

    t_plugin_event_queue_item * f_midi_item;
    v_sg_vocoder_process_midi(instance, midi_events, atm_events, midi_channel);

    int midi_event_pos = 0;
    int f_i = 0;

    t_smoother_linear * f_wet_smoother =
        &plugin_data->mono_modules.wet_smoother;
    t_smoother_linear * f_carrier_smoother =
        &plugin_data->mono_modules.carrier_smoother;
    t_smoother_linear * f_modulator_smoother =
        &plugin_data->mono_modules.modulator_smoother;

    SGFLT carrier_amp, modulator_amp, wet_amp;

    for(f_i = 0; f_i < sample_count; ++f_i){
        while(1){
            f_midi_item = v_plugin_event_queue_iter(
                &plugin_data->midi_queue,
                f_i
            );
            if(!f_midi_item){
                break;
            }

            if(f_midi_item->type == EVENT_CONTROLLER){
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

        v_vdr_run(
            &plugin_data->mono_modules.vocoder,
            sc_buffer[f_i].left,
            sc_buffer[f_i].right,
            input_buffer[f_i].left,
            input_buffer[f_i].right
        );

        v_sml_run(f_carrier_smoother, *plugin_data->carrier);
        carrier_amp = f_db_to_linear_fast(
            f_carrier_smoother->last_value * 0.1f
        );

        v_sml_run(f_wet_smoother, *plugin_data->wet);
        wet_amp = f_db_to_linear_fast(f_wet_smoother->last_value * 0.1f);

        sample.left = (
            input_buffer[f_i].left * carrier_amp
        ) + (
            plugin_data->mono_modules.vocoder.output0 * wet_amp
        );
        sample.right = (
            input_buffer[f_i].right * carrier_amp
        ) + (
            plugin_data->mono_modules.vocoder.output1 * wet_amp
        );

        if(*plugin_data->modulator >= -499.0f){
            v_sml_run(f_modulator_smoother, *plugin_data->modulator);
            modulator_amp = f_db_to_linear_fast(
                f_modulator_smoother->last_value * 0.1f
            );
            sample.left += sc_buffer[f_i].left * modulator_amp;
            sample.right += sc_buffer[f_i].right * modulator_amp;
        }
        _plugin_mix(
            run_mode,
            f_i,
            output_buffer,
            sample.left,
            sample.right
        );
    }
}

SGFLT* sg_vocoder_get_port_table(PluginHandle instance){
    t_sg_vocoder* plugin_data = (t_sg_vocoder*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sg_vocoder_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SG_VOCODER_COUNT);

    set_plugin_port(f_result, SG_VOCODER_WET, 0.0f, -500.0f, 0.0f);
    set_plugin_port(f_result, SG_VOCODER_MODULATOR, -500.0f, -500.0f, 0.0f);
    set_plugin_port(f_result, SG_VOCODER_CARRIER, -500.0f, -500.0f, 0.0f);

    f_result->cleanup = v_sg_vocoder_cleanup;
    f_result->connect_port = v_sg_vocoder_connect_port;
    f_result->get_port_table = sg_vocoder_get_port_table;
    f_result->instantiate = g_sg_vocoder_instantiate;
    f_result->panic = v_sg_vocoder_panic;
    f_result->load = v_sg_vocoder_load;
    f_result->set_port_value = v_sg_vocoder_set_port_value;
    f_result->set_cc_map = v_sg_vocoder_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_sg_vocoder_run;
    f_result->on_stop = v_sg_vocoder_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}


void v_sg_vocoder_mono_init(
    t_sg_vocoder_mono_modules * a_mono,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_sml_init(&a_mono->wet_smoother, a_sr, 0.0f, -500.0f, 0.1f);
    g_vdr_init(&a_mono->vocoder, a_sr);
    g_sml_init(&a_mono->carrier_smoother, a_sr, 0.0f, -500.0f, 0.1f);
    g_sml_init(&a_mono->modulator_smoother, a_sr, 0.0f, -500.0f, 0.1f);
}

/*
void v_sg_vocoder_destructor()
{
    if (f_result) {
        free((PluginPortDescriptor *) f_result->PortDescriptors);
        free((char **) f_result->PortNames);
        free((PluginPortRangeHint *) f_result->PortRangeHints);
        free(f_result);
    }
    if (SGDDescriptor) {
        free(SGDDescriptor);
    }
}
*/
