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

#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/delay/reverb.h"
#include "audiodsp/modules/filter/svf.h"
#include "plugin.h"
#include "plugins/reverb.h"


void v_sreverb_cleanup(PluginHandle instance){
    free(instance);
}

void v_sreverb_set_cc_map(PluginHandle instance, char * a_msg){
    t_sreverb *plugin = (t_sreverb *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_sreverb_panic(PluginHandle instance){
    t_sreverb *plugin = (t_sreverb*)instance;
    v_rvb_panic(&plugin->mono_modules.reverb);
}

void v_sreverb_on_stop(PluginHandle instance){
    //t_sreverb *plugin = (t_sreverb*)instance;
}

PluginHandle g_sreverb_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_sreverb *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_sreverb));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    v_sreverb_mono_init(
        &plugin_data->mono_modules,
        s_rate,
        a_plugin_uid
    );

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle) plugin_data;
}

void v_sreverb_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
){
    t_sreverb *plugin_data = (t_sreverb*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_sreverb_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_sreverb *plugin_data = (t_sreverb*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_sreverb_run(
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
    t_sreverb* plugin_data = (t_sreverb*)instance;
    t_sreverb_mono_modules* mm = &plugin_data->mono_modules;
    struct SamplePair sample;

    effect_translate_midi_events(
        midi_events,
        &plugin_data->midi_events,
        &plugin_data->atm_queue,
        atm_events,
        midi_channel
    );

    SGFLT f_dry_vol;

    for(int i = 0; i < sample_count; ++i){
        effect_process_events(
            i,
            &plugin_data->midi_events,
            plugin_data->port_table,
            plugin_data->descriptor,
            &plugin_data->cc_map,
            &plugin_data->atm_queue
        );

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue,
            i,
            plugin_data->port_table
        );

        v_sml_run(
            &mm->reverb_smoother,
            plugin_data->port_table[SREVERB_REVERB_WET] * 0.1f
        );

        v_sml_run(
            &mm->reverb_dry_smoother,
            plugin_data->port_table[SREVERB_REVERB_DRY] * 0.1f
        );
        f_dry_vol = f_db_to_linear_fast(
            mm->reverb_dry_smoother.last_value
        );

        v_rvb_reverb_set(
            &mm->reverb,
            plugin_data->port_table[SREVERB_REVERB_TIME] * 0.01f,
            f_db_to_linear_fast(
                mm->reverb_smoother.last_value
            ),
            plugin_data->port_table[SREVERB_REVERB_COLOR],
            plugin_data->port_table[SREVERB_REVERB_PRE_DELAY] * 0.001f,
            plugin_data->port_table[SREVERB_REVERB_HP]
        );

        v_rvb_reverb_run(
            &mm->reverb,
            input_buffer[i].left,
            input_buffer[i].right
        );

        v_sml_run(
            &mm->dry_pan_smoother,
            plugin_data->port_table[SREVERB_DRY_PAN] * 0.01f
        );

        v_pn2_set(
            &mm->dry_panner,
            mm->dry_pan_smoother.last_value,
            -3.0
        );

        v_sml_run(
            &mm->wet_pan_smoother,
            plugin_data->port_table[SREVERB_WET_PAN] * 0.01f
        );

        v_pn2_set(
            &mm->wet_panner,
            mm->wet_pan_smoother.last_value,
            -3.0
        );

        sample.left = (
            input_buffer[i].left * f_dry_vol * mm->dry_panner.gainL
        ) + (mm->reverb.output[0] * mm->wet_panner.gainL);
        sample.right = (
            input_buffer[i].right * f_dry_vol * mm->dry_panner.gainR
        ) + (mm->reverb.output[1] * mm->wet_panner.gainR);

        _plugin_mix(
            run_mode,
            i,
            output_buffer,
            sample.left,
            sample.right
        );
    }
}

SGFLT* sreverb_get_port_table(PluginHandle instance){
    t_sreverb* plugin_data = (t_sreverb*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *sreverb_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(SREVERB_COUNT);

    set_plugin_port(f_result, SREVERB_REVERB_TIME, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, SREVERB_REVERB_WET, -120.0f, -500.0f, 0.0f);
    set_plugin_port(f_result, SREVERB_REVERB_COLOR, 90.0f, 48.0f, 120.0f);
    set_plugin_port(f_result, SREVERB_REVERB_DRY, 0.0f, -500.0f, 0.0f);
    set_plugin_port(f_result, SREVERB_REVERB_PRE_DELAY, 10.0f, 0.0f, 1000.0f);
    set_plugin_port(f_result, SREVERB_REVERB_HP, 50.0f, 20.0f, 96.0f);
    set_plugin_port(f_result, SREVERB_DRY_PAN, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, SREVERB_WET_PAN, 0.0f, -100.0f, 100.0f);

    f_result->cleanup = v_sreverb_cleanup;
    f_result->connect_port = NULL;
    f_result->get_port_table = sreverb_get_port_table;
    f_result->instantiate = g_sreverb_instantiate;
    f_result->panic = v_sreverb_panic;
    f_result->load = v_sreverb_load;
    f_result->set_port_value = v_sreverb_set_port_value;
    f_result->set_cc_map = v_sreverb_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run = v_sreverb_run;
    f_result->on_stop = v_sreverb_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}

void v_sreverb_mono_init(
    t_sreverb_mono_modules* self,
    SGFLT a_sr,
    int a_plugin_uid
){
    g_sml_init(&self->dry_pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    self->dry_pan_smoother.last_value = 0.0f;
    g_pn2_init(&self->dry_panner);

    g_sml_init(&self->wet_pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    self->wet_pan_smoother.last_value = 0.0f;
    g_pn2_init(&self->wet_panner);

    g_sml_init(&self->reverb_smoother, a_sr, 100.0f, 0.0f, 0.001f);
    self->reverb_smoother.last_value = 0.0f;
    g_sml_init(&self->reverb_dry_smoother, a_sr, 100.0f, 0.0f, 0.001f);
    self->reverb_dry_smoother.last_value = 1.0f;

    g_rvb_reverb_init(&self->reverb, a_sr);
}

/*
void v_sreverb_destructor()
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
