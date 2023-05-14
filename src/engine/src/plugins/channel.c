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


void v_sgchnl_cleanup(PluginHandle instance){
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

PluginHandle g_sgchnl_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sgchnl *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sgchnl));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_sgchnl_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sgchnl_load(
    PluginHandle instance,
    PluginDescriptor* Descriptor,
    SGPATHSTR* a_file_path
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

void v_sgchnl_run(
    PluginHandle instance,
    enum PluginRunMode run_mode,
    int sample_count,
    struct SamplePair* input_buffers,
    struct SamplePair* sc_buffers,
    struct SamplePair* output_buffers,
    struct ShdsList* midi_events,
    struct ShdsList * atm_events,
    t_pkm_peak_meter* peak_meter,
    int midi_channel
){
    t_sgchnl *plugin_data = (t_sgchnl*)instance;
    float left, right;

    effect_translate_midi_events(
        midi_events,
        &plugin_data->midi_events,
        &plugin_data->atm_queue,
        atm_events,
        midi_channel
    );

    SGFLT f_vol_linear;
    SGFLT f_gain = f_db_to_linear_fast(
        plugin_data->port_table[SGCHNL_GAIN] * 0.01f
    );
    SGFLT f_pan_law = plugin_data->port_table[SGCHNL_LAW] * 0.01f;

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
            &plugin_data->mono_modules.volume_smoother,
            (plugin_data->port_table[SGCHNL_VOL_SLIDER] * 0.01f)
        );

        v_sml_run(
            &plugin_data->mono_modules.pan_smoother,
            plugin_data->port_table[SGCHNL_PAN] * 0.01f
        );

        v_pn2_set(
            &plugin_data->mono_modules.panner,
            plugin_data->mono_modules.pan_smoother.last_value,
            f_pan_law
        );

        f_vol_linear = f_db_to_linear_fast(
            plugin_data->mono_modules.volume_smoother.last_value - f_pan_law
        );

        left = input_buffers[i].left *
            f_vol_linear * f_gain * plugin_data->mono_modules.panner.gainL;
        right = input_buffers[i].right *
            f_vol_linear * f_gain * plugin_data->mono_modules.panner.gainR;
        if(peak_meter){
            v_pkm_run_single(
                peak_meter,
                left,
                right
            );
        }

        _plugin_mix(
            run_mode,
            i,
            output_buffers,
            left,
            right
        );
    }
}

SGFLT* sgchnl_get_port_table(PluginHandle instance){
    t_sgchnl *plugin_data = (t_sgchnl*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sgchnl_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SGCHNL_COUNT);

    set_plugin_port(f_result, SGCHNL_VOL_SLIDER, 0.0f, -5000.0f, 0.0f);
    set_plugin_port(f_result, SGCHNL_GAIN, 0.0f, -2400.0f, 2400.0f);
    set_plugin_port(f_result, SGCHNL_PAN, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, SGCHNL_LAW, -300.0f, -600.0f, 0.0f);

    f_result->cleanup = v_sgchnl_cleanup;
    f_result->connect_port = NULL;
    f_result->get_port_table = sgchnl_get_port_table;
    f_result->instantiate = g_sgchnl_instantiate;
    f_result->panic = v_sgchnl_panic;
    f_result->load = v_sgchnl_load;
    f_result->set_port_value = v_sgchnl_set_port_value;
    f_result->set_cc_map = v_sgchnl_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_sgchnl_run;
    f_result->on_stop = v_sgchnl_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_sgchnl_mono_init(
    t_sgchnl_mono_modules* a_mono,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_sml_init(&a_mono->volume_smoother, a_sr, 0.0f, -50.0f, 0.1f);
    a_mono->volume_smoother.last_value = 0.0f;
    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    a_mono->pan_smoother.last_value = 0.0f;
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
    if (SGDDescriptor) {
        free(SGDDescriptor);
    }
}
*/
