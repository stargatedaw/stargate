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
#include "plugins/compressor.h"


void v_sg_comp_cleanup(PluginHandle instance){
    free(instance);
}

void v_sg_comp_set_cc_map(PluginHandle instance, char* a_msg){
    t_sg_comp *plugin = (t_sg_comp *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sg_comp_panic(PluginHandle instance){
    //t_sg_comp *plugin = (t_sg_comp*)instance;
}

void v_sg_comp_on_stop(PluginHandle instance){
    //t_sg_comp *plugin = (t_sg_comp*)instance;
}

void v_sg_comp_connect_buffer(
    PluginHandle instance,
    int a_index,
    SGFLT * DataLocation,
    int a_is_sidechain
){
    t_sg_comp* plugin = (t_sg_comp*)instance;

    if(!a_is_sidechain){
        switch(a_index){
            case 0:
                plugin->output0 = DataLocation;
                break;
            case 1:
                plugin->output1 = DataLocation;
                break;
            default:
                sg_assert(
                    0,
                    "v_sg_comp_connect_buffer: unknown port %i",
                    a_index
                );
                break;
        }
    }
}

void v_sg_comp_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_sg_comp *plugin;

    plugin = (t_sg_comp *) instance;

    switch (port){
        case SG_COMP_THRESHOLD: plugin->threshold = data; break;
        case SG_COMP_RATIO: plugin->ratio = data; break;
        case SG_COMP_KNEE: plugin->knee = data; break;
        case SG_COMP_ATTACK: plugin->attack = data; break;
        case SG_COMP_RELEASE: plugin->release = data; break;
        case SG_COMP_GAIN: plugin->gain = data; break;
        case SG_COMP_MODE: plugin->mode = data; break;
        case SG_COMP_RMS_TIME: plugin->rms_time = data; break;
        case SG_COMP_UI_MSG_ENABLED: plugin->peak_meter = data; break;
    }
}

PluginHandle g_sg_comp_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sg_comp *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sg_comp));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_sg_comp_mono_init(
        &plugin_data->mono_modules,
        s_rate,
        a_plugin_uid
    );

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data,
        descriptor
    );

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sg_comp_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    char * a_file_path
){
    t_sg_comp *plugin_data = (t_sg_comp*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_sg_comp_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_sg_comp *plugin_data = (t_sg_comp*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_sg_comp_process_midi_event(
    t_sg_comp * plugin_data,
    t_seq_event * a_event
){
    if(a_event->type == EVENT_CONTROLLER){
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_sg_comp_process_midi_event: param %i out of range 1 to 128",
            a_event->param
        );

        int c = plugin_data->midi_event_count;
        plugin_data->midi_event_types[c] = EVENT_CONTROLLER;
        plugin_data->midi_event_ticks[c] = a_event->tick;
        plugin_data->midi_event_ports[c] = a_event->param;
        plugin_data->midi_event_values[c] = a_event->value;

        ++plugin_data->midi_event_count;
    }
}

void v_sg_comp_run(
    PluginHandle instance,
    int sample_count,
    struct ShdsList* midi_events,
    struct ShdsList * atm_events
){
    t_sg_comp *plugin_data = (t_sg_comp*)instance;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int f_i = 0;
    int midi_event_pos = 0;
    int f_is_rms = (int)(*plugin_data->mode);
    t_cmp_compressor * f_cmp = &plugin_data->mono_modules.compressor;
    SGFLT f_gain = f_db_to_linear_fast((*plugin_data->gain) * 0.1f);
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < event_count; ++f_i){
        v_sg_comp_process_midi_event(plugin_data, events[f_i]);
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

    f_i = 0;

    while(f_i < sample_count){
        while(
            midi_event_pos < plugin_data->midi_event_count
            &&
            plugin_data->midi_event_ticks[midi_event_pos] == f_i
        ){
            if(
                plugin_data->midi_event_types[midi_event_pos]
                ==
                EVENT_CONTROLLER
            ){
                v_cc_map_translate(
                    &plugin_data->cc_map, plugin_data->descriptor,
                    plugin_data->port_table,
                    plugin_data->midi_event_ports[midi_event_pos],
                    plugin_data->midi_event_values[midi_event_pos]
                );
            }
            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue,
            f_i,
            plugin_data->port_table
        );

        v_cmp_set(
            f_cmp,
            *plugin_data->threshold * 0.1f,
            (*plugin_data->ratio) * 0.1f,
            *plugin_data->knee * 0.1f,
            *plugin_data->attack * 0.001f,
            *plugin_data->release * 0.001f,
            *plugin_data->gain * 0.1f
        );

        if(f_is_rms){
            v_cmp_set_rms(f_cmp, (*plugin_data->rms_time) * 0.01f);
            v_cmp_run_rms(
                f_cmp,
                plugin_data->output0[f_i],
                plugin_data->output1[f_i]
            );
        } else {
            v_cmp_run(
                f_cmp,
                plugin_data->output0[f_i],
                plugin_data->output1[f_i]
            );
        }

        plugin_data->output0[f_i] = f_cmp->output0 * f_gain;
        plugin_data->output1[f_i] = f_cmp->output1 * f_gain;
        ++f_i;
    }

    if((int)(*plugin_data->peak_meter)){
        if(f_cmp->peak_tracker.dirty){
            sprintf(
                plugin_data->ui_msg_buff,
                "%i|gain|%f",
                plugin_data->plugin_uid,
                f_cmp->peak_tracker.gain_redux
            );
            plugin_data->queue_func("ui", plugin_data->ui_msg_buff);
            v_pkm_redux_lin_reset(&f_cmp->peak_tracker);
        }
    }
}


PluginDescriptor *sg_comp_plugin_descriptor(){
    PluginDescriptor *f_result = get_pyfx_descriptor(SG_COMP_COUNT);

    set_pyfx_port(f_result, SG_COMP_THRESHOLD, -120.0f, -360.0f, -60.0f);
    set_pyfx_port(f_result, SG_COMP_RATIO, 20.0f, 10.0f, 100.0f);
    set_pyfx_port(f_result, SG_COMP_KNEE, 0.0f, 0.0f, 120.0f);
    set_pyfx_port(f_result, SG_COMP_ATTACK, 50.0f, 0.0f, 500.0f);
    set_pyfx_port(f_result, SG_COMP_RELEASE, 100.0f, 10.0f, 500.0f);
    set_pyfx_port(f_result, SG_COMP_GAIN, 0.0f, -360.0f, 360.0f);
    set_pyfx_port(f_result, SG_COMP_MODE, 0.0f, 0.0f, 1.0f);
    set_pyfx_port(f_result, SG_COMP_RMS_TIME, 2.0f, 1.0f, 5.0f);
    set_pyfx_port(f_result, SG_COMP_UI_MSG_ENABLED, 0.0f, 0.0f, 1.0f);

    f_result->cleanup = v_sg_comp_cleanup;
    f_result->connect_port = v_sg_comp_connect_port;
    f_result->connect_buffer = v_sg_comp_connect_buffer;
    f_result->instantiate = g_sg_comp_instantiate;
    f_result->panic = v_sg_comp_panic;
    f_result->load = v_sg_comp_load;
    f_result->set_port_value = v_sg_comp_set_port_value;
    f_result->set_cc_map = v_sg_comp_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_sg_comp_run;
    f_result->on_stop = v_sg_comp_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_sg_comp_mono_init(
    t_sg_comp_mono_modules* f_result,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_cmp_init(&f_result->compressor, a_sr);
}

/*
void v_sg_comp_destructor()
{
    if (f_result) {
        free((PluginPortDescriptor *) f_result->PortDescriptors);
        free((char **) f_result->PortNames);
        free((PluginPortRangeHint *) f_result->PortRangeHints);
        free(f_result);
    }
    if (LMSDDescriptor) {
        free(LMSDDescriptor);
    }
}
*/
