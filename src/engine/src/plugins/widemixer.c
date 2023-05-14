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
#include "plugins/widemixer.h"


struct WMRunVars {
    int mute;
    int bass_mono_on;
    int bass_mono_solo;
    int stereo_mode;
    int invert_mode;
    int dc_offset;
    SGFLT bass_mono_freq;
    SGFLT bass_mono_low;
    SGFLT bass_mono_high;
    SGFLT gain;
    SGFLT pan_law;
    SGFLT mid_side;
};

static void init_run_vars(struct WMRunVars* runvars, t_widemixer* plugin){
    runvars->mute = (int)(*plugin->mute);
    runvars->bass_mono_on = (int)(*plugin->bass_mono_on);
    runvars->dc_offset = (int)(*plugin->dc_offset);
    if(runvars->bass_mono_on){
        runvars->bass_mono_solo = (int)(*plugin->bass_mono_solo);
        runvars->bass_mono_freq = (SGFLT)(*plugin->bass_mono);
        runvars->bass_mono_low = f_db_to_linear_fast(
            (*plugin->bass_mono_low) * 0.1f
        );
        runvars->bass_mono_high = f_db_to_linear_fast(
            (*plugin->bass_mono_high) * 0.1f
        );
    }
    runvars->invert_mode = (int)(*plugin->invert_mode);
    runvars->stereo_mode = (int)(*plugin->stereo_mode);
    runvars->gain = f_db_to_linear_fast((*plugin->gain) * 0.01f);
    runvars->pan_law = (*plugin->pan_law) * 0.01f;
    runvars->mid_side = (SGFLT)(*plugin->mid_side * 0.01);
}

static SGFLT run_widemixer(
    struct WMRunVars* runvars,
    t_widemixer* plugin,
    int* midi_event_pos,
    int sample_num,
    struct SamplePair* sample
){
    SGFLT tmp, mid, side[2];
    t_svf2_filter* filter = &plugin->mono_modules.bass_mono_filter;
    while(
        *midi_event_pos < plugin->midi_event_count
        &&
        plugin->midi_event_ticks[*midi_event_pos] == sample_num
    ){
        if(
            plugin->midi_event_types[*midi_event_pos]
            ==
            EVENT_CONTROLLER
        ){
            v_cc_map_translate(
                &plugin->cc_map,
                plugin->descriptor,
                plugin->port_table,
                plugin->midi_event_ports[*midi_event_pos],
                plugin->midi_event_values[*midi_event_pos]
            );
        }
        ++*midi_event_pos;
    }

    v_plugin_event_queue_atm_set(
        &plugin->atm_queue,
        sample_num,
        plugin->port_table
    );

    if(runvars->invert_mode){
        if(runvars->invert_mode == WIDEMIXER_INVERT_MODE_LEFT){
            sample->left *= -1.0;
        } else if(runvars->invert_mode == WIDEMIXER_INVERT_MODE_RIGHT){
            sample->right *= -1.0;
        } else if(runvars->invert_mode == WIDEMIXER_INVERT_MODE_BOTH){
            sample->left *= -1.0;
            sample->right *= -1.0;
        }
    }

    if(runvars->stereo_mode){
        if(runvars->stereo_mode == WIDEMIXER_STEREO_MODE_LEFT){
            sample->right = sample->left;
        } else if(runvars->stereo_mode == WIDEMIXER_STEREO_MODE_RIGHT){
            sample->left = sample->right;
        } else if(runvars->stereo_mode == WIDEMIXER_STEREO_MODE_SWAP){
            tmp = sample->left;
            sample->left = sample->right;
            sample->right = tmp;
        }
    }

    side[0] = sample->left - sample->right;
    side[1] = sample->right - sample->left;
    mid = sample->left - side[0];

    if(runvars->mid_side >= 0.01){
        v_axf_set_xfade(
            &plugin->mono_modules.xfade,
            runvars->mid_side
        );
        sample->left = f_axf_run_xfade(
            &plugin->mono_modules.xfade,
            sample->left,
            side[0]
        );
        sample->right = f_axf_run_xfade(
            &plugin->mono_modules.xfade,
            sample->right,
            side[1]
        );
    } else if(runvars->mid_side <= -0.01){
        tmp = runvars->mid_side + 1.0;
        v_axf_set_xfade(&plugin->mono_modules.xfade, tmp);
        sample->left = f_axf_run_xfade(
            &plugin->mono_modules.xfade,
            mid,
            sample->left
        );
        sample->right = f_axf_run_xfade(
            &plugin->mono_modules.xfade,
            mid,
            sample->right
        );
    }

    v_sml_run(
        &plugin->mono_modules.volume_smoother,
        (*plugin->vol_slider * 0.01f)
    );

    v_sml_run(
        &plugin->mono_modules.pan_smoother,
        (*plugin->pan * 0.01f)
    );

    v_pn2_set(
        &plugin->mono_modules.panner,
        plugin->mono_modules.pan_smoother.last_value,
        runvars->pan_law
    );
    if(runvars->bass_mono_on){
        v_svf2_set_cutoff_hz(
            &plugin->mono_modules.bass_mono_filter,
            runvars->bass_mono_freq
        );
        v_svf2_run(
            &plugin->mono_modules.bass_mono_filter,
            &plugin->mono_modules.bass_mono_filter.filter_kernels[0][0],
            sample->left
        );
        v_svf2_run(
            &plugin->mono_modules.bass_mono_filter,
            &plugin->mono_modules.bass_mono_filter.filter_kernels[0][1],
            sample->right
        );
        // 0.708 == -3dB
        if(runvars->bass_mono_solo){
            sample->left = (
                filter->filter_kernels[0][0].lp
                +
                filter->filter_kernels[0][1].lp
            ) * runvars->bass_mono_low * 0.708;
            sample->right = (
                filter->filter_kernels[0][0].lp
                +
                filter->filter_kernels[0][1].lp
            ) * runvars->bass_mono_low * 0.708;
        } else {
            sample->left = (
                (
                    (
                        filter->filter_kernels[0][0].lp
                        +
                        filter->filter_kernels[0][1].lp
                    ) * runvars->bass_mono_low * 0.708
                ) + (
                    (
                        filter->filter_kernels[0][0].bp
                        +
                        filter->filter_kernels[0][0].hp
                    ) * runvars->bass_mono_high
                )
            );
            sample->right = (
                (
                    (
                        filter->filter_kernels[0][0].lp
                        +
                        filter->filter_kernels[0][1].lp
                    ) * runvars->bass_mono_low * 0.708
                ) + (
                    (
                        filter->filter_kernels[0][1].bp
                        +
                        filter->filter_kernels[0][1].hp
                    ) * runvars->bass_mono_high
                )
            );
        }

        if(runvars->dc_offset){
            sample->left = f_dco_run(
                &plugin->mono_modules.dc_filter[0],
                sample->left
            );
            sample->right = f_dco_run(
                &plugin->mono_modules.dc_filter[1],
                sample->right
            );
        }
    }

    // * 1.090184 to compensate for various rounding errors that cannot be
    // fixed without changing the sound of everything
    return f_db_to_linear_fast(
        plugin->mono_modules.volume_smoother.last_value - runvars->pan_law
    ) * 1.090184;
}

void v_widemixer_cleanup(PluginHandle instance){
    free(instance);
}

void v_widemixer_set_cc_map(PluginHandle instance, char * a_msg){
    t_widemixer *plugin = (t_widemixer *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_widemixer_panic(PluginHandle instance){
    //t_widemixer *plugin = (t_widemixer*)instance;
}

void v_widemixer_on_stop(PluginHandle instance){
    //t_widemixer *plugin = (t_widemixer*)instance;
}

void v_widemixer_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_widemixer *plugin;
    plugin = (t_widemixer*)instance;

    switch (port){
        case WIDEMIXER_VOL_SLIDER: plugin->vol_slider = data; break;
        case WIDEMIXER_GAIN: plugin->gain = data; break;
        case WIDEMIXER_PAN: plugin->pan = data; break;
        case WIDEMIXER_LAW: plugin->pan_law = data; break;
        case WIDEMIXER_INVERT_MODE: plugin->invert_mode = data; break;
        case WIDEMIXER_STEREO_MODE: plugin->stereo_mode = data; break;
        case WIDEMIXER_BASS_MONO_ON: plugin->bass_mono_on = data; break;
        case WIDEMIXER_BASS_MONO: plugin->bass_mono = data; break;
        case WIDEMIXER_BASS_MONO_SOLO: plugin->bass_mono_solo = data; break;
        case WIDEMIXER_STEREO_EMPHASIS: plugin->mid_side = data; break;
        case WIDEMIXER_DC_OFFSET: plugin->dc_offset = data; break;
        case WIDEMIXER_MUTE: plugin->mute = data; break;
        case WIDEMIXER_BASS_MONO_LOW: plugin->bass_mono_low = data; break;
        case WIDEMIXER_BASS_MONO_HIGH: plugin->bass_mono_high = data; break;
        default:
            sg_assert(
                0,
                "v_widemixer_connect_port: unknown port %i",
                port
            );
            break;
    }
}

PluginHandle g_widemixer_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_widemixer *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_widemixer));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_widemixer_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_widemixer_load(
    PluginHandle instance,
    PluginDescriptor* Descriptor,
    SGPATHSTR * a_file_path
){
    t_widemixer *plugin_data = (t_widemixer*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_widemixer_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_widemixer *plugin_data = (t_widemixer*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_widemixer_process_midi_event(
    t_widemixer * plugin_data,
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
    if (a_event->type == EVENT_CONTROLLER){
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_widemixer_process_midi_event: param %i out of range 1 to 128",
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


void v_widemixer_process_midi(
    PluginHandle instance,
    struct ShdsList * events,
    struct ShdsList * atm_events,
    int midi_channel
){
    t_widemixer *plugin_data = (t_widemixer*)instance;
    int f_i = 0;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < events->len; ++f_i){
        v_widemixer_process_midi_event(
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


void v_widemixer_run(
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
    t_widemixer *plugin_data = (t_widemixer*)instance;
    float left, right;
    int midi_event_pos = 0;
    struct WMRunVars runvars;
    init_run_vars(&runvars, plugin_data);

    v_widemixer_process_midi(instance, midi_events, atm_events, midi_channel);

    SGFLT f_vol_linear;

    int f_i;
    struct SamplePair sample;

    for(f_i = 0; f_i < sample_count; ++f_i){
        sample.left = input_buffer[f_i].left;
        sample.right = input_buffer[f_i].right;
        f_vol_linear = run_widemixer(
            &runvars,
            plugin_data,
            &midi_event_pos,
            f_i,
            &sample
        );
        if(runvars.mute){
            output_buffer[f_i].left = 0.0;
            output_buffer[f_i].right = 0.0;
            if(peak_meter){
                v_pkm_run_single(peak_meter, 0.0, 0.0);
            }
            continue;
        }
        left = sample.left * f_vol_linear * runvars.gain *
            plugin_data->mono_modules.panner.gainL;
        right = sample.right * f_vol_linear * runvars.gain *
            plugin_data->mono_modules.panner.gainR;
        if(peak_meter){
            v_pkm_run_single(
                peak_meter,
                left,
                right
            );
        }
        _plugin_mix(
            run_mode,
            f_i,
            output_buffer,
            left,
            right
        );
    }
}

SGFLT* widemixer_get_port_table(PluginHandle instance){
    t_widemixer* plugin_data = (t_widemixer*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *widemixer_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(WIDEMIXER_COUNT);

    set_plugin_port(f_result, WIDEMIXER_VOL_SLIDER, 0.0f, -5000.0f, 0.0f);
    set_plugin_port(f_result, WIDEMIXER_GAIN, 0.0f, -2400.0f, 2400.0f);
    set_plugin_port(f_result, WIDEMIXER_PAN, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, WIDEMIXER_LAW, -300.0f, -600.0f, 0.0f);

    set_plugin_port(f_result, WIDEMIXER_INVERT_MODE, 0.0f, 0.0f, 3.0f);
    set_plugin_port(f_result, WIDEMIXER_STEREO_MODE, 0.0f, 0.0f, 3.0f);
    set_plugin_port(f_result, WIDEMIXER_BASS_MONO_ON, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, WIDEMIXER_BASS_MONO, 250.0f, 50.0f, 500.0f);
    set_plugin_port(f_result, WIDEMIXER_BASS_MONO_SOLO, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, WIDEMIXER_STEREO_EMPHASIS, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, WIDEMIXER_DC_OFFSET, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, WIDEMIXER_MUTE, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, WIDEMIXER_BASS_MONO_LOW, 0.0f, -240.0f, 240.0f);
    set_plugin_port(f_result, WIDEMIXER_BASS_MONO_HIGH, 0.0f, -240.0f, 240.0f);

    f_result->cleanup = v_widemixer_cleanup;
    f_result->connect_port = v_widemixer_connect_port;
    f_result->get_port_table = widemixer_get_port_table;
    f_result->instantiate = g_widemixer_instantiate;
    f_result->panic = v_widemixer_panic;
    f_result->load = v_widemixer_load;
    f_result->set_port_value = v_widemixer_set_port_value;
    f_result->set_cc_map = v_widemixer_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_widemixer_run;
    f_result->on_stop = v_widemixer_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_widemixer_mono_init(
    t_widemixer_mono_modules* a_mono,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_sml_init(&a_mono->volume_smoother, a_sr, 0.0f, -50.0f, 0.1f);
    a_mono->volume_smoother.last_value = 0.0f;
    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    a_mono->pan_smoother.last_value = 0.0f;
    g_dco_init(&a_mono->dc_filter[0], a_sr);
    g_dco_init(&a_mono->dc_filter[1], a_sr);
    g_svf2_init(&a_mono->bass_mono_filter, a_sr);
    v_svf2_set_res(&a_mono->bass_mono_filter, -12.0);
    g_axf_init(&a_mono->xfade, -3.0);
}

/*
void v_widemixer_destructor(){
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
