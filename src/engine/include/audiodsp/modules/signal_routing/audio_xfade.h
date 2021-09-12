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

#ifndef AUDIO_XFADE_H
#define AUDIO_XFADE_H

#include "audiodsp/lib/amp.h"
#include "compiler.h"

//#define AXF_DEBUG_MODE

typedef struct st_audio_xfade {
    SGFLT mid_point;
    SGFLT mid_point_50_minus;
    SGFLT in1_mult;
    SGFLT in2_mult;
#ifdef AXF_DEBUG_MODE
    int debug_counter;
#endif
}t_audio_xfade;

/*void v_axf_set_xfade(
 * t_audio_xfade *,
 * SGFLT a_point // 0 to 1
 * )
 */
void v_axf_set_xfade(t_audio_xfade*, SGFLT);
SGFLT f_axf_run_xfade(t_audio_xfade*, SGFLT, SGFLT);
void g_axf_init(t_audio_xfade* f_result, SGFLT a_mid_point);

/*t_audio_xfade * g_axf_get_audio_xfade
 * (
 * SGFLT a_mid_point //This is the negative gain at 0.5 for both channels.
 *                   //-3 or -6 is a good value
 * )
 */
t_audio_xfade * g_axf_get_audio_xfade(SGFLT a_mid_point);

#endif /* AUDIO_XFADE_H */

