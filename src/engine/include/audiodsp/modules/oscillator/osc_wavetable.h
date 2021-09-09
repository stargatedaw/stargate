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

#ifndef OSC_WAVETABLE_H
#define OSC_WAVETABLE_H

#include "audiodsp/lib/osc_core.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/interpolate-cubic.h"
#include "wavetables.h"
#include "compiler.h"


#define OSC_UNISON_MAX_VOICES 7

typedef struct{
    SGFLT inc;
    SGFLT last_pitch;
    SGFLT output;
}t_osc_wav;

typedef struct st_osc_wav_unison{
    SGFLT sr_recip;
    int voice_count;
    SGFLT bottom_pitch;
    SGFLT pitch_inc;
    SGFLT voice_inc[OSC_UNISON_MAX_VOICES];
    t_osc_core osc_cores[OSC_UNISON_MAX_VOICES];
    SGFLT * selected_wavetable;
    int selected_wavetable_sample_count;
    SGFLT selected_wavetable_sample_count_SGFLT;
    //Restart the oscillators at the same phase on each note-on
    SGFLT phases[OSC_UNISON_MAX_VOICES];
    //for generating instantaneous phase without affecting real phase
    SGFLT fm_phases[OSC_UNISON_MAX_VOICES];
    SGFLT uni_spread;
    //Set this with unison voices to prevent excessive volume
    SGFLT adjusted_amp;
    SGFLT current_sample;  //current output sample for the entire oscillator
}t_osc_wav_unison;


typedef SGFLT (*fp_get_osc_wav_func_ptr)(t_osc_wav*,t_wavetable*);

void v_osc_wav_set_uni_voice_count(t_osc_wav_unison*, int);
void v_osc_wav_set_unison_pitch(t_osc_wav_unison *, SGFLT, SGFLT);
SGFLT f_osc_wav_run_unison(t_osc_wav_unison *);
SGFLT f_osc_wav_run_unison_off(t_osc_wav_unison *);
void v_osc_wav_run(t_osc_core *, t_wavetable*);
void v_osc_wav_note_on_sync_phases(t_osc_wav_unison *);
void v_osc_wav_set_waveform(t_osc_wav_unison*, SGFLT *, int);
t_osc_wav * g_osc_get_osc_wav();
t_osc_wav_unison * g_osc_get_osc_wav_unison(SGFLT, int);
void v_osc_wav_apply_fm(t_osc_wav_unison*, SGFLT, SGFLT);
void g_osc_init_osc_wav_unison(
    t_osc_wav_unison * f_result,
    SGFLT a_sample_rate,
    int voice_num
);
void v_osc_wav_apply_fm_direct(
    t_osc_wav_unison* a_osc_ptr,
    SGFLT a_signal,
    SGFLT a_amt
);
void v_osc_wav_run_unison_core_only(
    t_osc_wav_unison * a_osc_ptr
);

#endif /* OSC_WAVETABLE_H */

