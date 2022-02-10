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

#ifndef SG_VOCODER_PLUGIN_H
#define SG_VOCODER_PLUGIN_H

#include "plugin.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/filter/vocoder.h"
#include "compiler.h"


#define SG_VOCODER_WET 0
#define SG_VOCODER_MODULATOR 1
#define SG_VOCODER_CARRIER 2

#define SG_VOCODER_FIRST_CONTROL_PORT 0

#define SG_VOCODER_LAST_CONTROL_PORT 2
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SG_VOCODER_COUNT 3

typedef struct {
    t_smoother_linear carrier_smoother;
    t_smoother_linear wet_smoother;
    t_vdr_vocoder vocoder;
    t_smoother_linear modulator_smoother;
} t_sg_vocoder_mono_modules;

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    PluginData * wet;
    PluginData * modulator;
    PluginData * carrier;
    SGFLT fs;
    t_sg_vocoder_mono_modules mono_modules;

    int i_mono_out;
    int i_buffer_clear;

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    SGFLT port_table[SG_VOCODER_COUNT];
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_sg_vocoder;

void v_sg_vocoder_mono_init(t_sg_vocoder_mono_modules*, SGFLT, int);
PluginDescriptor *sg_vocoder_plugin_descriptor();

#endif /* SG_VOCODER_PLUGIN_H */

