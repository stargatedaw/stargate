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

    g_get_port_table(
        (void**)plugin_data,
        descriptor
    );

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sg_comp_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
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

void v_sg_comp_run(
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
    t_sg_comp *plugin_data = (t_sg_comp*)instance;
    int f_is_rms = (int)(plugin_data->port_table[SG_COMP_MODE]);
    t_cmp_compressor * f_cmp = &plugin_data->mono_modules.compressor;
    SGFLT f_gain = f_db_to_linear_fast(
        plugin_data->port_table[SG_COMP_GAIN] * 0.1
    );
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

        v_cmp_set(
            f_cmp,
            plugin_data->port_table[SG_COMP_THRESHOLD] * 0.1f,
            plugin_data->port_table[SG_COMP_RATIO] * 0.1f,
            plugin_data->port_table[SG_COMP_KNEE] * 0.1f,
            plugin_data->port_table[SG_COMP_ATTACK] * 0.001f,
            plugin_data->port_table[SG_COMP_RELEASE] * 0.001f,
            plugin_data->port_table[SG_COMP_GAIN] * 0.1f
        );

        if(f_is_rms){
            v_cmp_set_rms(
                f_cmp,
                plugin_data->port_table[SG_COMP_RMS_TIME] * 0.01f
            );
            v_cmp_run_rms(
                f_cmp,
                input_buffer[i].left,
                input_buffer[i].right
            );
        } else {
            v_cmp_run(
                f_cmp,
                input_buffer[i].left,
                input_buffer[i].right
            );
        }

        _plugin_mix(
            run_mode,
            i,
            output_buffer,
            f_cmp->output0 * f_gain,
            f_cmp->output1 * f_gain
        );
    }

    if((int)(plugin_data->port_table[SG_COMP_UI_MSG_ENABLED])){
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

SGFLT* sgcomp_get_port_table(PluginHandle instance){
    t_sg_comp *plugin_data = (t_sg_comp*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sg_comp_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SG_COMP_COUNT);

    set_plugin_port(f_result, SG_COMP_THRESHOLD, -120.0f, -360.0f, -60.0f);
    set_plugin_port(f_result, SG_COMP_RATIO, 20.0f, 10.0f, 100.0f);
    set_plugin_port(f_result, SG_COMP_KNEE, 0.0f, 0.0f, 120.0f);
    set_plugin_port(f_result, SG_COMP_ATTACK, 50.0f, 0.0f, 500.0f);
    set_plugin_port(f_result, SG_COMP_RELEASE, 100.0f, 10.0f, 500.0f);
    set_plugin_port(f_result, SG_COMP_GAIN, 0.0f, -360.0f, 360.0f);
    set_plugin_port(f_result, SG_COMP_MODE, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, SG_COMP_RMS_TIME, 2.0f, 1.0f, 5.0f);
    set_plugin_port(f_result, SG_COMP_UI_MSG_ENABLED, 0.0f, 0.0f, 1.0f);

    f_result->cleanup = v_sg_comp_cleanup;
    f_result->connect_port = NULL;
    f_result->get_port_table = sgcomp_get_port_table;
    f_result->instantiate = g_sg_comp_instantiate;
    f_result->panic = v_sg_comp_panic;
    f_result->load = v_sg_comp_load;
    f_result->set_port_value = v_sg_comp_set_port_value;
    f_result->set_cc_map = v_sg_comp_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_sg_comp_run;
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
    if (SGDDescriptor) {
        free(SGDDescriptor);
    }
}
*/
