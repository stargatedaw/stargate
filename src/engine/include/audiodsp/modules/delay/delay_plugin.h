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
#ifndef SG_DELAY_H
#define SG_DELAY_H

//#define SG_DELAY_DEBUG_MODE

#include "delay.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "audiodsp/modules/modulation/env_follower.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/signal_routing/dry_wet.h"
#include "compiler.h"

/* A multi-mode delay module.  This is a complete delay with stereo,
 * ping-pong, etc... modes
 * feedback can be routed out and back into the module.
 */
typedef struct {
    t_delay_tap tap0;
    t_delay_tap tap1;
    SGFLT output0;  //mixed signal out
    SGFLT output1;  //mixed signal out
    SGFLT feedback0;  //feedback out/in
    SGFLT feedback1;  //feedback out/in
    SGFLT feedback_db;
    SGFLT feedback_linear;
    t_dw_dry_wet dw0;
    t_dw_dry_wet dw1;
    t_audio_xfade stereo_xfade0;
    t_audio_xfade stereo_xfade1;

    t_enf_env_follower feedback_env_follower;  //Checks for overflow
    t_enf_env_follower input_env_follower;  //Checks for overflow
    SGFLT wet_dry_diff;  //difference between wet and dry output volume
    SGFLT combined_inputs;  //Add output 0 and 1
    t_lim_limiter limiter;
    SGFLT last_duck;
    SGFLT limiter_gain;

    t_state_variable_filter svf0;
    t_state_variable_filter svf1;
    t_delay_simple delay0;
    t_delay_simple delay1;

} t_sg_delay;

/*t_sg_delay * g_ldl_get_delay(
 * SGFLT a_seconds, //The maximum amount of time for the delay to buffer
 * SGFLT a_sr  //sample rate
 * )
 */
t_sg_delay * g_ldl_get_delay(SGFLT,SGFLT);
/*void v_ldl_set_delay(
 * t_sg_delay* a_dly,
 * SGFLT a_seconds,
 * SGFLT a_feedback_db, //This should not exceed -2 or it could explode
 * int a_is_ducking,
 * SGFLT a_wet,
 * SGFLT a_dry,
 * SGFLT a_stereo)  //Crossfading between dual-mono and stereo.  0 to 1
 */
void v_ldl_set_delay(
    t_sg_delay*,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT,
    SGFLT
);
void v_ldl_run_delay(t_sg_delay*,SGFLT,SGFLT);

#endif /* SG_DELAY_H */

