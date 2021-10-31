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
#include "audiodsp/modules/filter/svf.h"
#include "plugin.h"
#include "plugins/delay.h"

void v_sgdelay_cleanup(PluginHandle instance){
    free(instance);
}

void v_sgdelay_set_cc_map(PluginHandle instance, char * a_msg){
    t_sgdelay *plugin = (t_sgdelay *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sgdelay_panic(PluginHandle instance)
{
    t_sgdelay *plugin = (t_sgdelay*)instance;

    int f_i = 0;
    while(f_i < plugin->mono_modules.delay->delay0.sample_count)
    {
        plugin->mono_modules.delay->delay0.buffer[f_i] = 0.0f;
        plugin->mono_modules.delay->delay1.buffer[f_i] = 0.0f;
        ++f_i;
    }
}

void v_sgdelay_on_stop(PluginHandle instance)
{
    //t_sgdelay *plugin = (t_sgdelay*)instance;
}

void v_sgdelay_connect_buffer(
    PluginHandle instance,
    int a_index,
    SGFLT * DataLocation,
    int a_is_sidechain
){
    if(a_is_sidechain)
    {
        return;
    }

    t_sgdelay *plugin = (t_sgdelay*)instance;

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
                "v_sgdelay_connect_buffer: unknown port %i",
                a_index
            );
            break;
    }
}

void v_sgdelay_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_sgdelay *plugin;

    plugin = (t_sgdelay *) instance;

    switch (port)
    {
        case SGDELAY_DELAY_TIME: plugin->delay_time = data; break;
        case SGDELAY_FEEDBACK: plugin->feedback = data; break;
        case SGDELAY_DRY: plugin->dry = data;  break;
        case SGDELAY_WET: plugin->wet = data; break;
        case SGDELAY_DUCK: plugin->duck = data; break;
        case SGDELAY_CUTOFF: plugin->cutoff = data; break;
        case SGDELAY_STEREO: plugin->stereo = data; break;
    }
}

PluginHandle g_sgdelay_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sgdelay *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sgdelay));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;


    v_sgdelay_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sgdelay_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    char * a_file_path
){
    t_sgdelay *plugin_data = (t_sgdelay*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

void v_sgdelay_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_sgdelay *plugin_data = (t_sgdelay*)Instance;
    plugin_data->port_table[a_port] = a_value;
}


void v_sgdelay_process_midi_event(
    t_sgdelay * plugin_data,
    t_seq_event * a_event
){
    if (a_event->type == EVENT_CONTROLLER)
    {
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_sgdelay_process_midi_event: param %i out of range 1 to 128",
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

void v_sgdelay_run(
        PluginHandle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_sgdelay *plugin_data = (t_sgdelay*)instance;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int f_i;

    int midi_event_pos = 0;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_sgdelay_process_midi_event(plugin_data, events[f_i]);
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
            &plugin_data->atm_queue, f_i,
            plugin_data->port_table);

        v_sml_run(
            &plugin_data->mono_modules.time_smoother,
            (*(plugin_data->delay_time))
        );

        v_ldl_set_delay(plugin_data->mono_modules.delay,
            (plugin_data->mono_modules.time_smoother.last_value * 0.01f),
            (*plugin_data->feedback) * 0.1f,
            (*plugin_data->wet) * 0.1f, (*plugin_data->dry) * 0.1f,
            (*(plugin_data->stereo) * .01), (*plugin_data->duck),
            (*plugin_data->cutoff));

        v_ldl_run_delay(plugin_data->mono_modules.delay,
                (plugin_data->output0[(f_i)]),
                (plugin_data->output1[(f_i)]));

        plugin_data->output0[(f_i)] =
                (plugin_data->mono_modules.delay->output0);
        plugin_data->output1[(f_i)] =
                (plugin_data->mono_modules.delay->output1);

        ++f_i;
    }
}

PluginDescriptor *sgdelay_plugin_descriptor(){
    PluginDescriptor *f_result = get_pyfx_descriptor(SGDELAY_COUNT);

    set_pyfx_port(f_result, SGDELAY_DELAY_TIME, 50.0f, 10.0f, 100.0f);
    set_pyfx_port(f_result, SGDELAY_FEEDBACK, -120.0f, -200.0f, 0.0f);
    set_pyfx_port(f_result, SGDELAY_DRY, 0.0f, -300.0f, 0.0f);
    set_pyfx_port(f_result, SGDELAY_WET, -120.0f, -300.0f, 0.0f);
    set_pyfx_port(f_result, SGDELAY_DUCK, -20.0f, -40.0f, 0.0f);
    set_pyfx_port(f_result, SGDELAY_CUTOFF, 90.0f, 40.0f, 118.0f);
    set_pyfx_port(f_result, SGDELAY_STEREO, 100.0f, 0.0f, 100.0f);


    f_result->cleanup = v_sgdelay_cleanup;
    f_result->connect_port = v_sgdelay_connect_port;
    f_result->connect_buffer = v_sgdelay_connect_buffer;
    f_result->instantiate = g_sgdelay_instantiate;
    f_result->panic = v_sgdelay_panic;
    f_result->load = v_sgdelay_load;
    f_result->set_port_value = v_sgdelay_set_port_value;
    f_result->set_cc_map = v_sgdelay_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_sgdelay_run;
    f_result->on_stop = v_sgdelay_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_sgdelay_mono_init(
    t_sgdelay_mono_modules* a_mono,
    SGFLT a_sr,
    int a_plugin_uid
){
    a_mono->delay = g_ldl_get_delay(1, a_sr);
    g_sml_init(
        &a_mono->time_smoother,
        a_sr,
        100.0f,
        10.0f,
        0.1f
    );

    a_mono->vol_linear = 1.0f;
}

/*
void v_sgdelay_destructor()
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
