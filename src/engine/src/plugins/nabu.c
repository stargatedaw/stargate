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
#include "plugins/nabu.h"

int NABU_AMORITIZER = 0;

void v_nabu_cleanup(PluginHandle instance){
    free(instance);
}

void v_nabu_set_cc_map(PluginHandle instance, char * a_msg){
    struct NabuPlugin* plugin = (struct NabuPlugin*)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_nabu_panic(PluginHandle instance){
    //struct NabuPlugin *plugin = (struct NabuPlugin*)instance;
}

void v_nabu_on_stop(PluginHandle instance){
    //struct NabuPlugin *plugin = (struct NabuPlugin*)instance;
}

void v_nabu_connect_port(
    PluginHandle instance,
    int port,
    PluginData* data
){
    struct NabuPlugin* plugin = (struct NabuPlugin*)instance;
    int fx_num, fx_port, norm_port;
    struct NabuMonoModules* mm = &plugin->mono_modules;
    struct MultiFX10Controls* controls;

    if(port >= NABU_FIRST_CONTROL_PORT && port <= NABU_LAST_CONTROL_PORT){
        norm_port = (port - NABU_FIRST_CONTROL_PORT);
        fx_num = norm_port / NABU_CONTROLS_PER_FX;
        fx_port = norm_port % NABU_CONTROLS_PER_FX;
        controls = &mm->fx[fx_num].controls;
        if(fx_port < MULTIFX10KNOB_KNOB_COUNT){
            controls->knobs[fx_port] = data;
        } else if(fx_port == 10){
            controls->route = data;
        } else if(fx_port == 11){
            controls->type = data;
        } else if(fx_port == 12){
            controls->dry = data;
        } else if(fx_port == 13){
            controls->wet = data;
        } else if(fx_port == 14){
            controls->pan = data;
        } else {
            sg_abort("Nabu: Port %i has invalid fx_port: %i", port, fx_port);
        }
        return;
    } else if(
        port >= NABU_FIRST_SPLITTER_PORT
        &&
        port <= NABU_LAST_SPLITTER_PORT
    ){
        norm_port = port - NABU_FIRST_SPLITTER_PORT;
        switch(norm_port){
            case 0: plugin->splitter_controls.splits = data; break;
            case 1: plugin->splitter_controls.type = data; break;
            case 2: plugin->splitter_controls.res = data; break;
            case 3: plugin->splitter_controls.output[0] = data; break;
            case 4: plugin->splitter_controls.freq[0] = data; break;
            case 5: plugin->splitter_controls.output[1] = data; break;
            case 6: plugin->splitter_controls.freq[1] = data; break;
            case 7: plugin->splitter_controls.output[2] = data; break;
            case 8: plugin->splitter_controls.freq[2] = data; break;
            case 9: plugin->splitter_controls.output[3] = data; break;
        };
    } else {
        switch(port){
            case NABU_UI_MSG_ENABLED_PORT:
                plugin->ui_msg_enabled = data;
                break;
            default:
                sg_abort("Nabu: Port %i is invalid", port);
                break;
        }
    }
}

PluginHandle g_nabu_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    struct NabuPlugin* plugin_data;
    hpalloc((void**)&plugin_data, sizeof(struct NabuPlugin));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_nabu_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs,
        plugin_data->plugin_uid
    );

    plugin_data->i_slow_index = NABU_SLOW_INDEX_ITERATIONS + NABU_AMORITIZER;
    plugin_data->ui_buff_limit = (int)(s_rate / 30.);
    plugin_data->ui_buff_count = 0;

    ++NABU_AMORITIZER;
    if(NABU_AMORITIZER >= NABU_SLOW_INDEX_ITERATIONS){
        NABU_AMORITIZER = 0;
    }

    plugin_data->is_on = 0;

    g_get_port_table(
        (void**)plugin_data,
        descriptor
    );

    v_cc_map_init(&plugin_data->cc_map);
    return (PluginHandle)plugin_data;
}

void v_nabu_load(
    PluginHandle instance,
    PluginDescriptor* Descriptor,
    SGPATHSTR * a_file_path
){
    struct NabuPlugin* plugin_data = (struct NabuPlugin*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_nabu_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    struct NabuPlugin* plugin_data = (struct NabuPlugin*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_nabu_process_midi_event(
    struct NabuPlugin* plugin_data,
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

    struct MIDIEvent* midi_event;
    if (a_event->type == EVENT_CONTROLLER){
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_nabu_process_midi_event: param %i out of range 1 to 128",
            a_event->param
        );

        midi_event = &plugin_data->midi_events[plugin_data->midi_event_count];
        midi_event->type = EVENT_CONTROLLER;
        midi_event->tick = a_event->tick;
        midi_event->port = a_event->param;
        midi_event->value = a_event->value;

        if(!plugin_data->is_on){
            plugin_data->is_on = mf10_routing_plan_set(
                &plugin_data->mono_modules.routing_plan,
                plugin_data->mono_modules.fx,
                &plugin_data->mono_modules.output,
                MULTIFX10_MAX_FX_COUNT
            );
            //Meaning that we now have set the port anyways because the
            //main loop won't be running
            if(!plugin_data->is_on){
                plugin_data->port_table[midi_event->port] = midi_event->value;
            }
        }

        ++plugin_data->midi_event_count;
    }
}

void v_nabu_run(
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
    int i, j;
    int i_mono_out;
    struct NabuPlugin* plugin_data = (struct NabuPlugin*)instance;
    struct NabuMonoModules* mm = &plugin_data->mono_modules;
    t_mf10_multi * f_fx;
    struct MIDIEvent* midi_event;
    struct MultiFX10MonoCluster* step;
    SGFLT splitter_input[2];
    int split_mask = 0;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int event_pos;
    int splits = (int)(*plugin_data->splitter_controls.splits);
    int midi_event_pos = 0;
    plugin_data->midi_event_count = 0;

    for(event_pos = 0; event_pos < event_count; ++event_pos){
        v_nabu_process_midi_event(
            plugin_data,
            events[event_pos],
            midi_channel
        );
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_seq_event * ev_tmp;
    for(i = 0; i < atm_events->len; ++i){
        ev_tmp = (t_seq_event*)atm_events->data[i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue,
            ev_tmp->type,
            ev_tmp->tick,
            ev_tmp->value,
            ev_tmp->port
        );
    }

    if(plugin_data->i_slow_index >= NABU_SLOW_INDEX_ITERATIONS){
        plugin_data->i_slow_index -= NABU_SLOW_INDEX_ITERATIONS;
        plugin_data->is_on = mf10_routing_plan_set(
            &plugin_data->mono_modules.routing_plan,
            plugin_data->mono_modules.fx,
            &plugin_data->mono_modules.output,
            MULTIFX10_MAX_FX_COUNT
        );
    } else {
        ++plugin_data->i_slow_index;
    }

    if(plugin_data->is_on){
        SGFLT freqs[3] = {
            *plugin_data->splitter_controls.freq[0],
            *plugin_data->splitter_controls.freq[1],
            *plugin_data->splitter_controls.freq[2],
        };
        if(splits){
            freq_splitter_set(
                &mm->splitter,
                splits,
                (int)(*plugin_data->splitter_controls.type),
                (*plugin_data->splitter_controls.res) * 0.1,
                freqs
            );
        }
        for(i = 0; i < mm->routing_plan.active_fx_count; ++i){
            step = mm->routing_plan.steps[i];
            dry_wet_pan_set(
                &step->dry_wet_pan,
                step->dry_smoother.last_value * 0.1,
                step->wet_smoother.last_value * 0.1,
                step->pan_smoother.last_value * 0.01
            );
        }

        for(i_mono_out = 0; i_mono_out < sample_count; ++i_mono_out){
            midi_event = &plugin_data->midi_events[midi_event_pos];
            while(
                midi_event_pos < plugin_data->midi_event_count
                &&
                midi_event->tick == i_mono_out
            ){
                if(midi_event->type == EVENT_CONTROLLER){
                    v_cc_map_translate(
                        &plugin_data->cc_map, plugin_data->descriptor,
                        plugin_data->port_table,
                        midi_event->port,
                        midi_event->value
                    );
                }
                ++midi_event_pos;
            }

            v_plugin_event_queue_atm_set(
                &plugin_data->atm_queue,
                i_mono_out,
                plugin_data->port_table
            );

            mm->output.left = 0.0;
            mm->output.right = 0.0;
            for(i = 0; i < mm->routing_plan.active_fx_count; ++i){
                step = mm->routing_plan.steps[i];
                step->input.left = 0.0;
                step->input.right = 0.0;
            }

            if(splits){
                int output;
                splitter_input[0] = input_buffer[i_mono_out].left;
                splitter_input[1] = input_buffer[i_mono_out].right;
                freq_splitter_run(&mm->splitter, splitter_input);
                for(j = 0; j < splits + 1; ++j){
                    output = (int)(*plugin_data->splitter_controls.output[j]);
                    if(output == NABU_MAIN_OUT){
                        mm->output.left += mm->splitter.output[j][0];
                        mm->output.right += mm->splitter.output[j][1];
                    } else {
                        split_mask |= 1 << output;
                        mm->fx[output].input.left +=
                            mm->splitter.output[j][0];
                        mm->fx[output].input.right +=
                            mm->splitter.output[j][1];
                    }
                }
            }

            for(i = 0; i < mm->routing_plan.active_fx_count; ++i){
                step = mm->routing_plan.steps[i];
                f_fx = &step->mf10;

                if(
                    step->input_main
                    &&
                    !(split_mask & (1 << step->mf10_index))
                ){
                    step->input.left += input_buffer[i_mono_out].left;
                    step->input.right += input_buffer[i_mono_out].right;
                }
                for(j = 0; j < step->meta.knob_count; ++j){
                    v_sml_run(
                        &step->smoothers[j],
                        *step->controls.knobs[j]
                    );
                }
                v_sml_run(&step->dry_smoother, *step->controls.dry);
                v_sml_run(&step->wet_smoother, *step->controls.wet);
                v_sml_run(&step->pan_smoother, *step->controls.pan);

                v_mf10_set_from_smoothers(
                    f_fx,
                    step->smoothers,
                    step->meta.knob_count
                );

                v_pkm_run_single(
                    &step->input_peak,
                    step->input.left,
                    step->input.right
                );
                step->meta.run(
                    f_fx,
                    step->input.left,
                    step->input.right
                );

                dry_wet_pan_run(
                    &step->dry_wet_pan,
                    step->input.left,
                    step->input.right,
                    f_fx->output0,
                    f_fx->output1
                );
                v_pkm_run_single(
                    &step->output_peak,
                    step->dry_wet_pan.output.left,
                    step->dry_wet_pan.output.right
                );
                step->output->left += step->dry_wet_pan.output.left;
                step->output->right += step->dry_wet_pan.output.right;
            }

            _plugin_mix(
                run_mode,
                i_mono_out,
                output_buffer,
                mm->output.left,
                mm->output.right
            );
        }
    } else {
        for(i_mono_out = 0; i_mono_out < sample_count; ++i_mono_out){
            _plugin_mix(
                run_mode,
                i_mono_out,
                output_buffer,
                input_buffer[i_mono_out].left,
                input_buffer[i_mono_out].right
            );
        }
    }

    if((int)(*plugin_data->ui_msg_enabled)){
        plugin_data->ui_buff_count += sample_count;
        if(plugin_data->ui_buff_count >= plugin_data->ui_buff_limit){
            plugin_data->ui_buff_count -= plugin_data->ui_buff_limit;
            char* ptr = &plugin_data->msg_buff[0];
            int count = sprintf(
                ptr,
                "%i|gain",
                plugin_data->plugin_uid
            );
            ptr += count;
            for(i = 0; i < MULTIFX10_MAX_FX_COUNT; ++i){
                if((int)(*mm->fx[i].controls.type) != 0){
                    count = sprintf(
                        ptr,
                        "|%i:%f:%f:%f:%f",
                        i,
                        mm->fx[i].input_peak.value[0],
                        mm->fx[i].input_peak.value[1],
                        mm->fx[i].output_peak.value[0],
                        mm->fx[i].output_peak.value[1]
                    );
                } else {
                    count = sprintf(ptr, "|%i:0:0:0:0", i);
                }
                ptr += count;
                v_pkm_reset(&mm->fx[i].input_peak);
                v_pkm_reset(&mm->fx[i].output_peak);
            }
            plugin_data->queue_func("ui", plugin_data->msg_buff);
        }
    }
}

SGFLT* nabu_get_port_table(PluginHandle instance){
    struct NabuPlugin *plugin_data = (struct NabuPlugin*)instance;
    return plugin_data->port_table;
}

PluginDescriptor* nabu_plugin_descriptor(){
    int i, j, port;
    PluginDescriptor* f_result = get_plugin_descriptor(NABU_PORT_COUNT);

    port = NABU_FIRST_CONTROL_PORT;
    for(i = 0; i < MULTIFX10_MAX_FX_COUNT; ++i){
        for(j = 0; j < 10; ++j){
            set_plugin_port(f_result, port, 635.0f, 0.0f, 1270.0f);
            ++port;
        }
        set_plugin_port(
            f_result,
            port,  // Route
            0.0,
            0.0,
            (SGFLT)(MULTIFX10_MAX_FX_COUNT - i + 1)
        );
        ++port;
        set_plugin_port(
            f_result,
            port,  // Type
            0.0f,
            0.0f,
            MULTIFX10KNOB_FX_COUNT
        );
        ++port;
        set_plugin_port(
            f_result,
            port,  // Dry
            -400.0,
            -400.0,
            120.0
        );
        ++port;
        set_plugin_port(
            f_result,
            port,  // Wet
            0.0,
            -400.0,
            120.0
        );
        ++port;
        set_plugin_port(
            f_result,
            port,  // Pan
            0.0f,
            -100.0,
            100.0
        );
        ++port;
    }

    set_plugin_port(
        f_result,
        port,  // Splits
        0.0f,
        0.0,
        3.0
    );
    ++port;
    set_plugin_port(
        f_result,
        port,  // Type
        0.0f,
        0.0,
        1.0
    );
    ++port;
    set_plugin_port(
        f_result,
        port,  // Res
        -120.0f,
        -300.0,
        -10.0
    );
    ++port;
    set_plugin_port(
        f_result,
        port,  // Output
        0.0f,
        0.0,
        13.
    );
    ++port;

    for(i = 0; i < 3; ++i){
        set_plugin_port(
            f_result,
            port,  // Freq
            51. + (i * 24.),
            30.0,
            120.
        );
        ++port;
        set_plugin_port(
            f_result,
            port,  // Output
            0.0f,
            0.0,
            13.
        );
        ++port;
    }

    set_plugin_port(
        f_result,
        NABU_UI_MSG_ENABLED_PORT,
        0.0,
        0.0,
        1.0
    );
    f_result->cleanup = v_nabu_cleanup;
    f_result->connect_port = v_nabu_connect_port;
    f_result->get_port_table = nabu_get_port_table;
    f_result->instantiate = g_nabu_instantiate;
    f_result->panic = v_nabu_panic;
    f_result->load = v_nabu_load;
    f_result->set_port_value = v_nabu_set_port_value;
    f_result->set_cc_map = v_nabu_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_nabu_run;
    f_result->on_stop = v_nabu_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}


void v_nabu_mono_init(
    struct NabuMonoModules* self,
    SGFLT sr,
    int a_plugin_uid
){
    int i;

    freq_splitter_init(&self->splitter, sr);
    for(i = 0; i < MULTIFX10_MAX_FX_COUNT; ++i){
        mf10_mono_cluster_init(&self->fx[i], sr, i);
    }
}

/*
void v_nabu_destructor()
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
