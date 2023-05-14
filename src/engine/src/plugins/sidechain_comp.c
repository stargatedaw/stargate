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
#include "plugins/sidechain_comp.h"


void v_scc_cleanup(PluginHandle instance)
{
    free(instance);
}

void v_scc_set_cc_map(PluginHandle instance, char * a_msg)
{
    t_scc *plugin = (t_scc *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_scc_panic(PluginHandle instance)
{
    //t_scc *plugin = (t_scc*)instance;
}

void v_scc_on_stop(PluginHandle instance)
{
    //t_scc *plugin = (t_scc*)instance;
}

void v_scc_connect_port(
    PluginHandle instance,
    int port,
    PluginData* data
){
    t_scc *plugin;

    plugin = (t_scc*)instance;

    switch (port){
        case SCC_THRESHOLD: plugin->threshold = data; break;
        case SCC_RATIO: plugin->ratio = data; break;
        case SCC_ATTACK: plugin->attack = data; break;
        case SCC_RELEASE: plugin->release = data; break;
        case SCC_WET: plugin->wet = data; break;
        case SCC_UI_MSG_ENABLED: plugin->peak_meter = data; break;
    }
}

PluginHandle g_scc_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_scc *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_scc));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_scc_mono_init(
        &plugin_data->mono_modules,
        s_rate,
        a_plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_scc_load(
    PluginHandle instance,
    PluginDescriptor* Descriptor,
    SGPATHSTR* a_file_path
){
    t_scc *plugin_data = (t_scc*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_scc_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_scc *plugin_data = (t_scc*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_scc_run(
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
    t_scc *plugin_data = (t_scc*)instance;
    t_scc_sidechain_comp * f_cmp = &plugin_data->mono_modules.sidechain_comp;
    int f_i;

    effect_translate_midi_events(
        midi_events,
        &plugin_data->midi_events,
        &plugin_data->atm_queue,
        atm_events,
        midi_channel
    );

    for(f_i = 0; f_i < sample_count; ++f_i){
        effect_process_events(
            f_i,
            &plugin_data->midi_events,
            plugin_data->port_table,
            plugin_data->descriptor,
            &plugin_data->cc_map,
            &plugin_data->atm_queue
        );

        v_scc_set(
            f_cmp,
            *plugin_data->threshold,
            (*plugin_data->ratio) * 0.1f,
            *plugin_data->attack * 0.001f,
            *plugin_data->release * 0.001f,
            *plugin_data->wet * 0.01f
        );

        v_scc_run_comp(
            f_cmp,
            sc_buffer[f_i].left,
            sc_buffer[f_i].right,
            input_buffer[f_i].left,
            input_buffer[f_i].right
        );

        _plugin_mix(
            run_mode,
            f_i,
            output_buffer,
            f_cmp->output0,
            f_cmp->output1
        );
    }

    if((int)(*plugin_data->peak_meter)){
        if(f_cmp->peak_tracker.dirty){
            sg_snprintf(
                plugin_data->ui_msg_buff,
                64,
                "%i|gain|%f",
                plugin_data->plugin_uid,
                f_cmp->peak_tracker.gain_redux
            );
            plugin_data->queue_func("ui", plugin_data->ui_msg_buff);
            v_pkm_redux_lin_reset(&f_cmp->peak_tracker);
        }
    }
}

SGFLT* scc_get_port_table(PluginHandle instance){
    t_scc* plugin_data = (t_scc*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *scc_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SCC_COUNT);

    set_plugin_port(f_result, SCC_THRESHOLD, -24.0f, -36.0f, -6.0f);
    set_plugin_port(f_result, SCC_RATIO, 20.0f, 1.0f, 100.0f);
    set_plugin_port(f_result, SCC_ATTACK, 20.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, SCC_RELEASE, 50.0f, 20.0f, 300.0f);
    set_plugin_port(f_result, SCC_WET, 100.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, SCC_UI_MSG_ENABLED, 0.0f, 0.0f, 1.0f);

    f_result->cleanup = v_scc_cleanup;
    f_result->connect_port = v_scc_connect_port;
    f_result->get_port_table = scc_get_port_table;
    f_result->instantiate = g_scc_instantiate;
    f_result->panic = v_scc_panic;
    f_result->load = v_scc_load;
    f_result->set_port_value = v_scc_set_port_value;
    f_result->set_cc_map = v_scc_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_scc_run;
    f_result->on_stop = v_scc_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_scc_mono_init(
    t_scc_mono_modules* f_result,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_scc_init(&f_result->sidechain_comp, a_sr);
}

/*
void v_scc_destructor()
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
