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
#include "audiodsp/lib/spectrum_analyzer.h"
#include "plugins/eq.h"


void v_sgeq_cleanup(PluginHandle instance)
{
    free(instance);
}

void v_sgeq_set_cc_map(PluginHandle instance, char * a_msg)
{
    t_sgeq *plugin = (t_sgeq *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sgeq_panic(PluginHandle instance)
{
    //t_sgeq *plugin = (t_sgeq*)instance;
}

void v_sgeq_on_stop(PluginHandle instance)
{
    //t_sgeq *plugin = (t_sgeq*)instance;
}

void v_sgeq_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_sgeq *plugin;

    plugin = (t_sgeq *) instance;

    switch (port){
        case SGEQ_EQ1_FREQ: plugin->eq_freq[0] = data; break;
        case SGEQ_EQ2_FREQ: plugin->eq_freq[1] = data; break;
        case SGEQ_EQ3_FREQ: plugin->eq_freq[2] = data; break;
        case SGEQ_EQ4_FREQ: plugin->eq_freq[3] = data; break;
        case SGEQ_EQ5_FREQ: plugin->eq_freq[4] = data; break;
        case SGEQ_EQ6_FREQ: plugin->eq_freq[5] = data; break;

        case SGEQ_EQ1_RES: plugin->eq_res[0] = data; break;
        case SGEQ_EQ2_RES: plugin->eq_res[1] = data; break;
        case SGEQ_EQ3_RES: plugin->eq_res[2] = data; break;
        case SGEQ_EQ4_RES: plugin->eq_res[3] = data; break;
        case SGEQ_EQ5_RES: plugin->eq_res[4] = data; break;
        case SGEQ_EQ6_RES: plugin->eq_res[5] = data; break;

        case SGEQ_EQ1_GAIN: plugin->eq_gain[0] = data; break;
        case SGEQ_EQ2_GAIN: plugin->eq_gain[1] = data; break;
        case SGEQ_EQ3_GAIN: plugin->eq_gain[2] = data; break;
        case SGEQ_EQ4_GAIN: plugin->eq_gain[3] = data; break;
        case SGEQ_EQ5_GAIN: plugin->eq_gain[4] = data; break;
        case SGEQ_EQ6_GAIN: plugin->eq_gain[5] = data; break;
        case SGEQ_SPECTRUM_ENABLED: plugin->spectrum_analyzer_on = data; break;

        case SGEQ_PRE_FX0_KNOB0: plugin->pre_fx_knob0[0] = data; break;
        case SGEQ_PRE_FX0_KNOB1: plugin->pre_fx_knob1[0] = data; break;
        case SGEQ_PRE_FX0_KNOB2: plugin->pre_fx_knob2[0] = data; break;
        case SGEQ_PRE_FX0_COMBOBOX: plugin->pre_fx_combobox[0] = data; break;

        case SGEQ_PRE_FX1_KNOB0: plugin->pre_fx_knob0[1] = data; break;
        case SGEQ_PRE_FX1_KNOB1: plugin->pre_fx_knob1[1] = data; break;
        case SGEQ_PRE_FX1_KNOB2: plugin->pre_fx_knob2[1] = data; break;
        case SGEQ_PRE_FX1_COMBOBOX: plugin->pre_fx_combobox[1] = data; break;

        case SGEQ_PRE_FX2_KNOB0: plugin->pre_fx_knob0[2] = data; break;
        case SGEQ_PRE_FX2_KNOB1: plugin->pre_fx_knob1[2] = data; break;
        case SGEQ_PRE_FX2_KNOB2: plugin->pre_fx_knob2[2] = data; break;
        case SGEQ_PRE_FX2_COMBOBOX: plugin->pre_fx_combobox[2] = data; break;

        case SGEQ_PRE_FX3_KNOB0: plugin->pre_fx_knob0[3] = data; break;
        case SGEQ_PRE_FX3_KNOB1: plugin->pre_fx_knob1[3] = data; break;
        case SGEQ_PRE_FX3_KNOB2: plugin->pre_fx_knob2[3] = data; break;
        case SGEQ_PRE_FX3_COMBOBOX: plugin->pre_fx_combobox[3] = data; break;

        case SGEQ_PRE_FX4_KNOB0: plugin->pre_fx_knob0[4] = data; break;
        case SGEQ_PRE_FX4_KNOB1: plugin->pre_fx_knob1[4] = data; break;
        case SGEQ_PRE_FX4_KNOB2: plugin->pre_fx_knob2[4] = data; break;
        case SGEQ_PRE_FX4_COMBOBOX: plugin->pre_fx_combobox[4] = data; break;

        case SGEQ_PRE_FX5_KNOB0: plugin->pre_fx_knob0[5] = data; break;
        case SGEQ_PRE_FX5_KNOB1: plugin->pre_fx_knob1[5] = data; break;
        case SGEQ_PRE_FX5_KNOB2: plugin->pre_fx_knob2[5] = data; break;
        case SGEQ_PRE_FX5_COMBOBOX: plugin->pre_fx_combobox[5] = data; break;

        case SGEQ_POST_FX0_KNOB0: plugin->post_fx_knob0[0] = data; break;
        case SGEQ_POST_FX0_KNOB1: plugin->post_fx_knob1[0] = data; break;
        case SGEQ_POST_FX0_KNOB2: plugin->post_fx_knob2[0] = data; break;
        case SGEQ_POST_FX0_COMBOBOX: plugin->post_fx_combobox[0] = data; break;

        case SGEQ_POST_FX1_KNOB0: plugin->post_fx_knob0[1] = data; break;
        case SGEQ_POST_FX1_KNOB1: plugin->post_fx_knob1[1] = data; break;
        case SGEQ_POST_FX1_KNOB2: plugin->post_fx_knob2[1] = data; break;
        case SGEQ_POST_FX1_COMBOBOX: plugin->post_fx_combobox[1] = data; break;

        case SGEQ_POST_FX2_KNOB0: plugin->post_fx_knob0[2] = data; break;
        case SGEQ_POST_FX2_KNOB1: plugin->post_fx_knob1[2] = data; break;
        case SGEQ_POST_FX2_KNOB2: plugin->post_fx_knob2[2] = data; break;
        case SGEQ_POST_FX2_COMBOBOX: plugin->post_fx_combobox[2] = data; break;

        case SGEQ_POST_FX3_KNOB0: plugin->post_fx_knob0[3] = data; break;
        case SGEQ_POST_FX3_KNOB1: plugin->post_fx_knob1[3] = data; break;
        case SGEQ_POST_FX3_KNOB2: plugin->post_fx_knob2[3] = data; break;
        case SGEQ_POST_FX3_COMBOBOX: plugin->post_fx_combobox[3] = data; break;

        case SGEQ_POST_FX4_KNOB0: plugin->post_fx_knob0[4] = data; break;
        case SGEQ_POST_FX4_KNOB1: plugin->post_fx_knob1[4] = data; break;
        case SGEQ_POST_FX4_KNOB2: plugin->post_fx_knob2[4] = data; break;
        case SGEQ_POST_FX4_COMBOBOX: plugin->post_fx_combobox[4] = data; break;

        case SGEQ_POST_FX5_KNOB0: plugin->post_fx_knob0[5] = data; break;
        case SGEQ_POST_FX5_KNOB1: plugin->post_fx_knob1[5] = data; break;
        case SGEQ_POST_FX5_KNOB2: plugin->post_fx_knob2[5] = data; break;
        case SGEQ_POST_FX5_COMBOBOX: plugin->post_fx_combobox[5] = data; break;
    }
}

PluginHandle g_sgeq_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sgeq *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sgeq));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_sgeq_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sgeq_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
){
    t_sgeq *plugin_data = (t_sgeq*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_sgeq_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_sgeq *plugin_data = (t_sgeq*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

int _prefx_check_if_on(t_sgeq *plugin_data){
    int on = 0;
    t_sgeq_mono_modules* mm = &plugin_data->mono_modules;

    for(int i = 0; i < 6; ++i){
        mm->pre_fx_func_ptr[i] = g_mf3_get_function_pointer(
            (int)(*(plugin_data->pre_fx_combobox[i]))
        );

        if(mm->pre_fx_func_ptr[i] != v_mf3_run_off){
            on = 1;
        }
    }
    return on;
}

int _postfx_check_if_on(t_sgeq *plugin_data){
    int on = 0;
    t_sgeq_mono_modules* mm = &plugin_data->mono_modules;

    for(int i = 0; i < 6; ++i){
        mm->post_fx_func_ptr[i] = g_mf3_get_function_pointer(
            (int)(*(plugin_data->post_fx_combobox[i]))
        );

        if(mm->post_fx_func_ptr[i] != v_mf3_run_off){
            on = 1;
        }
    }
    return on;
}

void v_sgeq_run(
    PluginHandle instance,
    enum PluginRunMode run_mode,
    int sample_count,
    struct SamplePair* input_buffer,
    struct SamplePair* sc_buffer,
    struct SamplePair* output_buffer,
    struct ShdsList * midi_events,
    struct ShdsList * atm_events,
    t_pkm_peak_meter* peak_meter,
    int midi_channel
){
    t_sgeq *plugin_data = (t_sgeq*)instance;
    t_mf3_multi * f_fx;

    t_sgeq_mono_modules* mm = &plugin_data->mono_modules;
    int prefx_on = _prefx_check_if_on(plugin_data);
    int postfx_on = _postfx_check_if_on(plugin_data);
    int spectrum_analyzer_on = (int)(*plugin_data->spectrum_analyzer_on);

    effect_translate_midi_events(
        midi_events,
        &plugin_data->midi_events,
        &plugin_data->atm_queue,
        atm_events,
        midi_channel
    );
    struct SamplePair sample;

    for(int i = 0; i < sample_count; ++i){
        sample.left = input_buffer[i].left;
        sample.right = input_buffer[i].right;
        effect_process_events(
            i,
            &plugin_data->midi_events,
            plugin_data->port_table,
            plugin_data->descriptor,
            &plugin_data->cc_map,
            &plugin_data->atm_queue
        );

        if(prefx_on){
            for(int j = 0; j < 6; ++j){
                if(
                    mm->pre_fx_func_ptr[j]
                    !=
                    v_mf3_run_off
                ){
                    f_fx = &mm->prefx[j];
                    v_sml_run(
                        &mm->pre_smoothers[j][0],
                        *plugin_data->pre_fx_knob0[j]
                    );
                    v_sml_run(
                        &mm->pre_smoothers[j][1],
                        *plugin_data->pre_fx_knob1[j]
                    );
                    v_sml_run(
                        &mm->pre_smoothers[j][2],
                        *plugin_data->pre_fx_knob2[j]
                    );

                    v_mf3_set(
                        f_fx,
                        mm->pre_smoothers[j][0].last_value,
                        mm->pre_smoothers[j][1].last_value,
                        mm->pre_smoothers[j][2].last_value
                    );

                    mm->pre_fx_func_ptr[j](
                        f_fx,
                        sample.left,
                        sample.right
                    );

                    sample.left = f_fx->output0;
                    sample.right = f_fx->output1;
                }
            }
        }

        for(int j = 0; j < SGEQ_EQ_COUNT; ++j){
            if(*plugin_data->eq_gain[j] != 0.0f){
                v_pkq_calc_coeffs(
                    &mm->eqs[j],
                    *plugin_data->eq_freq[j],
                    *plugin_data->eq_res[j] * 0.01f,
                    *plugin_data->eq_gain[j] * 0.1f
                );
                v_pkq_run(
                    &mm->eqs[j],
                    sample.left,
                    sample.right
                );
                sample.left = mm->eqs[j].output0;
                sample.right = mm->eqs[j].output1;
            }
        }

        if(postfx_on){
            for(int j = 0; j < 6; ++j){
                if(
                    mm->post_fx_func_ptr[j]
                    !=
                    v_mf3_run_off
                ){
                    f_fx = &mm->postfx[j];
                    v_sml_run(
                        &mm->post_smoothers[j][0],
                        *plugin_data->post_fx_knob0[j]
                    );
                    v_sml_run(
                        &mm->post_smoothers[j][1],
                        *plugin_data->post_fx_knob1[j]
                    );
                    v_sml_run(
                        &mm->post_smoothers[j][2],
                        *plugin_data->post_fx_knob2[j]
                    );

                    v_mf3_set(
                        f_fx,
                        mm->post_smoothers[j][0].last_value,
                        mm->post_smoothers[j][1].last_value,
                        mm->post_smoothers[j][2].last_value
                    );

                    mm->post_fx_func_ptr[j](
                        f_fx,
                        sample.left,
                        sample.right
                    );

                    sample.left = f_fx->output0;
                    sample.right = f_fx->output1;
                }
            }
        }

        _plugin_mix(
            run_mode,
            i,
            output_buffer,
            sample.left,
            sample.right
        );


        if(spectrum_analyzer_on){
            v_spa_run(
                plugin_data->mono_modules.spectrum_analyzer,
                (sample.left + sample.right) * 0.5
            );
        }


    }

    if(
        spectrum_analyzer_on
        &&
        plugin_data->mono_modules.spectrum_analyzer->str_buf[0] != '\0'
    ){
        plugin_data->queue_func(
            "ui",
            plugin_data->mono_modules.spectrum_analyzer->str_buf
        );
        plugin_data->mono_modules.spectrum_analyzer->str_buf[0] = '\0';
    }
}

SGFLT* sgeq_get_port_table(PluginHandle instance){
    t_sgeq *plugin_data = (t_sgeq*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sgeq_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SGEQ_COUNT);

    set_plugin_port(f_result, SGEQ_EQ1_FREQ, 24.0f, 4.0f, 123.0f);
    set_plugin_port(f_result, SGEQ_EQ2_FREQ, 42.0f, 4.0f, 123.0f);
    set_plugin_port(f_result, SGEQ_EQ3_FREQ, 60.0f, 4.0f, 123.0f);
    set_plugin_port(f_result, SGEQ_EQ4_FREQ, 78.0f, 4.0f, 123.0f);
    set_plugin_port(f_result, SGEQ_EQ5_FREQ, 96.0f, 4.0f, 123.0f);
    set_plugin_port(f_result, SGEQ_EQ6_FREQ, 114.0f, 4.0f, 123.0f);
    set_plugin_port(f_result, SGEQ_EQ1_RES, 300.0f, 100.0f, 600.0f);
    set_plugin_port(f_result, SGEQ_EQ2_RES, 300.0f, 100.0f, 600.0f);
    set_plugin_port(f_result, SGEQ_EQ3_RES, 300.0f, 100.0f, 600.0f);
    set_plugin_port(f_result, SGEQ_EQ4_RES, 300.0f, 100.0f, 600.0f);
    set_plugin_port(f_result, SGEQ_EQ5_RES, 300.0f, 100.0f, 600.0f);
    set_plugin_port(f_result, SGEQ_EQ6_RES, 300.0f, 100.0f, 600.0f);
    set_plugin_port(f_result, SGEQ_EQ1_GAIN, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, SGEQ_EQ2_GAIN, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, SGEQ_EQ3_GAIN, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, SGEQ_EQ4_GAIN, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, SGEQ_EQ5_GAIN, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, SGEQ_EQ6_GAIN, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, SGEQ_SPECTRUM_ENABLED, 0.0f, 0.0f, 1.0f);

    set_plugin_port(f_result, SGEQ_PRE_FX0_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX0_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX0_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX0_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_PRE_FX1_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX1_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX1_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX1_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_PRE_FX2_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX2_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX2_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX2_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_PRE_FX3_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX3_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX3_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX3_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_PRE_FX4_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX4_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX4_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX4_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_PRE_FX5_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX5_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX5_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_PRE_FX5_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);

    set_plugin_port(f_result, SGEQ_POST_FX0_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX0_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX0_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX0_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_POST_FX1_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX1_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX1_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX1_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_POST_FX2_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX2_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX2_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX2_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_POST_FX3_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX3_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX3_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX3_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_POST_FX4_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX4_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX4_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX4_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, SGEQ_POST_FX5_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX5_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX5_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, SGEQ_POST_FX5_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);

    f_result->cleanup = v_sgeq_cleanup;
    f_result->connect_port = v_sgeq_connect_port;
    f_result->get_port_table = sgeq_get_port_table;
    f_result->instantiate = g_sgeq_instantiate;
    f_result->panic = v_sgeq_panic;
    f_result->load = v_sgeq_load;
    f_result->set_port_value = v_sgeq_set_port_value;
    f_result->set_cc_map = v_sgeq_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_sgeq_run;
    f_result->on_stop = v_sgeq_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_sgeq_mono_init(
    t_sgeq_mono_modules* a_mono,
    SGFLT a_sr,
    int a_plugin_uid
){
    for(int i = 0; i < SGEQ_EQ_COUNT; ++i){
        g_pkq_init(&a_mono->eqs[i], a_sr);
    }

    a_mono->spectrum_analyzer = g_spa_spectrum_analyzer_get(
        4096,
        a_plugin_uid
    );

    for(int i = 0; i < 6; ++i){
        g_mf3_init(&a_mono->prefx[i], a_sr, 1);
        a_mono->pre_fx_func_ptr[i] = v_mf3_run_off;
        for(int j = 0; j < 3; ++j){
            g_sml_init(
                &a_mono->pre_smoothers[i][j],
                a_sr,
                127.0f,
                0.0f,
                0.1f
            );
        }
    }

    for(int i = 0; i < 6; ++i){
        g_mf3_init(&a_mono->postfx[i], a_sr, 1);
        a_mono->post_fx_func_ptr[i] = v_mf3_run_off;
        for(int j = 0; j < 3; ++j){
            g_sml_init(
                &a_mono->post_smoothers[i][j],
                a_sr,
                127.0f,
                0.0f,
                0.1f
            );
        }
    }
}

/*
void v_sgeq_destructor()
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
