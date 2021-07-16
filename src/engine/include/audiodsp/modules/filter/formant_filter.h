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

#ifndef FORMANT_FILTER_H
#define FORMANT_FILTER_H

#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"


extern SG_THREAD_LOCAL SGFLT f_formant_pitches[3][10];

/* ^^^^ Generated with this Python script:
from math import log
f_list = []
f_list.append([730, 1090, 2440]) #"a"
f_list.append([660, 1720, 2410]) #"ae"
f_list.append([530, 1840, 2480]) #"e"
f_list.append([270, 2290, 3010]) #"iy"
f_list.append([390, 1990, 2550]) #"i"
f_list.append([490, 1350, 1690]) #"er"
f_list.append([570, 840, 2410]) #"ow"
f_list.append([300, 870, 2240]) #"oo"
f_list.append([520, 1190, 2390]) #"uh"
f_list.append([440, 1020, 2240]) #"u"

def hz_to_pitch(a_hz):
    return ((12.0 * log(a_hz * (1.0/440.0), 2.0)) + 57.0)

print("SGFLT f_formant_pitches[3][" + str(len(f_list)) + "] =\n{")
for i in range(3):
    f_print = "    {"
    for f_item in f_list:
        f_print += str(hz_to_pitch(f_item[i]))
        f_print += ", "
    print(f_print + "},")
print "};"

 *  */

typedef struct
{
    t_state_variable_filter * filters[3][2];
    SGFLT output0;
    SGFLT output1;
    SGFLT pitch_tmp;
    SGFLT last_pos;
    SGFLT last_wet;
    t_audio_xfade xfade;
}t_for_formant_filter;

t_for_formant_filter * g_for_formant_filter_get(SGFLT);
void v_for_formant_filter_set(t_for_formant_filter*, SGFLT, SGFLT);
void v_for_formant_filter_run(t_for_formant_filter*, SGFLT, SGFLT);


void g_for_init(t_for_formant_filter * f_result, SGFLT a_sr);

//SGFLT growl_table[25][3][5];

typedef struct
{
    t_svf2_filter filter;
    SGFLT amp;
}t_grw_band;

typedef struct
{
    SGFLT output0;
    SGFLT output1;
    t_grw_band bands[5];
    t_audio_xfade xfade;
    SGFLT last_pos;
    SGFLT last_type;
    SGFLT last_wet;
}t_grw_growl_filter;

t_grw_growl_filter * g_grw_growl_filter_get(SGFLT);
void v_grw_growl_filter_set(t_grw_growl_filter*, SGFLT, SGFLT, SGFLT);
void v_grw_growl_filter_run(t_grw_growl_filter*, SGFLT, SGFLT);
void v_grw_growl_filter_free(t_grw_growl_filter*);
void g_grw_init(t_grw_growl_filter * f_result, SGFLT a_sr);

#endif /* FORMANT_FILTER_H */

