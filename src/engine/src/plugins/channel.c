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

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/peak_meter.h"
#include "plugin.h"
#include "plugins/channel.h"


void v_sgchnl_cleanup(PluginHandle instance)
{
    free(instance);
}

void v_sgchnl_set_cc_map(PluginHandle instance, char * a_msg)
{
    t_sgchnl *plugin = (t_sgchnl *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sgchnl_panic(PluginHandle instance)
{
    //t_sgchnl *plugin = (t_sgchnl*)instance;
}

void v_sgchnl_on_stop(PluginHandle instance)
{
    //t_sgchnl *plugin = (t_sgchnl*)instance;
}

void v_sgchnl_connect_buffer(
    PluginHandle instance,
    int a_index,
    SGFLT * DataLocation,
    int a_is_sidechain
){
    if(a_is_sidechain){
        return;
    }

    t_sgchnl *plugin = (t_sgchnl*)instance;
    plugin->buffers[a_index] = DataLocation;
}

void v_sgchnl_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_sgchnl *plugin;

    plugin = (t_sgchnl *) instance;

    switch (port)
    {
        case SGCHNL_VOL_SLIDER: plugin->vol_slider = data; break;
        case SGCHNL_GAIN: plugin->gain = data; break;
        case SGCHNL_PAN: plugin->pan = data; break;
        case SGCHNL_LAW: plugin->pan_law = data; break;
    }
}

PluginHandle g_sgchnl_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sgchnl *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sgchnl));
    hpalloc((void**)&plugin_data->buffers, sizeof(SGFLT*) * 2);

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->mono_modules =
            v_sgchnl_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sgchnl_load(
    PluginHandle instance,
    PluginDescriptor* Descriptor,
    char* a_file_path
){
    t_sgchnl *plugin_data = (t_sgchnl*)instance;
    generic_file_loader(
        instance, Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_sgchnl_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_sgchnl *plugin_data = (t_sgchnl*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_sgchnl_process_midi_event(
    t_sgchnl * plugin_data,
    t_seq_event * a_event
){
    if (a_event->type == EVENT_CONTROLLER)
    {
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_sgchnl_process_midi_event: param %i out of range 1 to 128",
            a_event->param
        );

        plugin_data->midi_event_types[plugin_data->midi_event_count] =
                EVENT_CONTROLLER;
        plugin_data->midi_event_ticks[plugin_data->midi_event_count] =
                a_event->tick;
        plugin_data->midi_event_ports[plugin_data->midi_event_count] =
                a_event->param;
        plugin_data->midi_event_values[plugin_data->midi_event_count] =
                a_event->value;

        ++plugin_data->midi_event_count;
    }
}

void v_sgchnl_process_midi(
    PluginHandle instance,
    struct ShdsList * events,
    struct ShdsList * atm_events
){
    t_sgchnl *plugin_data = (t_sgchnl*)instance;
    int f_i = 0;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < events->len; ++f_i)
    {
        v_sgchnl_process_midi_event(
            plugin_data, (t_seq_event*)events->data[f_i]);
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_seq_event * ev_tmp;
    for(f_i = 0; f_i < atm_events->len; ++f_i)
    {
        ev_tmp = (t_seq_event*)atm_events->data[f_i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue, ev_tmp->type,
            ev_tmp->tick, ev_tmp->value, ev_tmp->port);
    }
}


void v_sgchnl_run_mixing(
    PluginHandle instance,
    int sample_count,
    SGFLT ** output_buffers,
    int output_count,
    struct ShdsList* midi_events,
    struct ShdsList * atm_events,
    t_pkm_peak_meter* peak_meter
){
    t_sgchnl *plugin_data = (t_sgchnl*)instance;
    float left, right;

    v_sgchnl_process_midi(instance, midi_events, atm_events);

    SGFLT f_vol_linear;
    SGFLT f_gain = f_db_to_linear_fast((*plugin_data->gain) * 0.01f);
    SGFLT f_pan_law = (*plugin_data->pan_law) * 0.01f;

    int midi_event_pos = 0;
    int f_i;

    for(f_i = 0; f_i < sample_count; ++f_i){
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

        v_sml_run(
            &plugin_data->mono_modules->volume_smoother,
            (*plugin_data->vol_slider * 0.01f)
        );

        v_sml_run(
            &plugin_data->mono_modules->pan_smoother,
            (*plugin_data->pan * 0.01f)
        );

        v_pn2_set(
            &plugin_data->mono_modules->panner,
            plugin_data->mono_modules->pan_smoother.last_value,
            f_pan_law
        );

        f_vol_linear = f_db_to_linear_fast(
            plugin_data->mono_modules->volume_smoother.last_value - f_pan_law
        );

        left = plugin_data->buffers[0][f_i] *
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainL;
        right = plugin_data->buffers[1][f_i] *
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainR;
        if(peak_meter){
            v_pkm_run_single(
                peak_meter,
                left,
                right
            );
        }
        output_buffers[0][f_i] += left;
        output_buffers[1][f_i] += right;
    }
}

void v_sgchnl_run(
    PluginHandle instance,
    int sample_count,
    struct ShdsList* midi_events,
    struct ShdsList * atm_events
){
    t_sgchnl *plugin_data = (t_sgchnl*)instance;

    v_sgchnl_process_midi(instance, midi_events, atm_events);

    int midi_event_pos = 0;
    int f_i;

    SGFLT f_vol_linear;

    SGFLT f_gain = f_db_to_linear_fast((*plugin_data->gain) * 0.01f);
    SGFLT f_pan_law = (*plugin_data->pan_law) * 0.01f;

    for(f_i = 0; f_i < sample_count; ++f_i){
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
                    plugin_data->midi_event_values[midi_event_pos]);
            }
            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue,
            f_i,
            plugin_data->port_table
        );

        v_sml_run(
            &plugin_data->mono_modules->volume_smoother,
            (*plugin_data->vol_slider * 0.01f)
        );

        v_sml_run(
            &plugin_data->mono_modules->pan_smoother,
            (*plugin_data->pan * 0.01f)
        );

        v_pn2_set(
            &plugin_data->mono_modules->panner,
            plugin_data->mono_modules->pan_smoother.last_value,
            f_pan_law
        );

        f_vol_linear = f_db_to_linear_fast(
            (plugin_data->mono_modules->volume_smoother.last_value)
        );

        plugin_data->buffers[0][f_i] *=
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainL;
        plugin_data->buffers[1][f_i] *=
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainR;
    }
}

PluginDescriptor *sgchnl_plugin_descriptor(){
    PluginDescriptor *f_result = get_pyfx_descriptor(SGCHNL_COUNT);

    set_pyfx_port(f_result, SGCHNL_VOL_SLIDER, 0.0f, -5000.0f, 0.0f);
    set_pyfx_port(f_result, SGCHNL_GAIN, 0.0f, -2400.0f, 2400.0f);
    set_pyfx_port(f_result, SGCHNL_PAN, 0.0f, -100.0f, 100.0f);
    set_pyfx_port(f_result, SGCHNL_LAW, -300.0f, -600.0f, 0.0f);

    f_result->cleanup = v_sgchnl_cleanup;
    f_result->connect_port = v_sgchnl_connect_port;
    f_result->connect_buffer = v_sgchnl_connect_buffer;
    f_result->instantiate = g_sgchnl_instantiate;
    f_result->panic = v_sgchnl_panic;
    f_result->load = v_sgchnl_load;
    f_result->set_port_value = v_sgchnl_set_port_value;
    f_result->set_cc_map = v_sgchnl_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_sgchnl_run;
    f_result->run_mixing = v_sgchnl_run_mixing;
    f_result->on_stop = v_sgchnl_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

t_sgchnl_mono_modules * v_sgchnl_mono_init(SGFLT a_sr, int a_plugin_uid)
{
    t_sgchnl_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_sgchnl_mono_modules));

    g_sml_init(&a_mono->volume_smoother, a_sr, 0.0f, -50.0f, 0.1f);
    a_mono->volume_smoother.last_value = 0.0f;
    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    a_mono->pan_smoother.last_value = 0.0f;

    return a_mono;
}



/*
void v_sgchnl_destructor()
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
