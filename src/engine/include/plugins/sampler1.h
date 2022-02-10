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

#ifndef SAMPLER1_PLUGIN_H
#define SAMPLER1_PLUGIN_H

#include <stdio.h>

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/interpolate-sinc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/voice.h"
#include "audiodsp/modules/filter/dc_offset_filter.h"
#include "audiodsp/modules/modulation/adsr.h"
#include "audiodsp/modules/modulation/ramp_env.h"
#include "audiodsp/modules/multifx/multifx3knob.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "audiodsp/modules/oscillator/noise.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "plugin.h"
#include "compiler.h"

#define SAMPLER1_POLYPHONY 32
#define SAMPLER1_POLYPHONY_THRESH 16

// How many buffers in between slow indexing operations.
// Buffer == users soundcard latency settings, ie: 512 samples
#define SAMPLER1_SLOW_INDEX_COUNT 64

#define SAMPLER1_SINC_INTERPOLATION_POINTS 25
#define SAMPLER1_SINC_INTERPOLATION_POINTS_DIV2 13

#define SAMPLER1_NOISE_COUNT 16

//Delimits the file string sent with configure().  Also used in the file saving format
#define SAMPLER1_FILES_STRING_DELIMITER '|'
//When used in place of "|", it tells the sampler to load the sample even if it's already been loaded once.

/*Provide an arbitrary maximum number of samples the user can load*/
#define SAMPLER1_MAX_SAMPLE_COUNT 100

//Total number of LFOs, ADSRs, other envelopes, etc...  Used for the PolyFX mod matrix
#define SAMPLER1_MODULATOR_COUNT 6
//How many modular PolyFX
#define SAMPLER1_MODULAR_POLYFX_COUNT 4
//How many ports per PolyFX, 3 knobs and a combobox
#define SAMPLER1_PORTS_PER_MOD_EFFECT 4
//How many knobs per PolyFX, 3 knobs
#define SAMPLER1_CONTROLS_PER_MOD_EFFECT 3

//The number of mono_fx groups
#define SAMPLER1_MONO_FX_GROUPS_COUNT SAMPLER1_MAX_SAMPLE_COUNT
#define SAMPLER1_MONO_FX_COUNT 4

// Ports

#define SAMPLER1_LABEL "Sampler1"

#define SAMPLER1_FIRST_CONTROL_PORT 3

#define SAMPLER1_ATTACK  3
#define SAMPLER1_DECAY   4
#define SAMPLER1_SUSTAIN 5
#define SAMPLER1_RELEASE 6
#define SAMPLER1_FILTER_ATTACK  7
#define SAMPLER1_FILTER_DECAY   8
#define SAMPLER1_FILTER_SUSTAIN 9
#define SAMPLER1_FILTER_RELEASE 10
#define SAMPLER1_LFO_PITCH 11
#define SAMPLER1_MAIN_VOLUME 12
#define SAMPLER1_MAIN_GLIDE 13
#define SAMPLER1_MAIN_PITCHBEND_AMT 14
#define SAMPLER1_PITCH_ENV_TIME 15
#define SAMPLER1_LFO_FREQ 16
#define SAMPLER1_LFO_TYPE 17
//From MultiFX
#define SAMPLER1_FX0_KNOB0  18
#define SAMPLER1_FX0_KNOB1 19
#define SAMPLER1_FX0_KNOB2  20
#define SAMPLER1_FX0_COMBOBOX 21
#define SAMPLER1_FX1_KNOB0  22
#define SAMPLER1_FX1_KNOB1  23
#define SAMPLER1_FX1_KNOB2  24
#define SAMPLER1_FX1_COMBOBOX 25
#define SAMPLER1_FX2_KNOB0  26
#define SAMPLER1_FX2_KNOB1  27
#define SAMPLER1_FX2_KNOB2  28
#define SAMPLER1_FX2_COMBOBOX 29
#define SAMPLER1_FX3_KNOB0  30
#define SAMPLER1_FX3_KNOB1  31
#define SAMPLER1_FX3_KNOB2  32
#define SAMPLER1_FX3_COMBOBOX 33
//PolyFX Mod Matrix
#define SAMPLER1_PFXMATRIX_FIRST_PORT 34

#define SAMPLER1_PFXMATRIX_GRP0DST0SRC0CTRL0  34
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC0CTRL1  35
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC0CTRL2  36
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC1CTRL0  37
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC1CTRL1  38
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC1CTRL2  39
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC2CTRL0  40
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC2CTRL1  41
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC2CTRL2  42
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC3CTRL0  43
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC3CTRL1  44
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC3CTRL2  45
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC0CTRL0  46
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC0CTRL1  47
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC0CTRL2  48
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC1CTRL0  49
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC1CTRL1  50
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC1CTRL2  51
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC2CTRL0  52
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC2CTRL1  53
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC2CTRL2  54
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC3CTRL0  55
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC3CTRL1  56
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC3CTRL2  57
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC0CTRL0  58
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC0CTRL1  59
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC0CTRL2  60
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC1CTRL0  61
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC1CTRL1  62
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC1CTRL2  63
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC2CTRL0  64
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC2CTRL1  65
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC2CTRL2  66
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC3CTRL0  67
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC3CTRL1  68
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC3CTRL2  69
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC0CTRL0  70
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC0CTRL1  71
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC0CTRL2  72
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC1CTRL0  73
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC1CTRL1  74
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC1CTRL2  75
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC2CTRL0  76
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC2CTRL1  77
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC2CTRL2  78
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC3CTRL0  79
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC3CTRL1  80
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC3CTRL2  81


#define SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL0  82
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL1  83
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC4CTRL2  84
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC4CTRL0  85
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC4CTRL1  86
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC4CTRL2  87
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC4CTRL0  88
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC4CTRL1  89
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC4CTRL2  90
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC4CTRL0  91
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC4CTRL1  92
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC4CTRL2  93

#define SAMPLER1_PFXMATRIX_GRP0DST0SRC5CTRL0  94
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC5CTRL1  95
#define SAMPLER1_PFXMATRIX_GRP0DST0SRC5CTRL2  96
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC5CTRL0  97
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC5CTRL1  98
#define SAMPLER1_PFXMATRIX_GRP0DST1SRC5CTRL2  99
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC5CTRL0  100
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC5CTRL1  101
#define SAMPLER1_PFXMATRIX_GRP0DST2SRC5CTRL2  102
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC5CTRL0  103
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC5CTRL1  104
#define SAMPLER1_PFXMATRIX_GRP0DST3SRC5CTRL2  105


//End PolyFX Mod Matrix

/*The first port to use when enumerating the ports for mod_matrix controls.  All of the mod_matrix ports should be sequential,
 * any additional ports should prepend this port number*/
#define SAMPLER1_FIRST_SAMPLE_TABLE_PORT 106

/*The range of ports for sample pitch*/
#define SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MIN     SAMPLER1_FIRST_SAMPLE_TABLE_PORT
#define SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MAX     (SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

/*The range of ports for the low note to play a sample on*/
#define SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MIN   SAMPLER1_SAMPLE_PITCH_PORT_RANGE_MAX
#define SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MAX   (SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

/*The range of ports for the high note to play a sample on*/
#define SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MIN  SAMPLER1_PLAY_PITCH_LOW_PORT_RANGE_MAX
#define SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MAX  (SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

/*The range of ports for sample volume*/
#define SG_SAMPLE_VOLUME_PORT_RANGE_MIN    SAMPLER1_PLAY_PITCH_HIGH_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MAX    (SG_SAMPLE_VOLUME_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_START_PORT_RANGE_MIN    SAMPLER1_SAMPLE_VOLUME_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_START_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_START_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_END_PORT_RANGE_MIN    SAMPLER1_SAMPLE_START_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_END_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_END_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MIN    SAMPLER1_SAMPLE_END_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MIN    SAMPLER1_SAMPLE_VEL_SENS_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MIN    SAMPLER1_SAMPLE_VEL_LOW_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_PITCH_PORT_RANGE_MIN    SAMPLER1_SAMPLE_VEL_HIGH_PORT_RANGE_MAX
#define SAMPLER1_PITCH_PORT_RANGE_MAX    (SAMPLER1_PITCH_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_TUNE_PORT_RANGE_MIN    SAMPLER1_PITCH_PORT_RANGE_MAX
#define SAMPLER1_TUNE_PORT_RANGE_MAX    (SAMPLER1_TUNE_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN    SAMPLER1_TUNE_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MIN    SAMPLER1_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MIN    SAMPLER1_SAMPLE_LOOP_START_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MIN    SAMPLER1_SAMPLE_LOOP_END_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

//MonoFX0
#define SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MIN    SAMPLER1_SAMPLE_LOOP_MODE_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MAX    (SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MIN    SAMPLER1_MONO_FX0_KNOB0_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MAX    (SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MIN    SAMPLER1_MONO_FX0_KNOB1_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MAX    (SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MIN    SAMPLER1_MONO_FX0_KNOB2_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MAX    (SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
//MonoFX1
#define SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MIN    SAMPLER1_MONO_FX0_COMBOBOX_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MAX    (SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MIN    SAMPLER1_MONO_FX1_KNOB0_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MAX    (SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MIN    SAMPLER1_MONO_FX1_KNOB1_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MAX    (SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MIN    SAMPLER1_MONO_FX1_KNOB2_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MAX    (SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
//MonoFX2
#define SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MIN    SAMPLER1_MONO_FX1_COMBOBOX_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MAX    (SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MIN    SAMPLER1_MONO_FX2_KNOB0_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MAX    (SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MIN    SAMPLER1_MONO_FX2_KNOB1_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MAX    (SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MIN    SAMPLER1_MONO_FX2_KNOB2_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MAX    (SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
//MonoFX3
#define SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MIN    SAMPLER1_MONO_FX2_COMBOBOX_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MAX    (SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MIN    SAMPLER1_MONO_FX3_KNOB0_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MAX    (SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MIN    SAMPLER1_MONO_FX3_KNOB1_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MAX    (SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)

#define SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MIN    SAMPLER1_MONO_FX3_KNOB2_PORT_RANGE_MAX
#define SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MAX    (SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MIN + SAMPLER1_MONO_FX_GROUPS_COUNT)
//Sample FX Group
#define SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN    SAMPLER1_MONO_FX3_COMBOBOX_PORT_RANGE_MAX
#define SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MAX    (SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

//Noise amp
#define SAMPLER1_NOISE_AMP_MIN SAMPLER1_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MAX
#define SAMPLER1_NOISE_AMP_MAX (SAMPLER1_NOISE_AMP_MIN + SAMPLER1_MAX_SAMPLE_COUNT)
//Noise type
#define SAMPLER1_NOISE_TYPE_MIN SAMPLER1_NOISE_AMP_MAX
#define SAMPLER1_NOISE_TYPE_MAX (SAMPLER1_NOISE_TYPE_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

//sample fade-in
#define SAMPLER1_SAMPLE_FADE_IN_MIN SAMPLER1_NOISE_TYPE_MAX
#define SAMPLER1_SAMPLE_FADE_IN_MAX (SAMPLER1_SAMPLE_FADE_IN_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

//sample fade-out
#define SAMPLER1_SAMPLE_FADE_OUT_MIN SAMPLER1_SAMPLE_FADE_IN_MAX
#define SAMPLER1_SAMPLE_FADE_OUT_MAX (SAMPLER1_SAMPLE_FADE_OUT_MIN + SAMPLER1_MAX_SAMPLE_COUNT)

#define SAMPLER1_FIRST_EQ_PORT SAMPLER1_SAMPLE_FADE_OUT_MAX

/* Stacked as:
 * 100 *
 *     [freq, bw, gain] * 6
 */
#define SAMPLER1_LAST_EQ_PORT (SAMPLER1_FIRST_EQ_PORT + (18 * 100))

#define SAMPLER1_LFO_PITCH_FINE SAMPLER1_LAST_EQ_PORT
#define SAMPLER1_MIN_NOTE (SAMPLER1_LFO_PITCH_FINE + 1)
#define SAMPLER1_MAX_NOTE (SAMPLER1_MIN_NOTE + 1)
#define SAMPLER1_MAIN_PITCH (SAMPLER1_MAX_NOTE + 1)
#define SAMPLER1_ADSR_LIN_MAIN (SAMPLER1_MAIN_PITCH + 1)  // 5510
#define SAMPLER1_ATTACK_START 5511
#define SAMPLER1_ATTACK_END 5512
#define SAMPLER1_DECAY_START 5513
#define SAMPLER1_DECAY_END 5514
#define SAMPLER1_SUSTAIN_START 5515
#define SAMPLER1_SUSTAIN_END 5516
#define SAMPLER1_RELEASE_START 5517
#define SAMPLER1_RELEASE_END 5518

#define SAMPLER1_PORT_COUNT 5519
struct st_sampler1;

typedef struct
{
    t_mf3_multi multieffect[SAMPLER1_MONO_FX_COUNT];
    fp_mf3_run fx_func_ptr[SAMPLER1_MONO_FX_COUNT];
    t_eq6 eqs;
}t_sampler1_mfx_group;

typedef struct
{
    fp_mf3_run fx_func_ptr;
    fp_mf3_reset fx_reset_ptr;
    t_mf3_multi multieffect;
    int polyfx_mod_counts;
}t_sampler1_pfx_group;

typedef struct {
    t_smoother_linear pitchbend_smoother;

    t_dco_dc_offset_filter dc_offset_filters[2];
    t_sampler1_mfx_group mfx[SAMPLER1_MONO_FX_GROUPS_COUNT];

    t_white_noise white_noise1[SAMPLER1_NOISE_COUNT];
    int noise_current_index;

    t_sinc_interpolator sinc_interpolator;
} t_sampler1_mono_modules;

typedef struct
{
    int sample_fade_in_end_sample;
    SGFLT sample_fade_in_inc;
    int sample_fade_out_start_sample;
    SGFLT sample_fade_out_dec;
    SGFLT sample_fade_amp;
    t_int_frac_read_head sample_read_heads;
    SGFLT vel_sens_output;
}t_sampler1_pfx_sample;

typedef struct
{
    t_pn2_panner2 panner;
    t_adsr adsr_filter;
    fp_adsr_run adsr_run_func;
    t_adsr adsr_amp;
    t_ramp_env glide_env;
    t_ramp_env ramp_env;

    // For glide
    SGFLT last_pitch;
    SGFLT base_pitch;

    SGFLT target_pitch;

    SGFLT filter_output;  //For assigning the filter output to

    // This corresponds to the current sample being processed on this voice.
    // += this to the output buffer when finished.
    SGFLT current_sample;

    t_lfs_lfo lfo1;

    SGFLT note_f;
    SGFLT noise_sample;

    t_sampler1_pfx_sample samples[SAMPLER1_MAX_SAMPLE_COUNT];

    t_sampler1_pfx_group effects [SAMPLER1_MODULAR_POLYFX_COUNT];

    SGFLT multifx_current_sample[2];

    SGFLT * modulator_outputs[SAMPLER1_MODULATOR_COUNT];

    int noise_index;

    SGFLT velocity_track;
    SGFLT keyboard_track;
    int velocities;

    //Sample indexes for each note to play
    int sample_indexes[SAMPLER1_MAX_SAMPLE_COUNT];
    //The count of sample indexes to iterate through
    int sample_indexes_count;

    //PolyFX modulation streams
     //The index of the control to mod, currently 0-2
    int polyfx_mod_ctrl_indexes[SAMPLER1_MODULAR_POLYFX_COUNT][
        (SAMPLER1_CONTROLS_PER_MOD_EFFECT * SAMPLER1_MODULATOR_COUNT)];
    //The index of the modulation source(LFO, ADSR, etc...) to multiply by
    int polyfx_mod_src_index[SAMPLER1_MODULAR_POLYFX_COUNT][
        (SAMPLER1_CONTROLS_PER_MOD_EFFECT * SAMPLER1_MODULATOR_COUNT)];
    //The value of the mod_matrix knob, multiplied by .01
    SGFLT polyfx_mod_matrix_values[SAMPLER1_MODULAR_POLYFX_COUNT][
        (SAMPLER1_CONTROLS_PER_MOD_EFFECT * SAMPLER1_MODULATOR_COUNT)];

    //Active PolyFX to process
    int active_polyfx[SAMPLER1_MODULAR_POLYFX_COUNT];
    int active_polyfx_count;

} t_sampler1_poly_voice;

typedef struct {
    PluginData *basePitch;
    PluginData *low_note;
    PluginData *high_note;
    PluginData *sample_vol;
    PluginData *sampleStarts;
    PluginData *sampleEnds;
    PluginData *sampleLoopStarts;
    PluginData *sampleLoopEnds;
    PluginData *sampleLoopModes;
    PluginData *sampleFadeInEnds;
    PluginData *sampleFadeOutStarts;
    PluginData *sample_vel_sens;
    PluginData *sample_vel_low;
    PluginData *sample_vel_high;
    PluginData *sample_pitch;
    PluginData *sample_tune;
    PluginData *sample_interpolation_mode;
    PluginData *noise_amp;
    PluginData *noise_type;
    //For the per-sample interpolation modes
    int (*ratio_function_ptr)(struct st_sampler1 * plugin_data, int n);
    void (*interpolation_mode)(struct st_sampler1 * plugin_data, int n, int ch);
    SGFLT       sample_last_interpolated_value;
    t_audio_pool_item * audio_pool_items;
    SGFLT       sampleStartPos;
    SGFLT       sampleEndPos;
    // There is no sampleLoopEndPos because the regular
    // sample end is re-used for this purpose
    SGFLT       sampleLoopStartPos;
    SGFLT       sample_amp;     //linear, for multiplying
    SGFLT adjusted_base_pitch;
    fp_noise_func_ptr noise_func_ptr;
    int noise_index;
    SGFLT noise_linamp;
}t_sampler1_sample;

typedef struct st_sampler1 {
    char pad1[CACHE_LINE_SIZE];
    t_sampler1_sample samples[SAMPLER1_MAX_SAMPLE_COUNT];

    PluginData *mfx_knobs[SAMPLER1_MONO_FX_GROUPS_COUNT][
        SAMPLER1_MONO_FX_COUNT][SAMPLER1_CONTROLS_PER_MOD_EFFECT];
    PluginData *mfx_comboboxes[SAMPLER1_MONO_FX_GROUPS_COUNT][
        SAMPLER1_MONO_FX_COUNT];

    PluginData *main_pitch;
    PluginData *adsr_lin_main;
    PluginData *attack;
    PluginData *attack_start;
    PluginData *attack_end;
    PluginData *decay;
    PluginData *decay_start;
    PluginData *decay_end;
    PluginData *sustain;
    PluginData *sustain_start;
    PluginData *sustain_end;
    PluginData *release;
    PluginData *release_start;
    PluginData *release_end;

    PluginData *attack_f;
    PluginData *decay_f;
    PluginData *sustain_f;
    PluginData *release_f;

    PluginData *main_vol;

    PluginData *main_glide;
    PluginData *main_pb_amt;

    PluginData *pitch_env_time;

    PluginData *lfo_freq;
    PluginData *lfo_type;
    PluginData *lfo_pitch;
    PluginData *lfo_pitch_fine;

    PluginData *min_note;
    PluginData *max_note;

    //Corresponds to the actual knobs on the effects themselves,
    //not the mod matrix
    PluginData *pfx_mod_knob[SAMPLER1_MODULAR_POLYFX_COUNT][
        SAMPLER1_CONTROLS_PER_MOD_EFFECT];

    PluginData *fx_combobox[SAMPLER1_MODULAR_POLYFX_COUNT];

    //PolyFX Mod Matrix
    //Corresponds to the mod matrix spinboxes
    PluginData *polyfx_mod_matrix[SAMPLER1_MODULAR_POLYFX_COUNT][
        SAMPLER1_MODULATOR_COUNT][SAMPLER1_CONTROLS_PER_MOD_EFFECT];

    //End from PolyFX Mod Matrix

    //These 2 calculate which channels are assigned to a sample
    //and should be processed
    int monofx_channel_index[SAMPLER1_MONO_FX_GROUPS_COUNT];
    int monofx_channel_index_count;
    //Tracks which indexes are in use
    int monofx_channel_index_tracker[SAMPLER1_MONO_FX_GROUPS_COUNT];
    //The MonoFX group selected for each sample
    PluginData *sample_mfx_groups[SAMPLER1_MONO_FX_GROUPS_COUNT];
    int sample_mfx_groups_index[SAMPLER1_MONO_FX_GROUPS_COUNT];
    /*TODO:  Deprecate these 2?*/
    int loaded_samples[SAMPLER1_MAX_SAMPLE_COUNT];
    int loaded_samples_count;
    /*Used as a boolean when determining if a sample has already been loaded*/
    int sample_is_loaded;
    /*The index of the current sample being played*/
    int current_sample;

    SGFLT ratio;
    t_voc_voices voices;
    long sampleNo;

    SGFLT sample[2];

    t_sampler1_mono_modules mono_modules;
    t_pit_ratio * smp_pit_ratio;
    t_sampler1_poly_voice data[SAMPLER1_POLYPHONY];

    //These are used for storing the mono FX buffers from the polyphonic voices.
    SGFLT mono_fx_buffers[SAMPLER1_MONO_FX_GROUPS_COUNT][2];
    //For indexing operations that don't need to track realtime events closely
    int i_slow_index;

    SGFLT amp;  //linear amplitude, from the main volume knob

    SGFLT sv_pitch_bend_value;
    SGFLT sv_last_note;  //For glide

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    SGFLT port_table[SAMPLER1_PORT_COUNT];
    int plugin_uid;
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_sampler1;


void g_sampler1_poly_init(t_sampler1_poly_voice*, SGFLT);

void v_sampler1_poly_note_off(
    t_sampler1_poly_voice * a_voice,
    int a_fast_release
);

void g_sampler1_mono_init(t_sampler1_mono_modules*, SGFLT);
PluginDescriptor *sampler1_plugin_descriptor();

#endif
