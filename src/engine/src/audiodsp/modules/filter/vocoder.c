#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/filter/vocoder.h"
#include "audiodsp/modules/modulation/env_follower2.h"


void g_vdr_band_init(
    t_vdr_band * self,
    SGFLT a_sr,
    SGFLT a_pitch,
    SGFLT a_res
){
    SGFLT f_release = (1.0f / f_pit_midi_note_to_hz(a_pitch));
    g_svf_init(&self->m_filter, a_sr);
    v_svf_set_res(&self->m_filter, a_res);
    v_svf_set_cutoff_base(&self->m_filter, a_pitch);
    v_svf_set_cutoff(&self->m_filter);
    g_enf_init(&self->env_follower, a_sr);
    v_enf_set(&self->env_follower, 0.001f, f_release);
    g_svf2_init(&self->c_filter, a_sr);
    v_svf2_set_res(&self->c_filter, a_res);
    v_svf2_set_cutoff_base(&self->c_filter, a_pitch);
    v_svf2_set_cutoff(&self->c_filter);
}

void g_vdr_init(t_vdr_vocoder * self, SGFLT a_sr){
    self->output0 = 0.0f;
    self->output1 = 0.0f;

    int f_i;
    SGFLT f_freq = f_pit_hz_to_midi_note(240.0f);
    SGFLT f_inc = (f_pit_hz_to_midi_note(7200.0f) - f_freq) /
        (SGFLT)VOCODER_BAND_COUNT;

    for(f_i = 0; f_i < VOCODER_BAND_COUNT; ++f_i){
        g_vdr_band_init(
            &self->bands[f_i],
            a_sr,
            f_freq,
            -2.1f
        );
        f_freq += f_inc;
    }

    g_vdr_band_init(
        &self->low_band,
        a_sr,
        f_pit_hz_to_midi_note(200.0f),
        -6.0f
    );
    g_vdr_band_init(
        &self->high_band,
        a_sr,
        f_pit_hz_to_midi_note(7500.0f),
        -6.0f
    );

}

void v_vdr_run(
    t_vdr_vocoder * self,
    SGFLT a_mod_in0,
    SGFLT a_mod_in1,
    SGFLT a_input0,
    SGFLT a_input1
){
    int f_i;
    SGFLT f_env_val;
    t_state_variable_filter * f_m_filter;
    t_svf2_filter * f_c_filter;
    t_enf2_env_follower * f_envf;
    SGFLT f_mono_input = (a_mod_in0 + a_mod_in1) * 0.5f;

    self->output0 = 0.0f;
    self->output1 = 0.0f;

    for(f_i = 0; f_i < VOCODER_BAND_COUNT; ++f_i){
        f_m_filter = &self->bands[f_i].m_filter;
        f_envf = &self->bands[f_i].env_follower;
        f_c_filter = &self->bands[f_i].c_filter;

        f_env_val = v_svf_run_2_pole_bp(
            f_m_filter,
            f_mono_input
        );
        v_enf_run(f_envf, f_env_val);

        v_svf2_run_2_pole_bp(f_c_filter, a_input0, a_input1);
        self->output0 += f_c_filter->output0 * f_envf->envelope;
        self->output1 += f_c_filter->output1 * f_envf->envelope;
    }

    f_m_filter = &self->low_band.m_filter;
    f_envf = &self->low_band.env_follower;
    f_c_filter = &self->low_band.c_filter;

    f_env_val = v_svf_run_2_pole_lp(f_m_filter, f_mono_input);
    v_enf_run(f_envf, f_env_val);

    v_svf2_run_2_pole_lp(f_c_filter, a_input0, a_input1);
    self->output0 += f_c_filter->output0 * f_envf->envelope;
    self->output1 += f_c_filter->output1 * f_envf->envelope;

    f_env_val *= 0.25f;
    self->output0 += f_env_val;
    self->output1 += f_env_val;

    f_m_filter = &self->high_band.m_filter;
    f_envf = &self->high_band.env_follower;
    f_c_filter = &self->high_band.c_filter;

    f_env_val = v_svf_run_2_pole_hp(f_m_filter, f_mono_input);
    v_enf_run(f_envf, f_env_val);

    v_svf2_run_2_pole_hp(f_c_filter, a_input0, a_input1);
    self->output0 += f_c_filter->output0 * f_envf->envelope;
    self->output1 += f_c_filter->output1 * f_envf->envelope;

    f_env_val *= 0.25f;
    self->output0 += f_env_val;
    self->output1 += f_env_val;
}

