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
#include "audiodsp/lib/math.h"
#include "audiodsp/modules/filter/svf.h"
#include "plugin.h"
#include "plugins/fm1.h"
#include "csv/split.h"
#include "csv/1d.h"
#include "files.h"

void v_run_fm1_voice(
    t_fm1*,
    t_voc_single_voice*,
    t_fm1_poly_voice*,
    struct SamplePair*,
    int
);

void v_cleanup_fm1(PluginHandle instance){
    free(instance);
}

void v_fm1_set_cc_map(PluginHandle instance, char* a_msg){
    t_fm1 *plugin = (t_fm1*)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

void v_fm1_or_prep(PluginHandle instance, SGFLT sample_rate){
    t_fm1 *plugin = (t_fm1 *)instance;

    plugin->mono_modules.fm_macro_smoother[0].last_value =
        (*plugin->fm_macro[0] * 0.01f);

    plugin->mono_modules.fm_macro_smoother[1].last_value =
        (*plugin->fm_macro[1] * 0.01f);
}

void fm1Panic(PluginHandle instance){
    t_fm1 *plugin = (t_fm1 *)instance;
    int f_i;
    for(f_i = 0; f_i < FM1_POLYPHONY; ++f_i){
        v_adsr_kill(&plugin->data[f_i].adsr_amp);
        v_adsr_kill(&plugin->data[f_i].adsr_main);
    }
}

struct FM1OscArg {
    t_fm1* plugin_data;
    t_fm1_poly_voice* a_voice;
};

struct ResamplerStereoPair fm1_run_voice_osc(void* arg){
    struct FM1OscArg* _arg = (struct FM1OscArg*)arg;
    t_fm1* plugin_data = _arg->plugin_data;
    t_fm1_poly_voice* a_voice = _arg->a_voice;
    struct ResamplerStereoPair result = {};
    int f_osc_num;
    SGFLT f_macro_amp;
    SGFLT f_osc_amp;
    t_fm1_osc* f_osc;
    t_fm1_mono_modules* mm = &plugin_data->mono_modules;

    for(f_osc_num = 0; f_osc_num < FM1_OSC_COUNT; ++f_osc_num){
        f_macro_amp = 0.0f;
        f_osc = &a_voice->osc[f_osc_num];

        if(f_osc->osc_on){
            v_osc_wav_set_unison_pitch(
                &f_osc->osc_wavtable,
                f_osc->osc_uni_spread,
                (
                    a_voice->base_pitch +
                    (*plugin_data->osc[f_osc_num].pitch) +
                    ((*plugin_data->osc[f_osc_num].tune) * 0.01f)
                )
            );

            int f_i;
            for(f_i = 0; f_i < FM1_OSC_COUNT; ++f_i){
                f_osc->fm_osc_values[f_i] = f_osc->osc_fm[f_i];
            }

            for(f_i = 0; f_i < 2; ++f_i){
                if(mm->fm_macro_smoother[f_i].last_value > 0.0f){
                    int f_i2;
                    for(f_i2 = 0; f_i2 < FM1_OSC_COUNT; ++f_i2){
                        f_osc->fm_osc_values[f_i2] +=
                          ((*plugin_data->fm_macro_values[f_i][f_osc_num][f_i2]
                                * 0.005f) *
                            mm->fm_macro_smoother[f_i].last_value);
                    }

                    if(f_osc->osc_macro_amp[f_i] != 0.0f){
                        f_macro_amp += mm->fm_macro_smoother[f_i].last_value *
                            f_osc->osc_macro_amp[f_i];
                    }
                }
            }

            for(f_i = 0; f_i < FM1_OSC_COUNT; ++f_i){
                if(f_osc->fm_osc_values[f_i] < 0.0f){
                    f_osc->fm_osc_values[f_i] = 0.0f;
                } else if(f_osc->fm_osc_values[f_i] > 0.5f){
                    f_osc->fm_osc_values[f_i] = 0.5f;
                }

                if(f_i <= f_osc_num){
                    v_osc_wav_apply_fm(
                        &f_osc->osc_wavtable,
                        a_voice->osc[f_i].fm_last,
                        f_osc->fm_osc_values[f_i]
                    );
                } else {
                    v_osc_wav_apply_fm_direct(
                        &f_osc->osc_wavtable,
                        a_voice->osc[f_i].fm_last,
                        f_osc->fm_osc_values[f_i]
                    );
                }
            }

            if(f_osc->adsr_amp_on){
                v_adsr_run_db(&f_osc->adsr_amp_osc);
                f_osc->fm_last = f_osc_wav_run_unison(
                    &f_osc->osc_wavtable
                ) * f_osc->adsr_amp_osc.output;
            } else {
                f_osc->fm_last = f_osc_wav_run_unison(&f_osc->osc_wavtable);
            }

            if(f_osc->osc_audible || f_macro_amp >= 1.0f){
                f_osc_amp = f_osc->osc_linamp * f_db_to_linear(f_macro_amp);

                if(f_osc_amp >= 1.0f){  //clip at 0dB
                    result.left += f_osc->fm_last *
                        a_voice->osc[f_osc_num].panner.gainL;
                    result.right += f_osc->fm_last *
                        a_voice->osc[f_osc_num].panner.gainR;
                } else {
                    result.left += f_osc->fm_last * f_osc_amp *
                        a_voice->osc[f_osc_num].panner.gainL;
                    result.right += f_osc->fm_last * f_osc_amp *
                        a_voice->osc[f_osc_num].panner.gainR;
                }
            }
        }
    }
    return result;
}

void v_fm1_on_stop(PluginHandle instance){
    t_fm1 *plugin = (t_fm1 *)instance;
    int f_i;
    for(f_i = 0; f_i < FM1_POLYPHONY; ++f_i){
        v_fm1_poly_note_off(&plugin->data[f_i], 0);
    }

    plugin->sv_pitch_bend_value = 0.0f;
}

void v_fm1_connect_port(
    PluginHandle instance,
    int port,
    PluginData * data
){
    t_fm1 *plugin;

    plugin = (t_fm1 *) instance;

    switch (port){
        case FM1_ATTACK_MAIN: plugin->attack_main = data; break;
        case FM1_ATTACK_MAIN_START: plugin->attack_main_start = data; break;
        case FM1_ATTACK_MAIN_END: plugin->attack_main_end = data; break;
        case FM1_DECAY_MAIN: plugin->decay_main = data; break;
        case FM1_DECAY_MAIN_START: plugin->decay_main_start = data; break;
        case FM1_DECAY_MAIN_END: plugin->decay_main_end = data; break;
        case FM1_SUSTAIN_MAIN: plugin->sustain_main = data; break;
        case FM1_SUSTAIN_MAIN_START: plugin->sustain_main_start = data; break;
        case FM1_SUSTAIN_MAIN_END: plugin->sustain_main_end = data; break;
        case FM1_RELEASE_MAIN: plugin->release_main = data; break;
        case FM1_RELEASE_MAIN_START: plugin->release_main_start = data; break;
        case FM1_RELEASE_MAIN_END: plugin->release_main_end = data; break;

        case FM1_ATTACK1: plugin->osc[0].attack = data; break;
        case FM1_DECAY1: plugin->osc[0].decay = data; break;
        case FM1_SUSTAIN1: plugin->osc[0].sustain = data; break;
        case FM1_RELEASE1: plugin->osc[0].release = data; break;
        case FM1_ATTACK2: plugin->osc[1].attack = data; break;
        case FM1_DECAY2: plugin->osc[1].decay = data; break;
        case FM1_SUSTAIN2: plugin->osc[1].sustain = data; break;
        case FM1_RELEASE2: plugin->osc[1].release = data; break;

        case FM1_NOISE_AMP:
            plugin->noise_amp = data;
            break;
        case FM1_MAIN_VOLUME:
            plugin->main_vol = data;
            break;
        case FM1_OSC1_PITCH:
            plugin->osc[0].pitch = data;
            break;
        case FM1_OSC1_TUNE:
            plugin->osc[0].tune = data;
            break;
        case FM1_OSC1_TYPE: plugin->osc[0].type = data; break;
        case FM1_OSC1_VOLUME:
            plugin->osc[0].vol = data;
            break;
        case FM1_OSC2_PITCH:
            plugin->osc[1].pitch = data;
            break;
        case FM1_OSC2_TUNE:
            plugin->osc[1].tune = data;
            break;
        case FM1_OSC2_TYPE: plugin->osc[1].type = data; break;
        case FM1_OSC2_VOLUME:
            plugin->osc[1].vol = data;
            break;
        case FM1_OSC1_UNISON_VOICES:
            plugin->osc[0].uni_voice = data;
            break;
        case FM1_OSC1_UNISON_SPREAD:
            plugin->osc[0].uni_spread = data;
            break;
        case FM1_OSC2_UNISON_VOICES:
            plugin->osc[1].uni_voice = data;
            break;
        case FM1_OSC2_UNISON_SPREAD:
            plugin->osc[1].uni_spread = data;
            break;
        case FM1_OSC3_UNISON_VOICES:
            plugin->osc[2].uni_voice = data;
            break;
        case FM1_OSC3_UNISON_SPREAD:
            plugin->osc[2].uni_spread = data;
            break;
        case FM1_MAIN_GLIDE:
            plugin->main_glide = data;
            break;
        case FM1_MAIN_PITCHBEND_AMT:
            plugin->main_pb_amt = data;
            break;


        case FM1_ATTACK_PFX1:
            plugin->pfx_attack = data;
            break;
        case FM1_DECAY_PFX1:
            plugin->pfx_decay = data;
            break;
        case FM1_SUSTAIN_PFX1:
            plugin->pfx_sustain = data;
            break;
        case FM1_RELEASE_PFX1:
            plugin->pfx_release = data;
            break;
        case FM1_ATTACK_PFX2:
            plugin->pfx_attack_f = data;
            break;
        case FM1_DECAY_PFX2:
            plugin->pfx_decay_f = data;
            break;
        case FM1_SUSTAIN_PFX2:
            plugin->pfx_sustain_f = data;
            break;
        case FM1_RELEASE_PFX2:
            plugin->pfx_release_f = data;
            break;
        case FM1_RAMP_ENV_TIME:
            plugin->pitch_env_time = data;
            break;
        case FM1_LFO_FREQ:
            plugin->lfo_freq = data;
            break;
        case FM1_LFO_TYPE:
            plugin->lfo_type = data;
            break;

        case FM1_FX0_KNOB0: plugin->pfx_mod_knob[0][0] = data; break;
        case FM1_FX0_KNOB1: plugin->pfx_mod_knob[0][1] = data; break;
        case FM1_FX0_KNOB2: plugin->pfx_mod_knob[0][2] = data; break;
        case FM1_FX1_KNOB0: plugin->pfx_mod_knob[1][0] = data; break;
        case FM1_FX1_KNOB1: plugin->pfx_mod_knob[1][1] = data; break;
        case FM1_FX1_KNOB2: plugin->pfx_mod_knob[1][2] = data; break;
        case FM1_FX2_KNOB0: plugin->pfx_mod_knob[2][0] = data; break;
        case FM1_FX2_KNOB1: plugin->pfx_mod_knob[2][1] = data; break;
        case FM1_FX2_KNOB2: plugin->pfx_mod_knob[2][2] = data; break;
        case FM1_FX3_KNOB0: plugin->pfx_mod_knob[3][0] = data; break;
        case FM1_FX3_KNOB1: plugin->pfx_mod_knob[3][1] = data; break;
        case FM1_FX3_KNOB2: plugin->pfx_mod_knob[3][2] = data; break;

        case FM1_FX0_COMBOBOX: plugin->fx_combobox[0] = data; break;
        case FM1_FX1_COMBOBOX: plugin->fx_combobox[1] = data; break;
        case FM1_FX2_COMBOBOX: plugin->fx_combobox[2] = data; break;
        case FM1_FX3_COMBOBOX: plugin->fx_combobox[3] = data; break;
        //End from MultiFX
        /*PolyFX mod matrix port connections*/
        case FM1_PFXMATRIX_GRP0DST0SRC0CTRL0: plugin->polyfx_mod_matrix[0][0][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC0CTRL1: plugin->polyfx_mod_matrix[0][0][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC0CTRL2: plugin->polyfx_mod_matrix[0][0][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC1CTRL0: plugin->polyfx_mod_matrix[0][1][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC1CTRL1: plugin->polyfx_mod_matrix[0][1][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC1CTRL2: plugin->polyfx_mod_matrix[0][1][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC2CTRL0: plugin->polyfx_mod_matrix[0][2][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC2CTRL1: plugin->polyfx_mod_matrix[0][2][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC2CTRL2: plugin->polyfx_mod_matrix[0][2][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC3CTRL0: plugin->polyfx_mod_matrix[0][3][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC3CTRL1: plugin->polyfx_mod_matrix[0][3][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC3CTRL2: plugin->polyfx_mod_matrix[0][3][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC0CTRL0: plugin->polyfx_mod_matrix[1][0][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC0CTRL1: plugin->polyfx_mod_matrix[1][0][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC0CTRL2: plugin->polyfx_mod_matrix[1][0][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC1CTRL0: plugin->polyfx_mod_matrix[1][1][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC1CTRL1: plugin->polyfx_mod_matrix[1][1][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC1CTRL2: plugin->polyfx_mod_matrix[1][1][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC2CTRL0: plugin->polyfx_mod_matrix[1][2][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC2CTRL1: plugin->polyfx_mod_matrix[1][2][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC2CTRL2: plugin->polyfx_mod_matrix[1][2][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC3CTRL0: plugin->polyfx_mod_matrix[1][3][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC3CTRL1: plugin->polyfx_mod_matrix[1][3][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC3CTRL2: plugin->polyfx_mod_matrix[1][3][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC0CTRL0: plugin->polyfx_mod_matrix[2][0][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC0CTRL1: plugin->polyfx_mod_matrix[2][0][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC0CTRL2: plugin->polyfx_mod_matrix[2][0][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC1CTRL0: plugin->polyfx_mod_matrix[2][1][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC1CTRL1: plugin->polyfx_mod_matrix[2][1][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC1CTRL2: plugin->polyfx_mod_matrix[2][1][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC2CTRL0: plugin->polyfx_mod_matrix[2][2][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC2CTRL1: plugin->polyfx_mod_matrix[2][2][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC2CTRL2: plugin->polyfx_mod_matrix[2][2][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC3CTRL0: plugin->polyfx_mod_matrix[2][3][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC3CTRL1: plugin->polyfx_mod_matrix[2][3][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC3CTRL2: plugin->polyfx_mod_matrix[2][3][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC0CTRL0: plugin->polyfx_mod_matrix[3][0][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC0CTRL1: plugin->polyfx_mod_matrix[3][0][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC0CTRL2: plugin->polyfx_mod_matrix[3][0][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC1CTRL0: plugin->polyfx_mod_matrix[3][1][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC1CTRL1: plugin->polyfx_mod_matrix[3][1][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC1CTRL2: plugin->polyfx_mod_matrix[3][1][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC2CTRL0: plugin->polyfx_mod_matrix[3][2][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC2CTRL1: plugin->polyfx_mod_matrix[3][2][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC2CTRL2: plugin->polyfx_mod_matrix[3][2][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC3CTRL0: plugin->polyfx_mod_matrix[3][3][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC3CTRL1: plugin->polyfx_mod_matrix[3][3][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC3CTRL2: plugin->polyfx_mod_matrix[3][3][2] = data; break;

        //keyboard tracking
        case FM1_PFXMATRIX_GRP0DST0SRC4CTRL0: plugin->polyfx_mod_matrix[0][4][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC4CTRL1: plugin->polyfx_mod_matrix[0][4][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC4CTRL2: plugin->polyfx_mod_matrix[0][4][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC4CTRL0: plugin->polyfx_mod_matrix[1][4][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC4CTRL1: plugin->polyfx_mod_matrix[1][4][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC4CTRL2: plugin->polyfx_mod_matrix[1][4][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC4CTRL0: plugin->polyfx_mod_matrix[2][4][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC4CTRL1: plugin->polyfx_mod_matrix[2][4][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC4CTRL2: plugin->polyfx_mod_matrix[2][4][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC4CTRL0: plugin->polyfx_mod_matrix[3][4][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC4CTRL1: plugin->polyfx_mod_matrix[3][4][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC4CTRL2: plugin->polyfx_mod_matrix[3][4][2] = data; break;

        //velocity tracking
        case FM1_PFXMATRIX_GRP0DST0SRC5CTRL0: plugin->polyfx_mod_matrix[0][5][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC5CTRL1: plugin->polyfx_mod_matrix[0][5][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC5CTRL2: plugin->polyfx_mod_matrix[0][5][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC5CTRL0: plugin->polyfx_mod_matrix[1][5][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC5CTRL1: plugin->polyfx_mod_matrix[1][5][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC5CTRL2: plugin->polyfx_mod_matrix[1][5][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC5CTRL0: plugin->polyfx_mod_matrix[2][5][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC5CTRL1: plugin->polyfx_mod_matrix[2][5][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC5CTRL2: plugin->polyfx_mod_matrix[2][5][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC5CTRL0: plugin->polyfx_mod_matrix[3][5][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC5CTRL1: plugin->polyfx_mod_matrix[3][5][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC5CTRL2: plugin->polyfx_mod_matrix[3][5][2] = data; break;


        case FM1_NOISE_TYPE: plugin->noise_type = data; break;
        case FM1_ADSR1_CHECKBOX: plugin->osc[0].adsr_checked = data; break;
        case FM1_ADSR2_CHECKBOX: plugin->osc[1].adsr_checked = data; break;

        case FM1_LFO_AMP: plugin->lfo_amp = data; break;
        case FM1_LFO_PITCH: plugin->lfo_pitch = data; break;

        case FM1_PITCH_ENV_AMT: plugin->pitch_env_amt = data; break;
        case FM1_LFO_AMOUNT: plugin->lfo_amount = data; break;

        case FM1_OSC3_PITCH: plugin->osc[2].pitch = data; break;
        case FM1_OSC3_TUNE: plugin->osc[2].tune = data; break;
        case FM1_OSC3_TYPE: plugin->osc[2].type = data; break;
        case FM1_OSC3_VOLUME: plugin->osc[2].vol = data;  break;

        case FM1_OSC1_FM1: plugin->osc[0].fm[0] = data;  break;
        case FM1_OSC1_FM2: plugin->osc[0].fm[1] = data;  break;
        case FM1_OSC1_FM3: plugin->osc[0].fm[2] = data;  break;

        case FM1_OSC2_FM1: plugin->osc[1].fm[0] = data;  break;
        case FM1_OSC2_FM2: plugin->osc[1].fm[1] = data;  break;
        case FM1_OSC2_FM3: plugin->osc[1].fm[2] = data;  break;

        case FM1_OSC3_FM1: plugin->osc[2].fm[0] = data;  break;
        case FM1_OSC3_FM2: plugin->osc[2].fm[1] = data;  break;
        case FM1_OSC3_FM3: plugin->osc[2].fm[2] = data;  break;

        case FM1_ATTACK3: plugin->osc[2].attack = data; break;
        case FM1_DECAY3: plugin->osc[2].decay = data; break;
        case FM1_SUSTAIN3: plugin->osc[2].sustain = data; break;
        case FM1_RELEASE3: plugin->osc[2].release = data; break;

        case FM1_ADSR3_CHECKBOX: plugin->osc[2].adsr_checked = data; break;

        case FM1_PERC_ENV_PITCH1: plugin->perc_env_pitch1 = data; break;
        case FM1_PERC_ENV_TIME1: plugin->perc_env_time1 = data; break;
        case FM1_PERC_ENV_PITCH2: plugin->perc_env_pitch2 = data; break;
        case FM1_PERC_ENV_TIME2: plugin->perc_env_time2 = data; break;
        case FM1_PERC_ENV_ON: plugin->perc_env_on = data; break;

        case FM1_RAMP_CURVE: plugin->ramp_curve = data; break;

        case FM1_MONO_MODE: plugin->mono_mode = data; break;

        case FM1_OSC1_FM4: plugin->osc[0].fm[3] = data;  break;
        case FM1_OSC2_FM4: plugin->osc[1].fm[3] = data;  break;
        case FM1_OSC3_FM4: plugin->osc[2].fm[3] = data;  break;

        case FM1_OSC4_UNISON_VOICES: plugin->osc[3].uni_voice = data; break;
        case FM1_OSC4_UNISON_SPREAD: plugin->osc[3].uni_spread = data; break;

        case FM1_OSC4_PITCH: plugin->osc[3].pitch = data; break;
        case FM1_OSC4_TUNE: plugin->osc[3].tune = data; break;
        case FM1_OSC4_TYPE: plugin->osc[3].type = data; break;
        case FM1_OSC4_VOLUME: plugin->osc[3].vol = data;  break;

        case FM1_OSC4_FM1: plugin->osc[3].fm[0] = data;  break;
        case FM1_OSC4_FM2: plugin->osc[3].fm[1] = data;  break;
        case FM1_OSC4_FM3: plugin->osc[3].fm[2] = data;  break;
        case FM1_OSC4_FM4: plugin->osc[3].fm[3] = data;  break;

        case FM1_ATTACK4: plugin->osc[3].attack = data; break;
        case FM1_DECAY4: plugin->osc[3].decay = data; break;
        case FM1_SUSTAIN4: plugin->osc[3].sustain = data; break;
        case FM1_RELEASE4: plugin->osc[3].release = data; break;

        case FM1_ADSR4_CHECKBOX: plugin->osc[3].adsr_checked = data; break;

        case FM1_FM_MACRO1: plugin->fm_macro[0] = data; break;
        case FM1_FM_MACRO1_OSC1_FM1: plugin->fm_macro_values[0][0][0] = data; break;
        case FM1_FM_MACRO1_OSC1_FM2: plugin->fm_macro_values[0][0][1] = data; break;
        case FM1_FM_MACRO1_OSC1_FM3: plugin->fm_macro_values[0][0][2] = data; break;
        case FM1_FM_MACRO1_OSC1_FM4: plugin->fm_macro_values[0][0][3] = data; break;
        case FM1_FM_MACRO1_OSC2_FM1: plugin->fm_macro_values[0][1][0] = data; break;
        case FM1_FM_MACRO1_OSC2_FM2: plugin->fm_macro_values[0][1][1] = data; break;
        case FM1_FM_MACRO1_OSC2_FM3: plugin->fm_macro_values[0][1][2] = data; break;
        case FM1_FM_MACRO1_OSC2_FM4: plugin->fm_macro_values[0][1][3] = data; break;
        case FM1_FM_MACRO1_OSC3_FM1: plugin->fm_macro_values[0][2][0] = data; break;
        case FM1_FM_MACRO1_OSC3_FM2: plugin->fm_macro_values[0][2][1] = data; break;
        case FM1_FM_MACRO1_OSC3_FM3: plugin->fm_macro_values[0][2][2] = data; break;
        case FM1_FM_MACRO1_OSC3_FM4: plugin->fm_macro_values[0][2][3] = data; break;
        case FM1_FM_MACRO1_OSC4_FM1: plugin->fm_macro_values[0][3][0] = data; break;
        case FM1_FM_MACRO1_OSC4_FM2: plugin->fm_macro_values[0][3][1] = data; break;
        case FM1_FM_MACRO1_OSC4_FM3: plugin->fm_macro_values[0][3][2] = data; break;
        case FM1_FM_MACRO1_OSC4_FM4: plugin->fm_macro_values[0][3][3] = data; break;

        case FM1_FM_MACRO2: plugin->fm_macro[1] = data; break;
        case FM1_FM_MACRO2_OSC1_FM1: plugin->fm_macro_values[1][0][0] = data; break;
        case FM1_FM_MACRO2_OSC1_FM2: plugin->fm_macro_values[1][0][1] = data; break;
        case FM1_FM_MACRO2_OSC1_FM3: plugin->fm_macro_values[1][0][2] = data; break;
        case FM1_FM_MACRO2_OSC1_FM4: plugin->fm_macro_values[1][0][3] = data; break;
        case FM1_FM_MACRO2_OSC2_FM1: plugin->fm_macro_values[1][1][0] = data; break;
        case FM1_FM_MACRO2_OSC2_FM2: plugin->fm_macro_values[1][1][1] = data; break;
        case FM1_FM_MACRO2_OSC2_FM3: plugin->fm_macro_values[1][1][2] = data; break;
        case FM1_FM_MACRO2_OSC2_FM4: plugin->fm_macro_values[1][1][3] = data; break;
        case FM1_FM_MACRO2_OSC3_FM1: plugin->fm_macro_values[1][2][0] = data; break;
        case FM1_FM_MACRO2_OSC3_FM2: plugin->fm_macro_values[1][2][1] = data; break;
        case FM1_FM_MACRO2_OSC3_FM3: plugin->fm_macro_values[1][2][2] = data; break;
        case FM1_FM_MACRO2_OSC3_FM4: plugin->fm_macro_values[1][2][3] = data; break;
        case FM1_FM_MACRO2_OSC4_FM1: plugin->fm_macro_values[1][3][0] = data; break;
        case FM1_FM_MACRO2_OSC4_FM2: plugin->fm_macro_values[1][3][1] = data; break;
        case FM1_FM_MACRO2_OSC4_FM3: plugin->fm_macro_values[1][3][2] = data; break;
        case FM1_FM_MACRO2_OSC4_FM4: plugin->fm_macro_values[1][3][3] = data; break;

        case FM1_FM_MACRO1_OSC1_VOL: plugin->amp_macro_values[0][0] = data; break;
        case FM1_FM_MACRO1_OSC2_VOL: plugin->amp_macro_values[0][1] = data; break;
        case FM1_FM_MACRO1_OSC3_VOL: plugin->amp_macro_values[0][2] = data; break;
        case FM1_FM_MACRO1_OSC4_VOL: plugin->amp_macro_values[0][3] = data; break;

        case FM1_FM_MACRO2_OSC1_VOL: plugin->amp_macro_values[1][0] = data; break;
        case FM1_FM_MACRO2_OSC2_VOL: plugin->amp_macro_values[1][1] = data; break;
        case FM1_FM_MACRO2_OSC3_VOL: plugin->amp_macro_values[1][2] = data; break;
        case FM1_FM_MACRO2_OSC4_VOL: plugin->amp_macro_values[1][3] = data; break;

        case FM1_LFO_PHASE: plugin->lfo_phase = data; break;
        case FM1_LFO_PITCH_FINE: plugin->lfo_pitch_fine = data; break;
        case FM1_ADSR_PREFX: plugin->adsr_prefx = data; break;

        case FM1_ADSR1_DELAY: plugin->osc[0].adsr_fm_delay = data; break;
        case FM1_ADSR2_DELAY: plugin->osc[1].adsr_fm_delay = data; break;
        case FM1_ADSR3_DELAY: plugin->osc[2].adsr_fm_delay = data; break;
        case FM1_ADSR4_DELAY: plugin->osc[3].adsr_fm_delay = data; break;

        case FM1_ADSR1_HOLD: plugin->osc[0].adsr_fm_hold = data; break;
        case FM1_ADSR2_HOLD: plugin->osc[1].adsr_fm_hold = data; break;
        case FM1_ADSR3_HOLD: plugin->osc[2].adsr_fm_hold = data; break;
        case FM1_ADSR4_HOLD: plugin->osc[3].adsr_fm_hold = data; break;

        case FM1_PFX_ADSR_DELAY: plugin->pfx_delay = data; break;
        case FM1_PFX_ADSR_F_DELAY: plugin->pfx_delay_f = data; break;

        case FM1_PFX_ADSR_HOLD: plugin->pfx_hold = data; break;
        case FM1_PFX_ADSR_F_HOLD: plugin->pfx_hold_f = data; break;
        case FM1_HOLD_MAIN: plugin->hold_main = data; break;

        case FM1_DELAY_NOISE: plugin->noise_delay = data; break;
        case FM1_ATTACK_NOISE: plugin->noise_attack = data; break;
        case FM1_HOLD_NOISE: plugin->noise_hold = data; break;
        case FM1_DECAY_NOISE: plugin->noise_decay = data; break;
        case FM1_SUSTAIN_NOISE: plugin->noise_sustain = data; break;
        case FM1_RELEASE_NOISE: plugin->noise_release = data; break;
        case FM1_ADSR_NOISE_ON: plugin->noise_adsr_on = data; break;

        case FM1_DELAY_LFO: plugin->lfo_delay = data; break;
        case FM1_ATTACK_LFO: plugin->lfo_attack = data; break;
        case FM1_HOLD_LFO: plugin->lfo_hold = data; break;
        case FM1_DECAY_LFO: plugin->lfo_decay = data; break;
        case FM1_SUSTAIN_LFO: plugin->lfo_sustain = data; break;
        case FM1_RELEASE_LFO: plugin->lfo_release = data; break;
        case FM1_ADSR_LFO_ON: plugin->lfo_adsr_on = data; break;

        case FM1_OSC5_TYPE: plugin->osc[4].type = data; break;
        case FM1_OSC5_PITCH: plugin->osc[4].pitch = data; break;
        case FM1_OSC5_TUNE: plugin->osc[4].tune = data; break;
        case FM1_OSC5_VOLUME: plugin->osc[4].vol = data; break;
        case FM1_OSC5_UNISON_VOICES: plugin->osc[4].uni_voice = data; break;
        case FM1_OSC5_UNISON_SPREAD: plugin->osc[4].uni_spread = data; break;
        case FM1_OSC1_FM5: plugin->osc[0].fm[4] = data; break;
        case FM1_OSC2_FM5: plugin->osc[1].fm[4] = data; break;
        case FM1_OSC3_FM5: plugin->osc[2].fm[4] = data; break;
        case FM1_OSC4_FM5: plugin->osc[3].fm[4] = data; break;
        case FM1_OSC5_FM5: plugin->osc[4].fm[4] = data; break;
        case FM1_OSC6_FM5: plugin->osc[5].fm[4] = data; break;
        case FM1_ADSR5_DELAY: plugin->osc[4].adsr_fm_delay = data; break;
        case FM1_ATTACK5 : plugin->osc[4].attack = data; break;
        case FM1_ADSR5_HOLD: plugin->osc[4].adsr_fm_hold = data; break;
        case FM1_DECAY5  : plugin->osc[4].decay = data; break;
        case FM1_SUSTAIN5: plugin->osc[4].sustain = data; break;
        case FM1_RELEASE5: plugin->osc[4].release = data; break;
        case FM1_ADSR5_CHECKBOX: plugin->osc[4].adsr_checked = data; break;

        case FM1_OSC6_TYPE: plugin->osc[5].type = data; break;
        case FM1_OSC6_PITCH: plugin->osc[5].pitch = data; break;
        case FM1_OSC6_TUNE: plugin->osc[5].tune = data; break;
        case FM1_OSC6_VOLUME: plugin->osc[5].vol = data; break;
        case FM1_OSC6_UNISON_VOICES: plugin->osc[5].uni_voice = data; break;
        case FM1_OSC6_UNISON_SPREAD: plugin->osc[5].uni_spread = data; break;
        case FM1_OSC1_FM6: plugin->osc[0].fm[5] = data; break;
        case FM1_OSC2_FM6: plugin->osc[1].fm[5] = data; break;
        case FM1_OSC3_FM6: plugin->osc[2].fm[5] = data; break;
        case FM1_OSC4_FM6: plugin->osc[3].fm[5] = data; break;
        case FM1_OSC5_FM6: plugin->osc[4].fm[5] = data; break;
        case FM1_OSC6_FM6: plugin->osc[5].fm[5] = data; break;
        case FM1_ADSR6_DELAY: plugin->osc[5].adsr_fm_delay = data; break;
        case FM1_ATTACK6: plugin->osc[5].attack = data; break;
        case FM1_ADSR6_HOLD: plugin->osc[5].adsr_fm_hold = data; break;
        case FM1_DECAY6  : plugin->osc[5].decay = data; break;
        case FM1_SUSTAIN6: plugin->osc[5].sustain = data; break;
        case FM1_RELEASE6: plugin->osc[5].release = data; break;
        case FM1_ADSR6_CHECKBOX: plugin->osc[5].adsr_checked = data; break;

        case FM1_FM_MACRO1_OSC1_FM5: plugin->fm_macro_values[0][0][4] = data; break;
        case FM1_FM_MACRO1_OSC2_FM5: plugin->fm_macro_values[0][1][4] = data; break;
        case FM1_FM_MACRO1_OSC3_FM5: plugin->fm_macro_values[0][2][4] = data; break;
        case FM1_FM_MACRO1_OSC4_FM5: plugin->fm_macro_values[0][3][4] = data; break;
        case FM1_FM_MACRO1_OSC5_FM5: plugin->fm_macro_values[0][4][4] = data; break;
        case FM1_FM_MACRO1_OSC6_FM5: plugin->fm_macro_values[0][5][4] = data; break;

        case FM1_FM_MACRO1_OSC1_FM6: plugin->fm_macro_values[0][0][5] = data; break;
        case FM1_FM_MACRO1_OSC2_FM6: plugin->fm_macro_values[0][1][5] = data; break;
        case FM1_FM_MACRO1_OSC3_FM6: plugin->fm_macro_values[0][2][5] = data; break;
        case FM1_FM_MACRO1_OSC4_FM6: plugin->fm_macro_values[0][3][5] = data; break;
        case FM1_FM_MACRO1_OSC5_FM6: plugin->fm_macro_values[0][4][5] = data; break;
        case FM1_FM_MACRO1_OSC6_FM6: plugin->fm_macro_values[0][5][5] = data; break;

        case FM1_FM_MACRO1_OSC5_FM1: plugin->fm_macro_values[0][4][0] = data; break;
        case FM1_FM_MACRO1_OSC5_FM2: plugin->fm_macro_values[0][4][1] = data; break;
        case FM1_FM_MACRO1_OSC5_FM3: plugin->fm_macro_values[0][4][2] = data; break;
        case FM1_FM_MACRO1_OSC5_FM4: plugin->fm_macro_values[0][4][3] = data; break;

        case FM1_FM_MACRO1_OSC6_FM1: plugin->fm_macro_values[0][5][0] = data; break;
        case FM1_FM_MACRO1_OSC6_FM2: plugin->fm_macro_values[0][5][1] = data; break;
        case FM1_FM_MACRO1_OSC6_FM3: plugin->fm_macro_values[0][5][2] = data; break;
        case FM1_FM_MACRO1_OSC6_FM4: plugin->fm_macro_values[0][5][3] = data; break;

        case FM1_FM_MACRO1_OSC5_VOL: plugin->amp_macro_values[0][4] = data; break;
        case FM1_FM_MACRO1_OSC6_VOL: plugin->amp_macro_values[0][5] = data; break;

        case FM1_FM_MACRO2_OSC1_FM5: plugin->fm_macro_values[1][0][4] = data; break;
        case FM1_FM_MACRO2_OSC2_FM5: plugin->fm_macro_values[1][1][4] = data; break;
        case FM1_FM_MACRO2_OSC3_FM5: plugin->fm_macro_values[1][2][4] = data; break;
        case FM1_FM_MACRO2_OSC4_FM5: plugin->fm_macro_values[1][3][4] = data; break;
        case FM1_FM_MACRO2_OSC5_FM5: plugin->fm_macro_values[1][4][4] = data; break;
        case FM1_FM_MACRO2_OSC6_FM5: plugin->fm_macro_values[1][5][4] = data; break;

        case FM1_FM_MACRO2_OSC1_FM6: plugin->fm_macro_values[1][0][5] = data; break;
        case FM1_FM_MACRO2_OSC2_FM6: plugin->fm_macro_values[1][1][5] = data; break;
        case FM1_FM_MACRO2_OSC3_FM6: plugin->fm_macro_values[1][2][5] = data; break;
        case FM1_FM_MACRO2_OSC4_FM6: plugin->fm_macro_values[1][3][5] = data; break;
        case FM1_FM_MACRO2_OSC5_FM6: plugin->fm_macro_values[1][4][5] = data; break;
        case FM1_FM_MACRO2_OSC6_FM6: plugin->fm_macro_values[1][5][5] = data; break;

        case FM1_FM_MACRO2_OSC5_FM1: plugin->fm_macro_values[1][4][0] = data; break;
        case FM1_FM_MACRO2_OSC5_FM2: plugin->fm_macro_values[1][4][1] = data; break;
        case FM1_FM_MACRO2_OSC5_FM3: plugin->fm_macro_values[1][4][2] = data; break;
        case FM1_FM_MACRO2_OSC5_FM4: plugin->fm_macro_values[1][4][3] = data; break;

        case FM1_FM_MACRO2_OSC6_FM1: plugin->fm_macro_values[1][5][0] = data; break;
        case FM1_FM_MACRO2_OSC6_FM2: plugin->fm_macro_values[1][5][1] = data; break;
        case FM1_FM_MACRO2_OSC6_FM3: plugin->fm_macro_values[1][5][2] = data; break;
        case FM1_FM_MACRO2_OSC6_FM4: plugin->fm_macro_values[1][5][3] = data; break;

        case FM1_FM_MACRO2_OSC5_VOL: plugin->amp_macro_values[1][4] = data; break;
        case FM1_FM_MACRO2_OSC6_VOL: plugin->amp_macro_values[1][5] = data; break;

        case FM1_OSC5_FM1: plugin->osc[4].fm[0] = data; break;
        case FM1_OSC5_FM2: plugin->osc[4].fm[1] = data; break;
        case FM1_OSC5_FM3: plugin->osc[4].fm[2] = data; break;
        case FM1_OSC5_FM4: plugin->osc[4].fm[3] = data; break;

        case FM1_OSC6_FM1: plugin->osc[5].fm[0] = data; break;
        case FM1_OSC6_FM2: plugin->osc[5].fm[1] = data; break;
        case FM1_OSC6_FM3: plugin->osc[5].fm[2] = data; break;
        case FM1_OSC6_FM4: plugin->osc[5].fm[3] = data; break;

        case FM1_NOISE_PREFX: plugin->noise_prefx = data; break;

        //fm macro 1
        case FM1_PFXMATRIX_GRP0DST0SRC6CTRL0: plugin->polyfx_mod_matrix[0][6][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC6CTRL1: plugin->polyfx_mod_matrix[0][6][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC6CTRL2: plugin->polyfx_mod_matrix[0][6][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC6CTRL0: plugin->polyfx_mod_matrix[1][6][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC6CTRL1: plugin->polyfx_mod_matrix[1][6][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC6CTRL2: plugin->polyfx_mod_matrix[1][6][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC6CTRL0: plugin->polyfx_mod_matrix[2][6][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC6CTRL1: plugin->polyfx_mod_matrix[2][6][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC6CTRL2: plugin->polyfx_mod_matrix[2][6][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC6CTRL0: plugin->polyfx_mod_matrix[3][6][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC6CTRL1: plugin->polyfx_mod_matrix[3][6][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC6CTRL2: plugin->polyfx_mod_matrix[3][6][2] = data; break;
        //fm macro 2
        case FM1_PFXMATRIX_GRP0DST0SRC7CTRL0: plugin->polyfx_mod_matrix[0][7][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC7CTRL1: plugin->polyfx_mod_matrix[0][7][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST0SRC7CTRL2: plugin->polyfx_mod_matrix[0][7][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC7CTRL0: plugin->polyfx_mod_matrix[1][7][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC7CTRL1: plugin->polyfx_mod_matrix[1][7][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST1SRC7CTRL2: plugin->polyfx_mod_matrix[1][7][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC7CTRL0: plugin->polyfx_mod_matrix[2][7][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC7CTRL1: plugin->polyfx_mod_matrix[2][7][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST2SRC7CTRL2: plugin->polyfx_mod_matrix[2][7][2] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC7CTRL0: plugin->polyfx_mod_matrix[3][7][0] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC7CTRL1: plugin->polyfx_mod_matrix[3][7][1] = data; break;
        case FM1_PFXMATRIX_GRP0DST3SRC7CTRL2: plugin->polyfx_mod_matrix[3][7][2] = data; break;

        case FM1_MIN_NOTE: plugin->min_note = data; break;
        case FM1_MAX_NOTE: plugin->max_note = data; break;
        case FM1_MAIN_PITCH: plugin->main_pitch = data; break;

        case FM1_ADSR_LIN_MAIN: plugin->adsr_lin_main = data; break;
        case FM1_MAIN_PAN: plugin->pan = data; break;
        case FM1_OSC1_PAN: plugin->osc[0].pan = data; break;
        case FM1_OSC2_PAN: plugin->osc[1].pan = data; break;
        case FM1_OSC3_PAN: plugin->osc[2].pan = data; break;
        case FM1_OSC4_PAN: plugin->osc[3].pan = data; break;
        case FM1_OSC5_PAN: plugin->osc[4].pan = data; break;
        case FM1_OSC6_PAN: plugin->osc[5].pan = data; break;
    }
}

PluginHandle g_fm1_instantiate(
    PluginDescriptor * descriptor,
    int s_rate,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
){
    t_fm1 *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_fm1));

    plugin_data->fs = s_rate;
    plugin_data->descriptor = descriptor;

    v_fm1_mono_init(
        &plugin_data->mono_modules,
        plugin_data->fs
    );

    int i;

    g_voc_voices_init(
        &plugin_data->voices,
        FM1_POLYPHONY,
        FM1_POLYPHONY_THRESH
    );

    for(i = 0; i < FM1_POLYPHONY; ++i){
        g_fm1_poly_init(
            &plugin_data->data[i],
            plugin_data->fs,
            &plugin_data->mono_modules,
            i
        );
    }
    plugin_data->sampleNo = 0;

    //plugin_data->pitch = 1.0f;
    plugin_data->sv_pitch_bend_value = 0.0f;
    plugin_data->sv_last_note = -1.0f;  //For glide

    g_get_port_table((void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PluginHandle)plugin_data;
}

void v_fm1_load(
    PluginHandle instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR * a_file_path
){
    t_fm1 *plugin_data = (t_fm1*)instance;
    generic_file_loader(
        instance,
        Descriptor,
        a_file_path,
        plugin_data->port_table,
        &plugin_data->cc_map
    );
}

void v_fm1_set_port_value(
    PluginHandle Instance,
    int a_port,
    SGFLT a_value
){
    t_fm1 *plugin_data = (t_fm1*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

void v_fm1_process_midi_event(
    t_fm1 *plugin_data,
    t_seq_event * a_event,
    int f_poly_mode,
    int midi_channel
){
    int is_in_channel = midi_event_is_in_channel(
        a_event->channel,
        midi_channel
    );
    if(!is_in_channel){
        return;
    }
    int f_min_note = (int)*plugin_data->min_note;
    int f_max_note = (int)*plugin_data->max_note;

    if (a_event->type == EVENT_NOTEON){
        if (a_event->velocity > 0){
            if(
                a_event->note > f_max_note
                ||
                a_event->note < f_min_note
            ){
                return;
            }

            int f_voice = i_pick_voice(
                &plugin_data->voices,
                a_event->note,
                plugin_data->sampleNo,
                a_event->tick
            );

            t_fm1_osc* f_pfx_osc = NULL;
            t_fm1_poly_voice* f_fm1_voice = &plugin_data->data[f_voice];
            // Per-note pan
            v_pn2_set_normalize(
                &f_fm1_voice->panner,
                a_event->pan,
                -3.0
            );

            resampler_linear_reset(&f_fm1_voice->resampler);
            int f_adsr_main_lin = (int)(*plugin_data->adsr_lin_main);
            f_fm1_voice->adsr_run_func = FP_ADSR_RUN[f_adsr_main_lin];

            SGFLT f_main_pitch = (*plugin_data->main_pitch);

            f_fm1_voice->note_f = (SGFLT)a_event->note + f_main_pitch +
                a_event->pitch_fine;
            f_fm1_voice->note = a_event->note + (int)(f_main_pitch);

            f_fm1_voice->amp = f_db_to_linear_fast(
                ((a_event->velocity * 0.094488) - 12)
            ); //-12db to 0db

            f_fm1_voice->main_vol_lin = f_db_to_linear_fast(
                *(plugin_data->main_vol)
            );

            f_fm1_voice->keyboard_track = f_fm1_voice->note_f * 0.007874016f;

            f_fm1_voice->velocity_track =
                ((SGFLT)(a_event->velocity)) * 0.007874016f;

            f_fm1_voice->target_pitch = f_fm1_voice->note_f;

            if(plugin_data->sv_last_note < 0.0f){
                f_fm1_voice->last_pitch = f_fm1_voice->note_f;
            } else {
                f_fm1_voice->last_pitch = plugin_data->sv_last_note;
            }

            v_rmp_retrigger_glide_t(
                &f_fm1_voice->glide_env,
                *(plugin_data->main_glide) * 0.01f,
                f_fm1_voice->last_pitch,
                f_fm1_voice->target_pitch
            );

            int f_i;

            SGFLT f_db;

            for(f_i = 0; f_i < FM1_OSC_COUNT; ++f_i){
                int f_osc_type = (int)(*plugin_data->osc[f_i].type) - 1;
                f_pfx_osc = &f_fm1_voice->osc[f_i];

                if(f_osc_type >= 0){
                    f_pfx_osc->osc_on = 1;

                    if(f_poly_mode == POLY_MODE_RETRIG){
                        v_osc_wav_note_on_sync_phases(
                            &f_pfx_osc->osc_wavtable
                        );
                    }
                    v_osc_wav_set_waveform(
                        &f_pfx_osc->osc_wavtable,
                        plugin_data->mono_modules.wavetables->tables[
                            f_osc_type
                        ]->wavetable,
                        plugin_data->mono_modules.wavetables->tables[
                            f_osc_type
                        ]->length
                    );
                    v_osc_wav_set_uni_voice_count(
                        &f_pfx_osc->osc_wavtable,
                        *plugin_data->osc[f_i].uni_voice
                    );
                } else {
                    f_pfx_osc->osc_on = 0;
                    continue;
                }

                f_pfx_osc->osc_uni_spread =
                    (*plugin_data->osc[f_i].uni_spread) * 0.01f;

                v_pn2_set_normalize(
                    &f_fm1_voice->osc[f_i].panner,
                    *plugin_data->osc[f_i].pan * 0.01,
                    -3.0
                );

                int f_i2;
                for(f_i2 = 0; f_i2 < FM1_OSC_COUNT; ++f_i2){
                    f_pfx_osc->osc_fm[f_i2] =
                        (*plugin_data->osc[f_i].fm[f_i2]) * 0.005;
                    // TODO: FM2
                    // Make this control exponential, will break backwards
                    // compatibility of old projects and presets
                    // f_pfx_osc->osc_fm[f_i2] =
                    //     (*plugin_data->osc_fm[f_i][f_i2]) * 0.0075;
                    // f_pfx_osc->osc_fm[f_i2] *= f_pfx_osc->osc_fm[f_i2];
                }

                f_db = (*plugin_data->osc[f_i].vol);

                v_adsr_retrigger(&f_pfx_osc->adsr_amp_osc);

                f_pfx_osc->osc_linamp = f_db_to_linear_fast(f_db);

                if(f_db > -29.2f){
                    f_pfx_osc->osc_audible = 1;
                } else {
                    f_pfx_osc->osc_audible = 0;
                }

                f_pfx_osc->adsr_amp_on =
                    (int)(*plugin_data->osc[f_i].adsr_checked);

                if(f_pfx_osc->adsr_amp_on){
                    SGFLT f_attack1 = *(plugin_data->osc[f_i].attack) * .01f;
                    f_attack1 = (f_attack1) * (f_attack1);
                    SGFLT f_decay1 = *(plugin_data->osc[f_i].decay) * .01f;
                    f_decay1 = (f_decay1) * (f_decay1);
                    SGFLT f_release1 = *(plugin_data->osc[f_i].release) * .01f;
                    f_release1 = (f_release1) * (f_release1);

                    v_adsr_set_adsr_db(
                        &f_pfx_osc->adsr_amp_osc,
                        f_attack1,
                        f_decay1,
                        *(plugin_data->osc[f_i].sustain),
                        f_release1
                    );

                    v_adsr_set_delay_time(
                        &f_pfx_osc->adsr_amp_osc,
                        (*plugin_data->osc[f_i].adsr_fm_delay) * 0.01f
                    );
                    v_adsr_set_hold_time(
                        &f_pfx_osc->adsr_amp_osc,
                        (*plugin_data->osc[f_i].adsr_fm_hold) * 0.01f
                    );
                }

                for(f_i2 = 0; f_i2 < 2; ++f_i2){
                    f_pfx_osc->osc_macro_amp[f_i2] =
                        (*plugin_data->amp_macro_values[f_i2][f_i]);
                }
            }

            f_fm1_voice->noise_linamp = f_db_to_linear_fast(
                *(plugin_data->noise_amp)
            );

            f_fm1_voice->adsr_noise_on = (int)*plugin_data->noise_adsr_on;

            f_fm1_voice->noise_prefx = (int)*plugin_data->noise_prefx;

            if(f_fm1_voice->adsr_noise_on){
                v_adsr_retrigger(&f_fm1_voice->adsr_noise);
                SGFLT f_attack = *(plugin_data->noise_attack) * .01f;
                f_attack = (f_attack) * (f_attack);
                SGFLT f_decay = *(plugin_data->noise_decay) * .01f;
                f_decay = (f_decay) * (f_decay);
                SGFLT f_sustain = (*plugin_data->noise_sustain);
                SGFLT f_release = *(plugin_data->noise_release) * .01f;
                f_release = (f_release) * (f_release);
                v_adsr_set_adsr_db(
                    &f_fm1_voice->adsr_noise,
                    f_attack,
                    f_decay,
                    f_sustain,
                    f_release
                );
                v_adsr_set_delay_time(
                    &f_fm1_voice->adsr_noise,
                    (*plugin_data->noise_delay) * 0.01f
                );
                v_adsr_set_hold_time(
                    &f_fm1_voice->adsr_noise,
                    (*plugin_data->noise_hold) * 0.01f
                );
            }

            f_fm1_voice->adsr_lfo_on = (int)*plugin_data->lfo_adsr_on;

            if(f_fm1_voice->adsr_lfo_on){
                v_adsr_retrigger(&f_fm1_voice->adsr_lfo);
                SGFLT f_attack = *(plugin_data->lfo_attack) * .01f;
                f_attack = (f_attack) * (f_attack);
                SGFLT f_decay = *(plugin_data->lfo_decay) * .01f;
                f_decay = (f_decay) * (f_decay);
                SGFLT f_sustain = (*plugin_data->lfo_sustain) * 0.01f;
                SGFLT f_release = *(plugin_data->lfo_release) * .01f;
                f_release = (f_release) * (f_release);
                v_adsr_set_adsr(
                    &f_fm1_voice->adsr_lfo,
                    f_attack,
                    f_decay,
                    f_sustain,
                    f_release
                );
                v_adsr_set_delay_time(
                    &f_fm1_voice->adsr_lfo,
                    (*plugin_data->lfo_delay) * 0.01f
                );
                v_adsr_set_hold_time(
                    &f_fm1_voice->adsr_lfo,
                    (*plugin_data->lfo_hold) * 0.01f
                );
            }

            v_adsr_retrigger(&f_fm1_voice->adsr_main);

            SGFLT f_attack = set_pmn_adsr(
                (*plugin_data->attack_main) * .01f,
                a_event->attack,
                (*plugin_data->attack_main_start) * .01f,
                (*plugin_data->attack_main_end) * .01f
            );
            f_attack = (f_attack) * (f_attack);

            SGFLT f_decay = set_pmn_adsr(
                *(plugin_data->decay_main) * .01f,
                a_event->decay,
                *(plugin_data->decay_main_start) * .01f,
                *(plugin_data->decay_main_end) * .01f
            );
            f_decay = (f_decay) * (f_decay);

            SGFLT sustain = set_pmn_adsr(
                (*plugin_data->sustain_main),
                a_event->sustain,
                (*plugin_data->sustain_main_start),
                (*plugin_data->sustain_main_end)
            );

            SGFLT f_release = set_pmn_adsr(
                (*plugin_data->release_main) * .01f,
                a_event->release,
                (*plugin_data->release_main_start) * .01f,
                (*plugin_data->release_main_end) * .01f
            );
            f_release = (f_release) * (f_release);

            FP_ADSR_SET[f_adsr_main_lin](
                &f_fm1_voice->adsr_main,
                f_attack,
                f_decay,
                sustain,
                f_release
            );

            v_adsr_set_hold_time(
                &f_fm1_voice->adsr_main,
                (*plugin_data->hold_main) * 0.01f
            );

            f_fm1_voice->noise_amp = f_db_to_linear(*(plugin_data->noise_amp));

            /*Set the last_note property, so the next note can glide from
             * it if glide is turned on*/
            plugin_data->sv_last_note = f_fm1_voice->note_f;

            int i_dst, i_src, i_ctrl;

            f_fm1_voice->active_polyfx_count = 0;
            //Determine which PolyFX have been enabled
            for(i_dst = 0; i_dst < FM1_MODULAR_POLYFX_COUNT; ++i_dst){
                int f_pfx_combobox_index =
                    (int)(*(plugin_data->fx_combobox[(i_dst)]));
                f_fm1_voice->effects[i_dst].fx_func_ptr =
                    g_mf3_get_function_pointer(f_pfx_combobox_index);

                if(f_pfx_combobox_index != 0){
                    f_fm1_voice->active_polyfx[
                        f_fm1_voice->active_polyfx_count] = i_dst;
                    ++f_fm1_voice->active_polyfx_count;
                }
            }

            int f_dst;

            for(i_dst = 0; i_dst < f_fm1_voice->active_polyfx_count; ++i_dst){
                f_dst = f_fm1_voice->active_polyfx[i_dst];
                f_fm1_voice->polyfx_mod_counts[f_dst] = 0;

                for(i_src = 0; i_src < FM1_MODULATOR_COUNT; ++i_src){
                    for(
                        i_ctrl = 0;
                        i_ctrl < FM1_CONTROLS_PER_MOD_EFFECT;
                        ++i_ctrl
                    ){
                        if(
                            (*plugin_data->polyfx_mod_matrix[
                                f_fm1_voice->active_polyfx[i_dst]
                            ][i_src][i_ctrl]) != 0
                        ){
                            f_fm1_voice->polyfx_mod_ctrl_indexes[f_dst][
                                f_fm1_voice->polyfx_mod_counts[f_dst]] =
                                    i_ctrl;
                            f_fm1_voice->polyfx_mod_src_index[f_dst][
                                f_fm1_voice->polyfx_mod_counts[f_dst]] = i_src;
                            f_fm1_voice->polyfx_mod_matrix_values[f_dst][
                                f_fm1_voice->polyfx_mod_counts[f_dst]] =
                                    (*plugin_data->polyfx_mod_matrix[
                                        f_dst][i_src][i_ctrl]) * .01;
                            ++f_fm1_voice->polyfx_mod_counts[f_dst];
                        }
                    }
                }
            }

            //Get the noise function pointer
            f_fm1_voice->noise_func_ptr = fp_noise_stereo_get(
                (int)(*(plugin_data->noise_type))
            );

            v_adsr_retrigger(&f_fm1_voice->adsr_amp);
            v_adsr_retrigger(&f_fm1_voice->adsr_filter);
            v_lfs_sync(
                &f_fm1_voice->lfo1,
                *plugin_data->lfo_phase * 0.01f,
                *plugin_data->lfo_type
            );

            SGFLT f_attack_a = (*(plugin_data->pfx_attack) * .01);
            f_attack_a *= f_attack_a;
            SGFLT f_decay_a = (*(plugin_data->pfx_decay) * .01);
            f_decay_a *= f_decay_a;
            SGFLT f_release_a = (*(plugin_data->pfx_release) * .01);
            f_release_a *= f_release_a;

            v_adsr_set_adsr_db(
                &f_fm1_voice->adsr_amp,
                f_attack_a,
                f_decay_a,
                *(plugin_data->pfx_sustain),
                f_release_a
            );

            v_adsr_set_delay_time(
                &f_fm1_voice->adsr_amp,
                (*(plugin_data->pfx_delay) * .01)
            );
            v_adsr_set_hold_time(
                &f_fm1_voice->adsr_amp,
                (*(plugin_data->pfx_hold) * .01)
            );

            SGFLT f_attack_f = (*(plugin_data->pfx_attack_f) * .01);
            f_attack_f *= f_attack_f;
            SGFLT f_decay_f = (*(plugin_data->pfx_decay_f) * .01);
            f_decay_f *= f_decay_f;
            SGFLT f_release_f = (*(plugin_data->pfx_release_f) * .01);
            f_release_f *= f_release_f;

            v_adsr_set_adsr(
                &f_fm1_voice->adsr_filter,
                f_attack_f,
                f_decay_f,
                *(plugin_data->pfx_sustain_f) * .01,
                f_release_f
            );

            v_adsr_set_delay_time(
                &f_fm1_voice->adsr_filter,
                (*(plugin_data->pfx_delay_f) * .01)
            );
            v_adsr_set_hold_time(
                &f_fm1_voice->adsr_filter,
                (*(plugin_data->pfx_hold_f) * .01)
            );

            /*Retrigger the pitch envelope*/
            v_rmp_retrigger_curve(
                &f_fm1_voice->ramp_env,
                (*(plugin_data->pitch_env_time) * .01),
                1.0f,
                (*plugin_data->ramp_curve) * 0.01f
            );

            f_fm1_voice->noise_amp = f_db_to_linear(*(plugin_data->noise_amp));

            f_fm1_voice->adsr_prefx = (int)*plugin_data->adsr_prefx;

            f_fm1_voice->perc_env_on = (int)(*plugin_data->perc_env_on);

            if(f_fm1_voice->perc_env_on){
                v_pnv_set(
                    &f_fm1_voice->perc_env,
                    (*plugin_data->perc_env_time1) * 0.001f,
                    (*plugin_data->perc_env_pitch1),
                    (*plugin_data->perc_env_time2) * 0.001f,
                    (*plugin_data->perc_env_pitch2),
                    f_fm1_voice->note_f
                );
            }
        }
        /*0 velocity, the same as note-off*/
        else
        {
            v_voc_note_off(
                &plugin_data->voices,
                a_event->note,
                (plugin_data->sampleNo),
                (a_event->tick)
            );
        }
    } else if (a_event->type == EVENT_NOTEOFF){
        v_voc_note_off(
            &plugin_data->voices,
            a_event->note,
            (plugin_data->sampleNo),
            (a_event->tick)
        );
    } else if (a_event->type == EVENT_CONTROLLER){
        sg_assert(
            a_event->param >= 1 && a_event->param < 128,
            "v_fm1_process_midi_event: param %i out of range 1 to 128",
            a_event->param
        );

        v_plugin_event_queue_add(
            &plugin_data->midi_queue,
            EVENT_CONTROLLER,
            a_event->tick,
            a_event->value,
            a_event->param
        );
    } else if (a_event->type == EVENT_PITCHBEND){
        v_plugin_event_queue_add(
            &plugin_data->midi_queue,
            EVENT_PITCHBEND,
            a_event->tick,
            a_event->value * 0.00012207f,
            0
        );
    }
}

void v_run_fm1(
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
    t_fm1 *plugin_data = (t_fm1*) instance;
    t_fm1_poly_voice* pvoice;
    struct SamplePair sample;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    v_plugin_event_queue_reset(&plugin_data->midi_queue);

    int midi_event_pos = 0;
    int f_poly_mode = (int)(*plugin_data->mono_mode);

    if(
        unlikely(
            f_poly_mode == POLY_MODE_MONO
            &&
            plugin_data->voices.poly_mode != POLY_MODE_MONO
        )
    ){
        fm1Panic(instance);  //avoid hung notes
    }

    plugin_data->voices.poly_mode = f_poly_mode;

    int f_i;

    for(f_i = 0; f_i < event_count; ++f_i){
        v_fm1_process_midi_event(
            plugin_data,
            events[f_i],
            f_poly_mode,
            midi_channel
        );
    }

    f_i = 0;

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

    int i_iterator;
    t_plugin_event_queue_item * f_midi_item;

    for(i_iterator = 0; i_iterator < sample_count; ++i_iterator){
        while(1){
            f_midi_item = v_plugin_event_queue_iter(
                &plugin_data->midi_queue,
                i_iterator
            );
            if(!f_midi_item){
                break;
            }

            if(f_midi_item->type == EVENT_PITCHBEND){
                plugin_data->sv_pitch_bend_value = f_midi_item->value;
            } else if(f_midi_item->type == EVENT_CONTROLLER){
                v_cc_map_translate(
                    &plugin_data->cc_map,
                    plugin_data->descriptor,
                    plugin_data->port_table,
                    f_midi_item->port,
                    f_midi_item->value
                );
            }

            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue,
            i_iterator,
            plugin_data->port_table
        );

        if(plugin_data->mono_modules.reset_wavetables){
            int f_voice = 0;
            int f_osc_type[FM1_OSC_COUNT];
            int f_i = 0;

            for(f_i = 0; f_i < FM1_OSC_COUNT; ++f_i){
                f_osc_type[f_i] = (int)(*plugin_data->osc[f_i].type) - 1;
            }

            for(f_voice = 0; f_voice < FM1_POLYPHONY; ++f_voice){
                pvoice = &plugin_data->data[f_voice];

                for(f_i = 0; f_i < FM1_OSC_COUNT; ++f_i){
                    if(f_osc_type[f_i] >= 0){
                        v_osc_wav_set_waveform(
                            &pvoice->osc[f_i].osc_wavtable,
                            plugin_data->mono_modules.wavetables->tables[
                                f_osc_type[f_i]
                            ]->wavetable,
                            plugin_data->mono_modules.wavetables->tables[
                                f_osc_type[f_i]
                            ]->length
                        );
                    }
                }
            }

            plugin_data->mono_modules.reset_wavetables = 0;
        }

        v_sml_run(
            &plugin_data->mono_modules.pitchbend_smoother,
            (plugin_data->sv_pitch_bend_value)
        );

        v_sml_run(
            &plugin_data->mono_modules.fm_macro_smoother[0],
            (*plugin_data->fm_macro[0] * 0.01f)
        );

        v_sml_run(
            &plugin_data->mono_modules.fm_macro_smoother[1],
            (*plugin_data->fm_macro[1] * 0.01f)
        );

        sample.left = 0.0;
        sample.right = 0.0;
        for(f_i = 0; f_i < FM1_POLYPHONY; ++f_i){
            pvoice = &plugin_data->data[f_i];
            if(pvoice->adsr_main.stage != ADSR_STAGE_OFF){
                v_run_fm1_voice(
                    plugin_data,
                    &plugin_data->voices.voices[f_i],
                    pvoice,
                    &sample,
                    f_i
                );
            } else {
                plugin_data->voices.voices[f_i].n_state = note_state_off;
            }
        }

        v_svf2_run_4_pole_lp(
            &plugin_data->mono_modules.aa_filter,
            sample.left,
            sample.right
        );
        v_sml_run(
            &plugin_data->mono_modules.pan_smoother,
            (*plugin_data->pan * 0.01f)
        );

        v_pn2_set(
            &plugin_data->mono_modules.panner,
            plugin_data->mono_modules.pan_smoother.last_value,
            -3.0
        );
        // Multiplying by 2.0 fixes some unexplained volume bug switching to
        // the new plugin API.  After a week of reviewing a clean and simple
        // patch to this file and not seeing any reason for this, just
        // kludging the volume here instead
        sample.left = input_buffer[i_iterator].left + (
            plugin_data->mono_modules.aa_filter.output0 * 2.0 *
            plugin_data->mono_modules.panner.gainL
        );
        sample.right = input_buffer[i_iterator].right + (
            plugin_data->mono_modules.aa_filter.output1 * 2.0 *
            plugin_data->mono_modules.panner.gainR
        );

        _plugin_mix(
            run_mode,
            i_iterator,
            output_buffer,
            sample.left,
            sample.right
        );

        ++plugin_data->sampleNo;
    }
}

void v_run_fm1_voice(
    t_fm1* plugin_data,
    t_voc_single_voice* a_poly_voice,
    t_fm1_poly_voice* a_voice,
    struct SamplePair* out,
    int a_voice_num
){
    if(plugin_data->sampleNo < a_poly_voice->on){
        return;
    }

    if(
        plugin_data->sampleNo == a_poly_voice->off
        &&
        a_voice->adsr_main.stage < ADSR_STAGE_RELEASE
    ){
        if(a_poly_voice->n_state == note_state_killed){
            v_fm1_poly_note_off(a_voice, 1);
        } else {
            v_fm1_poly_note_off(a_voice, 0);
        }
    }

    a_voice->adsr_run_func(&a_voice->adsr_main);

    f_rmp_run_ramp(&a_voice->glide_env);

    v_adsr_run_db(&a_voice->adsr_amp);

    v_adsr_run(&a_voice->adsr_filter);

    f_rmp_run_ramp_curve(&a_voice->ramp_env);

    //Set and run the LFO
    v_lfs_set(&a_voice->lfo1, (*(plugin_data->lfo_freq)) * .01);
    v_lfs_run(&a_voice->lfo1);

    a_voice->lfo_amount_output =
        (a_voice->lfo1.output) * ((*plugin_data->lfo_amount) * 0.01f);

    if(a_voice->adsr_lfo_on){
        v_adsr_run(&a_voice->adsr_lfo);
        a_voice->lfo_amount_output *= a_voice->adsr_lfo.output;
    }

    a_voice->lfo_amp_output = f_db_to_linear_fast(
        (
            (*plugin_data->lfo_amp) * a_voice->lfo_amount_output
        ) - (
            f_sg_abs((*plugin_data->lfo_amp)) * 0.5
        )
    );

    a_voice->lfo_pitch_output =
        (*plugin_data->lfo_pitch + (*plugin_data->lfo_pitch_fine * 0.01f))
        * (a_voice->lfo_amount_output);

    if(a_voice->perc_env_on){
        a_voice->base_pitch = f_pnv_run(&a_voice->perc_env);
    } else {
        a_voice->base_pitch =
            (a_voice->glide_env.output_multiplied) +
            ((a_voice->ramp_env.output_multiplied) *
            (*plugin_data->pitch_env_amt))
            + (plugin_data->mono_modules.pitchbend_smoother.last_value  *
            (*(plugin_data->main_pb_amt))) + (a_voice->last_pitch) +
            (a_voice->lfo_pitch_output);
    }

    struct FM1OscArg osc_arg = (struct FM1OscArg){
        .plugin_data = plugin_data,
        .a_voice = a_voice,
    };

    a_voice->current_sample = resampler_linear_run(
        &a_voice->resampler,
        &osc_arg
    );

    struct SamplePair noise_sample = a_voice->noise_func_ptr(
        a_voice->white_noise
    );

    if(a_voice->noise_prefx){
        if(a_voice->adsr_noise_on){
            v_adsr_run(&a_voice->adsr_noise);
            a_voice->current_sample.left += noise_sample.left
                * a_voice->noise_linamp * a_voice->adsr_noise.output;
            a_voice->current_sample.right += noise_sample.right
                * a_voice->noise_linamp * a_voice->adsr_noise.output;
        } else {
            a_voice->current_sample.left +=
                noise_sample.left * a_voice->noise_linamp;
            a_voice->current_sample.right +=
                noise_sample.right * a_voice->noise_linamp;
        }
    }

    if(a_voice->adsr_prefx){
        a_voice->current_sample.left *= a_voice->adsr_main.output;
        a_voice->current_sample.right *= a_voice->adsr_main.output;
    }

    a_voice->current_sample.left *= a_voice->amp;
    a_voice->current_sample.right *= a_voice->amp;

    a_voice->multifx_current_sample[0] = a_voice->current_sample.left;
    a_voice->multifx_current_sample[1] = a_voice->current_sample.right;

    t_fm1_pfx_group * f_pfx_group;
    int i_dst, f_dst;
    //Modular PolyFX, processed from the index created during note_on
    for(i_dst = 0; (i_dst) < (a_voice->active_polyfx_count); ++i_dst){
        f_dst = a_voice->active_polyfx[(i_dst)];
        f_pfx_group = &a_voice->effects[f_dst];

        v_mf3_set(
            &f_pfx_group->multieffect,
            *(plugin_data->pfx_mod_knob[f_dst][0]),
            *(plugin_data->pfx_mod_knob[f_dst][1]),
            *(plugin_data->pfx_mod_knob[f_dst][2])
        );

        int f_mod_test;

        for(
            f_mod_test = 0;
            f_mod_test < (a_voice->polyfx_mod_counts[f_dst]);
            f_mod_test++
        ){
            v_mf3_mod_single(
                &f_pfx_group->multieffect,
                *(a_voice->modulator_outputs[
                    (a_voice->polyfx_mod_src_index[f_dst][f_mod_test])]
                ),
                a_voice->polyfx_mod_matrix_values[f_dst][f_mod_test],
                a_voice->polyfx_mod_ctrl_indexes[f_dst][f_mod_test]
            );
        }

        f_pfx_group->fx_func_ptr(
            &f_pfx_group->multieffect,
            a_voice->multifx_current_sample[0],
            a_voice->multifx_current_sample[1]
        );

        a_voice->multifx_current_sample[0] = f_pfx_group->multieffect.output0;
        a_voice->multifx_current_sample[1] = f_pfx_group->multieffect.output1;
    }

    a_voice->multifx_current_sample[0] *= a_voice->lfo_amp_output;
    a_voice->multifx_current_sample[1] *= a_voice->lfo_amp_output;

    if(!a_voice->noise_prefx){
        SGFLT f_noise_amp;
        if(a_voice->adsr_noise_on){
            v_adsr_run(&a_voice->adsr_noise);
            f_noise_amp =
                a_voice->noise_linamp *
                a_voice->adsr_noise.output *
                a_voice->adsr_main.output;
        } else {
            f_noise_amp =
                a_voice->noise_linamp *
                a_voice->adsr_main.output;
        }
        out->left += noise_sample.left * f_noise_amp;
        out->right += noise_sample.right * f_noise_amp;
    }

    if(a_voice->adsr_prefx){
        out->left += a_voice->multifx_current_sample[0] *
            a_voice->main_vol_lin * a_voice->panner.gainL;
        out->right += a_voice->multifx_current_sample[1] *
            a_voice->main_vol_lin * a_voice->panner.gainR;
    } else {
        out->left += a_voice->multifx_current_sample[0] *
            a_voice->adsr_main.output * a_voice->main_vol_lin *
            a_voice->panner.gainL;
        out->right += a_voice->multifx_current_sample[1] *
            a_voice->adsr_main.output * a_voice->main_vol_lin *
            a_voice->panner.gainR;
    }
}


SGFLT* f_char_to_wavetable(char * a_char){
    SGFLT * f_result;

    lmalloc((void**)&f_result, sizeof(SGFLT) * 1024);

    t_1d_char_array * f_arr = c_split_str(a_char, '|', 1025, 32);

    int f_i = 1;

    //int f_count = atoi(f_arr->array[0]);

    while(f_i < 1025){
        f_result[f_i - 1] = atof(f_arr->array[f_i]);
        ++f_i;
    }

    g_free_1d_char_array(f_arr);

    return f_result;
}

void v_fm1_configure(
    PluginHandle instance,
    char* key,
    char* value,
    pthread_spinlock_t* a_spinlock
){
    t_fm1 *plugin_data = (t_fm1*)instance;

    if (!strcmp(key, "fm1_add_eng0"))
    {
        SGFLT * f_table = f_char_to_wavetable(value);
        v_wt_set_wavetable(
            plugin_data->mono_modules.wavetables,
            17,
            f_table,
            1024,
            a_spinlock,
            &plugin_data->mono_modules.reset_wavetables
        );
    }
    else if (!strcmp(key, "fm1_add_eng1"))
    {
        SGFLT * f_table = f_char_to_wavetable(value);
        v_wt_set_wavetable(
            plugin_data->mono_modules.wavetables,
            18,
            f_table,
            1024,
            a_spinlock,
            &plugin_data->mono_modules.reset_wavetables
        );
    }
    else if (!strcmp(key, "fm1_add_eng2"))
    {
        SGFLT * f_table = f_char_to_wavetable(value);
        v_wt_set_wavetable(
            plugin_data->mono_modules.wavetables,
            19,
            f_table,
            1024,
            a_spinlock,
            &plugin_data->mono_modules.reset_wavetables
        );
    }
    else
    {
        //printf("FM1 unhandled configure key %s\n", key);
    }
}

SGFLT* fm1_get_port_table(PluginHandle instance){
    t_fm1 *plugin_data = (t_fm1*)instance;
    return plugin_data->port_table;
}

PluginDescriptor *fm1_plugin_descriptor(){
    PluginDescriptor *f_result = get_plugin_descriptor(FM1_COUNT);

    set_plugin_port(f_result, FM1_ATTACK_MAIN, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_ATTACK_MAIN_START, 0.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_ATTACK_MAIN_END, 200.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY_MAIN, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY_MAIN_START, 10.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY_MAIN_END, 200.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_MAIN, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_MAIN_START, -30.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_MAIN_END, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE_MAIN, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_RELEASE_MAIN_START, 10.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_RELEASE_MAIN_END, 400.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ATTACK1, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY1, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN1, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE1, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ATTACK2, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY2, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN2, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE2, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_NOISE_AMP, -30.0f, -60.0f, 0.0f);
    set_plugin_port(
        f_result,
        FM1_OSC1_TYPE,
        1.0f,
        0.0f,
        (SGFLT)WT_TOTAL_WAVETABLE_COUNT
    );
    set_plugin_port(f_result, FM1_OSC1_PITCH, 0.0f, -72.0f, 72.0f);
    set_plugin_port(f_result, FM1_OSC1_TUNE, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC1_VOLUME, -6.0f, -30.0f, 0.0f);
    set_plugin_port(
        f_result,
        FM1_OSC2_TYPE,
        0.0f,
        0.0f,
        (SGFLT)WT_TOTAL_WAVETABLE_COUNT
    );
    set_plugin_port(f_result, FM1_OSC2_PITCH, 0.0f, -72.0f, 72.0f);
    set_plugin_port(f_result, FM1_OSC2_TUNE, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC2_VOLUME, -6.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_MAIN_VOLUME, -6.0f, -30.0f, 12.0f);
    set_plugin_port(f_result, FM1_OSC1_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    set_plugin_port(f_result, FM1_OSC1_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_MAIN_GLIDE, 0.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_MAIN_PITCHBEND_AMT, 18.0f, 1.0f, 36.0f);
    set_plugin_port(f_result, FM1_ATTACK_PFX1, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY_PFX1, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_PFX1, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE_PFX1, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ATTACK_PFX2, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY_PFX2, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_PFX2, 100.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_RELEASE_PFX2, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_RAMP_ENV_TIME, 100.0f, 0.0f, 600.0f);
    set_plugin_port(f_result, FM1_LFO_FREQ, 200.0f, 10, 1600);
    set_plugin_port(f_result, FM1_LFO_TYPE, 0.0f, 0.0f, 2.0f);
    set_plugin_port(f_result, FM1_FX0_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX0_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX0_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX0_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, FM1_FX1_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX1_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX1_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX1_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, FM1_FX2_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX2_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX2_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX2_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_plugin_port(f_result, FM1_FX3_KNOB0, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX3_KNOB1, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX3_KNOB2, 64.0f, 0.0f, 127.0f);
    set_plugin_port(f_result, FM1_FX3_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);

    int f_i = FM1_PFXMATRIX_GRP0DST0SRC0CTRL0;

    while(f_i <= FM1_PFXMATRIX_GRP0DST3SRC3CTRL2)
    {
        set_plugin_port(f_result, f_i,  0.0f, -100.0f, 100.0f);
        ++f_i;
    }

    set_plugin_port(f_result, FM1_NOISE_TYPE, 0.0f, 0, 2);
    set_plugin_port(f_result, FM1_ADSR1_CHECKBOX, 0.0f, 0, 1);
    set_plugin_port(f_result, FM1_ADSR2_CHECKBOX, 0.0f, 0, 1);
    set_plugin_port(f_result, FM1_LFO_AMP, 0.0f, -24.0f, 24.0f);
    set_plugin_port(f_result, FM1_LFO_PITCH, 0.0f, -36.0f, 36.0f);
    set_plugin_port(f_result, FM1_PITCH_ENV_AMT, 0.0f, -60.0f, 60.0f);
    set_plugin_port(f_result, FM1_OSC2_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    set_plugin_port(f_result, FM1_OSC2_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_LFO_AMOUNT, 100.0f, 0.0f, 100.0f);
    set_plugin_port(
        f_result,
        FM1_OSC3_TYPE,
        0.0f,
        0.0f,
        (SGFLT)WT_TOTAL_WAVETABLE_COUNT
    );
    set_plugin_port(f_result, FM1_OSC3_PITCH, 0.0f, -72.0f, 72.0f);
    set_plugin_port(f_result, FM1_OSC3_TUNE, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC3_VOLUME, -6.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_OSC3_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    set_plugin_port(f_result, FM1_OSC3_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC1_FM1, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC1_FM2, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC1_FM3, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC2_FM1, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC2_FM2, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC2_FM3, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC3_FM1, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC3_FM2, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC3_FM3, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_ATTACK3, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY3, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN3, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE3, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ADSR3_CHECKBOX, 0.0f, 0, 1);

    f_i = FM1_PFXMATRIX_GRP0DST0SRC4CTRL0;

    while(f_i <= FM1_PFXMATRIX_GRP0DST3SRC5CTRL2)
    {
        set_plugin_port(f_result, f_i, 0.0f, -100.0f, 100.0f);
        ++f_i;
    }

    set_plugin_port(f_result, FM1_PERC_ENV_TIME1, 10.0f, 2.0f, 40.0f);
    set_plugin_port(f_result, FM1_PERC_ENV_PITCH1, 66.0f, 42.0f, 120.0f);
    set_plugin_port(f_result, FM1_PERC_ENV_TIME2, 100.0f, 20.0f, 400.0f);
    set_plugin_port(f_result, FM1_PERC_ENV_PITCH2, 48.0f, 33.0f, 63.0f);
    set_plugin_port(f_result, FM1_PERC_ENV_ON, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, FM1_RAMP_CURVE, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_MONO_MODE, 0.0f, 0.0f, 3.0f);
    set_plugin_port(f_result, FM1_OSC1_FM4, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC2_FM4, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC3_FM4, 0.0f, 0.0f, 100.0f);
    set_plugin_port(
        f_result,
        FM1_OSC4_TYPE,
        0.0f,
        0.0f,
        (SGFLT)WT_TOTAL_WAVETABLE_COUNT
    );
    set_plugin_port(f_result, FM1_OSC4_PITCH, 0.0f, -72.0f, 72.0f);
    set_plugin_port(f_result, FM1_OSC4_TUNE, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC4_VOLUME, -6.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_OSC4_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    set_plugin_port(f_result, FM1_OSC4_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC4_FM1, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC4_FM2, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC4_FM3, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC4_FM4, 0.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_ATTACK4, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY4, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN4, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE4, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ADSR4_CHECKBOX, 0.0f, 0, 1);
    set_plugin_port(f_result, FM1_LFO_PHASE, 0.0f, 0.0f, 100.0);

    f_i = 0;
    int f_port = FM1_FM_MACRO1;

    while(f_i < 2)
    {
        set_plugin_port(f_result, f_port, 0.0f, 0.0f, 100.0f);
        ++f_port;

        int f_i2 = 0;

        while(f_i2 < 4)
        {
            int f_i3 = 0;

            while(f_i3 < 4)
            {
                set_plugin_port(f_result, f_port, 0.0f, -100.0f, 100.0f);
                ++f_port;
                ++f_i3;
            }

            ++f_i2;
        }

        ++f_i;
    }


    f_i = 0;
    f_port = FM1_FM_MACRO1_OSC1_VOL;

    while(f_i < 2)
    {
        int f_i2 = 0;

        while(f_i2 < 4)
        {
            set_plugin_port(f_result, f_port, 0.0f, -30.0f, 30.0f);
            ++f_port;
            ++f_i2;
        }

        ++f_i;
    }

    set_plugin_port(f_result, FM1_LFO_PITCH_FINE, 0.0f, -100.0f, 100.0);
    set_plugin_port(f_result, FM1_ADSR_PREFX, 0.0f, 0.0f, 1.0);

    f_port = FM1_ADSR1_DELAY;

    // The loop covers the hold and delay ports
    while(f_port <= FM1_HOLD_MAIN)
    {
        set_plugin_port(f_result, f_port, 0.0f, 0.0f, 200.0f);
        ++f_port;
    }

    set_plugin_port(f_result, FM1_DELAY_NOISE, 0.0f, 0.0f, 200.0);
    set_plugin_port(f_result, FM1_ATTACK_NOISE, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_HOLD_NOISE, 0.0f, 0.0f, 200.0);
    set_plugin_port(f_result, FM1_DECAY_NOISE, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_NOISE, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE_NOISE, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ADSR_NOISE_ON, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, FM1_DELAY_LFO, 0.0f, 0.0f, 200.0);
    set_plugin_port(f_result, FM1_ATTACK_LFO, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_HOLD_LFO, 0.0f, 0.0f, 200.0);
    set_plugin_port(f_result, FM1_DECAY_LFO, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN_LFO, 100.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_RELEASE_LFO, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ADSR_LFO_ON, 0.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, FM1_OSC5_TYPE, 0.0f, 0.0f, (SGFLT)WT_TOTAL_WAVETABLE_COUNT);
    set_plugin_port(f_result, FM1_OSC5_PITCH, 0.0f, -72.0f, 72.0f);
    set_plugin_port(f_result, FM1_OSC5_TUNE, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC5_VOLUME, -6.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_OSC5_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    set_plugin_port(f_result, FM1_OSC5_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_ADSR5_DELAY, 0.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_ATTACK5, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_ADSR5_HOLD, 0.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY5, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN5, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE5, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ADSR5_CHECKBOX, 0.0f, 0, 1);
    set_plugin_port(f_result, FM1_OSC6_TYPE, 0.0f, 0.0f, (SGFLT)WT_TOTAL_WAVETABLE_COUNT);
    set_plugin_port(f_result, FM1_OSC6_PITCH, 0.0f, -72.0f, 72.0f);
    set_plugin_port(f_result, FM1_OSC6_TUNE, 0.0f, -100.0f, 100.0f);
    set_plugin_port(f_result, FM1_OSC6_VOLUME, -6.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_OSC6_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    set_plugin_port(f_result, FM1_OSC6_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    set_plugin_port(f_result, FM1_ADSR6_DELAY, 0.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_ATTACK6, 10.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_ADSR6_HOLD, 0.0f, 0.0f, 200.0f);
    set_plugin_port(f_result, FM1_DECAY6, 50.0f, 10.0f, 200.0f);
    set_plugin_port(f_result, FM1_SUSTAIN6, 0.0f, -30.0f, 0.0f);
    set_plugin_port(f_result, FM1_RELEASE6, 50.0f, 10.0f, 400.0f);
    set_plugin_port(f_result, FM1_ADSR6_CHECKBOX, 0.0f, 0, 1);
    set_plugin_port(f_result, FM1_MIN_NOTE, 0.0f, 0.0f, 120.0f);
    set_plugin_port(f_result, FM1_MAX_NOTE, 120.0f, 0.0f, 120.0f);
    set_plugin_port(f_result, FM1_MAIN_PITCH, 0.0f, -36.0f, 36.0f);
    set_plugin_port(f_result, FM1_ADSR_LIN_MAIN, 1.0f, 0.0f, 1.0f);
    set_plugin_port(f_result, FM1_MAIN_PAN, 0.0f, -100.0f, 100.0f);

    f_port = FM1_FM_MACRO1_OSC1_FM5;

    while(f_port <= FM1_FM_MACRO2_OSC6_VOL)
    {
        set_plugin_port(f_result, f_port, 0.0f, -100.0f, 100.0f);
        ++f_port;
    }

    f_port = FM1_OSC5_FM1;

    while(f_port <= FM1_OSC6_FM4)
    {
        set_plugin_port(f_result, f_port, 0.0f, 0.0f, 100.0f);
        ++f_port;
    }

    f_port = FM1_OSC1_FM5;

    while(f_port <= FM1_OSC6_FM5)
    {
        set_plugin_port(f_result, f_port, 0.0f, 0.0f, 100.0f);
        ++f_port;
    }

    f_port = FM1_OSC1_FM6;

    while(f_port <= FM1_OSC6_FM6){
        set_plugin_port(f_result, f_port, 0.0f, 0.0f, 100.0f);
        ++f_port;
    }

    set_plugin_port(f_result, FM1_NOISE_PREFX, 1.0f, 0, 1);

    f_port = FM1_PFXMATRIX_GRP0DST0SRC6CTRL0;

    while(f_port <= FM1_PFXMATRIX_GRP0DST3SRC7CTRL2)
    {
        set_plugin_port(f_result, f_port,  0.0f, -100.0f, 100.0f);
        ++f_port;
    }
    for(f_port = FM1_OSC1_PAN; f_port <= FM1_OSC6_PAN; ++f_port){
        set_plugin_port(f_result, f_port,  0.0f, -100.0f, 100.0f);
    }

    f_result->cleanup = v_cleanup_fm1;
    f_result->connect_port = v_fm1_connect_port;
    f_result->get_port_table = fm1_get_port_table;
    f_result->instantiate = g_fm1_instantiate;
    f_result->panic = fm1Panic;
    f_result->load = v_fm1_load;
    f_result->set_port_value = v_fm1_set_port_value;
    f_result->set_cc_map = v_fm1_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = v_fm1_configure;
    f_result->run = v_run_fm1;
    f_result->offline_render_prep = v_fm1_or_prep;
    f_result->on_stop = v_fm1_on_stop;

    return f_result;
}

/*initialize all of the modules in an instance of poly_voice*/

void g_fm1_poly_init(
    t_fm1_poly_voice* voice,
    SGFLT a_sr,
    t_fm1_mono_modules* a_mono,
    int voice_num
){
    t_fm1_osc* f_osc;
    int f_i, f_i2;

    for(f_i = 0; f_i < FM1_OSC_COUNT; ++f_i){
        voice->osc[f_i] = (t_fm1_osc){};
        f_osc = &voice->osc[f_i];
        g_osc_init_osc_wav_unison(
            &f_osc->osc_wavtable,
            a_sr,
            f_i + voice_num
        );
        f_osc->osc_uni_spread = 0.0f;
        f_osc->osc_on = 0;
        f_osc->fm_last = 0.0;
        g_adsr_init(&f_osc->adsr_amp_osc, a_sr);
        f_osc->adsr_amp_on = 0;
        f_osc->osc_linamp = 1.0f;
        f_osc->osc_audible = 1;
        g_pn2_init(&f_osc->panner);

        for(f_i2 = 0; f_i2 < FM1_OSC_COUNT; ++f_i2){
            f_osc->fm_osc_values[f_i2] = 0.0f;
            f_osc->osc_fm[f_i2] = 0.0;
        }
    }

    g_adsr_init(&voice->adsr_main, a_sr);

    resampler_linear_init(
        &voice->resampler,
        44100,
        a_sr,
        fm1_run_voice_osc
    );

    g_white_noise_init(&voice->white_noise[0], a_sr);
    g_white_noise_init(&voice->white_noise[1], a_sr);
    voice->noise_amp = 0;

    g_rmp_init(&voice->glide_env, a_sr);

    //voice->real_pitch = 60.0f;

    voice->target_pitch = 66.0f;
    voice->last_pitch = 66.0f;
    voice->base_pitch = 66.0f;

    resampler_stereo_pair_init(&voice->current_sample);

    voice->amp = 1.0f;
    voice->note_f = voice_num;

    voice->noise_linamp = 1.0f;
    voice->adsr_prefx = 0;

    voice->lfo_amount_output = 0.0f;
    voice->lfo_amp_output = 0.0f;
    voice->lfo_pitch_output = 0.0f;

    g_adsr_init(&voice->adsr_amp, a_sr);
    g_adsr_init(&voice->adsr_filter, a_sr);
    g_adsr_init(&voice->adsr_noise, a_sr);
    g_adsr_init(&voice->adsr_lfo, a_sr);
    voice->adsr_noise_on = 0;
    voice->adsr_lfo_on = 0;

    voice->noise_amp = 0.0f;

    g_pn2_init(&voice->panner);
    g_rmp_init(&voice->glide_env, a_sr);
    g_rmp_init(&voice->ramp_env, a_sr);

    g_lfs_init(&voice->lfo1, a_sr);

    voice->noise_sample = 0.0f;


    for(f_i = 0; f_i < FM1_MODULAR_POLYFX_COUNT; ++f_i){
        g_mf3_init(&voice->effects[f_i].multieffect, a_sr, 1);
        voice->effects[f_i].fx_func_ptr = v_mf3_run_off;
    }

    voice->modulator_outputs[0] = &(voice->adsr_amp.output);
    voice->modulator_outputs[1] = &(voice->adsr_filter.output);
    voice->modulator_outputs[2] = &(voice->ramp_env.output);
    voice->modulator_outputs[3] = &(voice->lfo_amount_output);
    voice->modulator_outputs[4] = &(voice->keyboard_track);
    voice->modulator_outputs[5] = &(voice->velocity_track);
    voice->modulator_outputs[6] = &(a_mono->fm_macro_smoother[0].last_value);
    voice->modulator_outputs[7] = &(a_mono->fm_macro_smoother[1].last_value);

    voice->noise_func_ptr = noise_off_stereo_run;

    voice->perc_env_on = 0;
    g_pnv_init(&voice->perc_env, a_sr);
}


void v_fm1_poly_note_off(t_fm1_poly_voice * a_voice, int a_fast)
{
    if(a_fast)
    {
        v_adsr_set_fast_release(&a_voice->adsr_main);
    }
    else
    {
        v_adsr_release(&a_voice->adsr_main);
    }

    v_adsr_release(&a_voice->adsr_lfo);
    v_adsr_release(&a_voice->adsr_noise);
    v_adsr_release(&a_voice->adsr_amp);
    v_adsr_release(&a_voice->adsr_filter);

    int f_i = 0;

    while(f_i < FM1_OSC_COUNT)
    {
        v_adsr_release(&a_voice->osc[f_i].adsr_amp_osc);
        ++f_i;
    }

}

/*Initialize any modules that will be run monophonically*/
void v_fm1_mono_init(t_fm1_mono_modules* a_mono, SGFLT a_sr){
    g_sml_init(&a_mono->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.2f);

    int f_i = 0;
    for(f_i = 0; f_i < FM1_FM_MACRO_COUNT; ++f_i){
        g_sml_init(&a_mono->fm_macro_smoother[f_i], a_sr, 0.5f, 0.0f, 0.02f);
    }

    a_mono->wavetables = g_wt_wavetables_get();
    //indicates that wavetables must be re-pointered immediately
    a_mono->reset_wavetables = 0;
    g_svf2_init(&a_mono->aa_filter, a_sr);
    v_svf2_set_cutoff_base(&a_mono->aa_filter, 120.0f);
    v_svf2_add_cutoff_mod(&a_mono->aa_filter, 0.0f);
    v_svf2_set_res(&a_mono->aa_filter, -6.0f);
    v_svf2_set_cutoff(&a_mono->aa_filter);

    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    a_mono->pan_smoother.last_value = 0.0f;
    g_pn2_init(&a_mono->panner);
}

