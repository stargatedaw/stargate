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

    for(int i = 0; i < plugin->mono_modules.delay->delay0.sample_count; ++i){
        plugin->mono_modules.delay->delay0.buffer[i] = 0.0f;
        plugin->mono_modules.delay->delay1.buffer[i] = 0.0f;
    }
}

void v_sgdelay_on_stop(PluginHandle instance)
{
    //t_sgdelay *plugin = (t_sgdelay*)instance;
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

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sgdelay_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
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

void v_sgdelay_run(
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
    t_sgdelay *plugin_data = (t_sgdelay*)instance;

    effect_translate_midi_events(
        midi_events,
        &plugin_data->midi_events,
        &plugin_data->atm_queue,
        atm_events,
        midi_channel
    );

    for(int i = 0; i < sample_count; ++i){
        effect_process_events(
            i,
            &plugin_data->midi_events,
            plugin_data->port_table,
            plugin_data->descriptor,
            &plugin_data->cc_map,
            &plugin_data->atm_queue
        );

        v_sml_run(
            &plugin_data->mono_modules.time_smoother,
            plugin_data->port_table[SGDELAY_DELAY_TIME]
        );

        v_ldl_set_delay(plugin_data->mono_modules.delay,
            plugin_data->mono_modules.time_smoother.last_value * 0.01f,
            plugin_data->port_table[SGDELAY_FEEDBACK] * 0.1f,
            plugin_data->port_table[SGDELAY_WET] * 0.1f,
            plugin_data->port_table[SGDELAY_DRY] * 0.1f,
            plugin_data->port_table[SGDELAY_STEREO] * .01,
            plugin_data->port_table[SGDELAY_DUCK],
            plugin_data->port_table[SGDELAY_CUTOFF]
        );

        v_ldl_run_delay(plugin_data->mono_modules.delay,
            input_buffer[i].left,
            input_buffer[i].right
        );

        _plugin_mix(
            run_mode,
            i,
            output_buffer,
            plugin_data->mono_modules.delay->output0,
            plugin_data->mono_modules.delay->output1
        );
    }
}

SGFLT* sgdelay_get_port_table(PluginHandle instance){
    t_sgdelay *plugin_data = (t_sgdelay*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sgdelay_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SGDELAY_COUNT);

    set_plugin_port(f_result, SGDELAY_DELAY_TIME, 50.0f, 10.0f, 100.0f);
    set_plugin_port(f_result, SGDELAY_FEEDBACK, -120.0f, -200.0f, 0.0f);
    set_plugin_port(f_result, SGDELAY_DRY, 0.0f, -300.0f, 0.0f);
    set_plugin_port(f_result, SGDELAY_WET, -120.0f, -300.0f, 0.0f);
    set_plugin_port(f_result, SGDELAY_DUCK, -20.0f, -40.0f, 0.0f);
    set_plugin_port(f_result, SGDELAY_CUTOFF, 90.0f, 40.0f, 118.0f);
    set_plugin_port(f_result, SGDELAY_STEREO, 100.0f, 0.0f, 100.0f);

    f_result->cleanup = v_sgdelay_cleanup;
    f_result->connect_port = NULL;
    f_result->get_port_table = sgdelay_get_port_table;
    f_result->instantiate = g_sgdelay_instantiate;
    f_result->panic = v_sgdelay_panic;
    f_result->load = v_sgdelay_load;
    f_result->set_port_value = v_sgdelay_set_port_value;
    f_result->set_cc_map = v_sgdelay_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_sgdelay_run;
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
    if (SGDDescriptor) {
        free(SGDDescriptor);
    }
}
*/
