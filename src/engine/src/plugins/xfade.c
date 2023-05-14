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
#include "audiodsp/modules/delay/reverb.h"
#include "plugins/xfade.h"


void v_xfade_cleanup(PluginHandle instance)
{
    free(instance);
}

void v_xfade_set_cc_map(PluginHandle instance, char * a_msg)
{
    t_xfade *plugin = (t_xfade *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_xfade_panic(PluginHandle instance)
{
    //t_xfade *plugin = (t_xfade*)instance;
}

void v_xfade_on_stop(PluginHandle instance)
{
    //t_xfade *plugin = (t_xfade*)instance;
}

void v_xfade_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_xfade *plugin;

    plugin = (t_xfade *) instance;

    switch (port)
    {
        case XFADE_SLIDER: plugin->pan = data; break;
        case XFADE_MIDPOINT: plugin->pan_law = data; break;
    }
}

PluginHandle g_xfade_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_xfade *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_xfade));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_xfade_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);
    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_xfade_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
){
    t_xfade *plugin_data = (t_xfade*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

void v_xfade_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_xfade *plugin_data = (t_xfade*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_xfade_process_midi_event(
    t_xfade * plugin_data,
    t_seq_event * a_event,
    int midi_channel
){
    int is_in_channel = midi_event_is_in_channel(
        a_event->channel,
        midi_channel
    );
    if(!is_in_channel){
        return;
    }
    if (a_event->type == EVENT_CONTROLLER)
    {
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_xfade_process_midi_event: param %i out of range 1 to 128",
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


void v_xfade_process_midi(
    PluginHandle instance,
    struct ShdsList* events,
    struct ShdsList* atm_events,
    int midi_channel
){
    t_xfade *plugin_data = (t_xfade*)instance;
    int f_i = 0;

    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < events->len; ++f_i){
        v_xfade_process_midi_event(
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

void v_xfade_run(
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
    t_xfade *plugin_data = (t_xfade*)instance;

    v_xfade_process_midi(instance, midi_events, atm_events, midi_channel);

    int midi_event_pos = 0;
    int f_i = 0;

    SGFLT f_pan_law = (*plugin_data->pan_law) * 0.01f;
    struct SamplePair sample;

    for(f_i = 0; f_i < sample_count; ++f_i){
        sample.left = input_buffer[f_i].left;
        sample.right = input_buffer[f_i].right;
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
            &plugin_data->mono_modules.pan_smoother,
            (*plugin_data->pan * 0.01f)
        );

        v_pn2_set(
            &plugin_data->mono_modules.panner,
            plugin_data->mono_modules.pan_smoother.last_value,
            f_pan_law
        );

        sample.left *= plugin_data->mono_modules.panner.gainL;
        sample.right *= plugin_data->mono_modules.panner.gainL;
        _plugin_mix(
            run_mode,
            f_i,
            output_buffer,
            sample.left + (
                sc_buffer[f_i].left *
                plugin_data->mono_modules.panner.gainR
            ),
            sample.right + (
                sc_buffer[f_i].right *
                plugin_data->mono_modules.panner.gainR
            )
        );
    }
}

SGFLT* xfade_get_port_table(PluginHandle instance){
    t_xfade* plugin_data = (t_xfade*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *xfade_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(XFADE_COUNT);

    set_plugin_port(f_result, XFADE_SLIDER, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, XFADE_MIDPOINT, -300.0f, -600.0f, 0.0f);

    f_result->cleanup = v_xfade_cleanup;
    f_result->connect_port = v_xfade_connect_port;
    f_result->get_port_table = xfade_get_port_table;
    f_result->instantiate = g_xfade_instantiate;
    f_result->panic = v_xfade_panic;
    f_result->load = v_xfade_load;
    f_result->set_port_value = v_xfade_set_port_value;
    f_result->set_cc_map = v_xfade_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_xfade_run;
    f_result->on_stop = v_xfade_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_xfade_mono_init(
     t_xfade_mono_modules* a_mono,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    a_mono->pan_smoother.last_value = 0.0f;
}

/*
void v_xfade_destructor()
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
