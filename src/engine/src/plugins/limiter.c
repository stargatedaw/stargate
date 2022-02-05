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
#include "plugins/limiter.h"


void v_sg_lim_cleanup(PluginHandle instance)
{
    free(instance);
}

void v_sg_lim_set_cc_map(PluginHandle instance, char * a_msg)
{
    t_sg_lim *plugin = (t_sg_lim *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sg_lim_panic(PluginHandle instance)
{
    //t_sg_lim *plugin = (t_sg_lim*)instance;
}

void v_sg_lim_on_stop(PluginHandle instance)
{
    //t_sg_lim *plugin = (t_sg_lim*)instance;
}

void v_sg_lim_connect_buffer(
    PluginHandle instance,
    struct SamplePair* DataLocation,
    int a_is_sidechain
){
    t_sg_lim *plugin = (t_sg_lim*)instance;

    if(!a_is_sidechain){
        plugin->output = DataLocation;
    }
}

PluginHandle g_sg_lim_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sg_lim *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sg_lim));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_sg_lim_mono_init(
        &plugin_data->mono_modules,
        s_rate,
        a_plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sg_lim_load(PluginHandle instance,
        PluginDescriptor * Descriptor, char * a_file_path)
{
    t_sg_lim *plugin_data = (t_sg_lim*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

void v_sg_lim_set_port_value(PluginHandle Instance,
        int a_port, SGFLT a_value)
{
    t_sg_lim *plugin_data = (t_sg_lim*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_sg_lim_process_midi_event(
    t_sg_lim * plugin_data,
    t_seq_event * a_event
){
    if (a_event->type == EVENT_CONTROLLER)
    {
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_sg_lim_process_midi_event: param %i out of range 1 to 128",
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

void v_sg_lim_run(
        PluginHandle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_sg_lim *plugin_data = (t_sg_lim*)instance;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int f_i = 0;
    int midi_event_pos = 0;
    t_lim_limiter * f_lim = &plugin_data->mono_modules.limiter;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_sg_lim_process_midi_event(plugin_data, events[f_i]);
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

    f_i = 0;

    while(f_i < sample_count)
    {
        while(midi_event_pos < plugin_data->midi_event_count &&
                plugin_data->midi_event_ticks[midi_event_pos] == f_i)
        {
            if(plugin_data->midi_event_types[midi_event_pos] ==
                    EVENT_CONTROLLER)
            {
                v_cc_map_translate(
                    &plugin_data->cc_map, plugin_data->descriptor,
                    plugin_data->port_table,
                    plugin_data->midi_event_ports[midi_event_pos],
                    plugin_data->midi_event_values[midi_event_pos]);
            }
            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue, f_i, plugin_data->port_table);

        v_lim_set(
            f_lim,
            plugin_data->port_table[SG_LIM_THRESHOLD] * 0.1f,
            plugin_data->port_table[SG_LIM_CEILING] * 0.1f,
            plugin_data->port_table[SG_LIM_RELEASE]
        );

        v_lim_run(
            f_lim,
            plugin_data->output[f_i].left,
            plugin_data->output[f_i].right
        );

        plugin_data->output[f_i].left = f_lim->output0;
        plugin_data->output[f_i].right = f_lim->output1;
        ++f_i;
    }

    if((int)(plugin_data->port_table[SG_LIM_UI_MSG_ENABLED])){
        if(f_lim->peak_tracker.dirty){
            sprintf(
                plugin_data->ui_msg_buff,
                "%i|gain|%f",
                plugin_data->plugin_uid,
                f_lim->peak_tracker.gain_redux
            );
            plugin_data->queue_func("ui", plugin_data->ui_msg_buff);
            v_pkm_redux_lin_reset(&f_lim->peak_tracker);
        }
    }
}


SGFLT* sglim_get_port_table(PluginHandle instance){
    t_sg_lim *plugin_data = (t_sg_lim*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sg_lim_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SG_LIM_COUNT);

    set_plugin_port(f_result, SG_LIM_THRESHOLD, 0.0f, -360.0f, 0.0f);
    set_plugin_port(f_result, SG_LIM_CEILING, 0.0f, -180.0f, 0.0f);
    set_plugin_port(f_result, SG_LIM_RELEASE, 500.0f, 50.0f, 1500.0f);
    set_plugin_port(f_result, SG_LIM_UI_MSG_ENABLED, 0.0f, 0.0f, 1.0f);

    f_result->cleanup = v_sg_lim_cleanup;
    f_result->connect_port = NULL;
    f_result->connect_buffer = v_sg_lim_connect_buffer;
    f_result->get_port_table = sglim_get_port_table;
    f_result->instantiate = g_sg_lim_instantiate;
    f_result->panic = v_sg_lim_panic;
    f_result->load = v_sg_lim_load;
    f_result->set_port_value = v_sg_lim_set_port_value;
    f_result->set_cc_map = v_sg_lim_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_sg_lim_run;
    f_result->on_stop = v_sg_lim_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_sg_lim_mono_init(
    t_sg_lim_mono_modules* f_result,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_lim_init(&f_result->limiter, a_sr, 1);
}

/*
void v_sg_lim_destructor()
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
