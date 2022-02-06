#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/delay/reverb.h"
#include "audiodsp/modules/filter/comb_filter.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"


void v_rvb_reverb_set(
    t_rvb_reverb* self,
    SGFLT a_time,
    SGFLT a_wet,
    SGFLT a_color,
    SGFLT a_predelay,
    SGFLT a_hp_cutoff
){
    if(unlikely(a_time != self->time)){
        self->time = a_time;
        // Changes to the comb filters now cause it to play forever at 1.0
        // so adjust it here
        a_time *= 0.93;
        int f_i;
        SGFLT f_base = 30.0f - (a_time * 25.0f);
        SGFLT f_factor = 1.4f + (a_time * 0.8f);

        self->feedback = a_time - 1.03f;
        v_lfs_set(&self->lfo, 1.0f - (a_time * 0.9f));

        for(f_i = 0; f_i < REVERB_TAP_COUNT; ++f_i){
            self->taps[f_i].pitch = f_base + (((SGFLT)f_i) * f_factor);
            v_cmb_set_all(
                &self->taps[f_i].tap,
                0.0f,
                self->feedback,
                self->taps[f_i].pitch
            );
        }

    }

    if(unlikely(a_wet != self->wet)){
        self->wet = a_wet;
        self->wet_linear =  a_wet * (self->volume_factor);
    }

    if(unlikely(a_color != self->color)){
        self->color = a_color;
        v_svf_set_cutoff_base(&self->lp, a_color);
        v_svf_set_cutoff(&self->lp);
    }

    if(unlikely(self->last_predelay != a_predelay)){
        self->last_predelay = a_predelay;
        self->predelay_size = (int)(self->sr * a_predelay);
        if(self->predelay_counter >= self->predelay_size){
            self->predelay_counter = 0;
        }
    }

    if(unlikely(self->hp_cutoff != a_hp_cutoff)){
        v_svf_set_cutoff_base(&self->hp, a_hp_cutoff);
        v_svf_set_cutoff(&self->hp);
        self->hp_cutoff = a_hp_cutoff;
    }
}

void v_rvb_reverb_run(
    t_rvb_reverb* self,
    SGFLT a_input0,
    SGFLT a_input1
){
    int f_i;
    t_state_variable_filter * f_filter;
    t_comb_filter * f_comb;

    self->output[0] *= 0.02f;
    self->output[1] *= 0.02f;
    v_lfs_run(&self->lfo);
    SGFLT f_lfo_diff = self->lfo.output * 2.0f;

    SGFLT f_tmp_sample = v_svf_run_2_pole_lp(
        &self->lp,
        a_input0 + a_input1
    );
    f_tmp_sample = v_svf_run_2_pole_hp(&self->hp, f_tmp_sample);
    f_tmp_sample *= (self->wet_linear);

    for(f_i = 0; f_i < REVERB_TAP_COUNT; ++f_i){
        f_comb = &self->taps[f_i].tap;
        v_cmb_run(f_comb, f_tmp_sample);
        self->output[0] += f_comb->output_sample;
        self->output[1] += f_comb->output_sample;
    }

    for(f_i = 0; f_i < REVERB_DIFFUSER_COUNT; ++f_i){
        f_filter = &self->diffusers[f_i].diffuser;
        v_svf_set_cutoff_base(
            f_filter,
            self->diffusers[f_i].pitch + f_lfo_diff
        );
        v_svf_set_cutoff(f_filter);
        self->output[0] = v_svf_run_2_pole_allpass(f_filter, self->output[0]);
        v_svf_set_cutoff_base(
            f_filter,
            self->diffusers[f_i].pitch - f_lfo_diff
        );
        v_svf_set_cutoff(f_filter);
        self->output[1] = v_svf_run_2_pole_allpass(f_filter, self->output[1]);
    }

    self->predelay_buffer[0][self->predelay_counter] = self->output[0];
    self->predelay_buffer[1][self->predelay_counter] = self->output[1];
    ++self->predelay_counter;
    if(unlikely(self->predelay_counter >= self->predelay_size)){
        self->predelay_counter = 0;
    }

    self->output[0] = self->predelay_buffer[0][self->predelay_counter];
    self->output[1] = self->predelay_buffer[1][self->predelay_counter];
}

void v_rvb_panic(t_rvb_reverb * self){
    int f_i, f_i2;
    SGFLT * f_tmp;
    int f_count;
    int f_pre_count = self->sr + 5000;
    for(f_i2 = 0; f_i2 < 2; ++f_i2){
        for(f_i = 0; f_i < f_pre_count; ++f_i){
            self->predelay_buffer[f_i2][f_i] = 0.0f;
        }
    }

    for(f_i = 0; f_i < REVERB_TAP_COUNT; ++f_i){
        f_tmp = self->taps[f_i].tap.input_buffer;
        f_count = self->taps[f_i].tap.buffer_size;
        for(f_i2 = 0; f_i2 < f_count; ++f_i2){
            f_tmp[f_i2] = 0.0f;
        }
    }
}

void g_rvb_reverb_init(t_rvb_reverb* f_result, SGFLT a_sr){
    int f_i, i;
    SGFLT* buffer[2];
    for(i = 0; i < 2; ++i){
        hpalloc(
            (void**)&buffer[i],
            sizeof(SGFLT) * (a_sr + 5000)
        );

        for(f_i = 0; f_i < a_sr + 5000; ++f_i){
            buffer[i][f_i] = 0.0f;
        }
    }
    g_rvb_reverb_init_buffer(
        f_result,
        a_sr,
        buffer
    );
}

void g_rvb_reverb_init_buffer(
    t_rvb_reverb * f_result,
    SGFLT a_sr,
    SGFLT** buffer
){
    int f_i;

    f_result->predelay_buffer[0] = buffer[0];
    f_result->predelay_buffer[1] = buffer[1];
    f_result->color = -12345.67;
    // Force set it the first time
    f_result->time = -123.5f;
    f_result->wet = 0.0f;
    f_result->wet_linear = 0.0f;
    f_result->hp_cutoff = -12345.0f;

    f_result->sr = a_sr;

    for(f_i = 0; f_i < REVERB_DIFFUSER_COUNT; ++f_i){
        f_result->diffusers[f_i].pitch = 33.0f + (((SGFLT)f_i) * 7.0f);
    }

    f_result->output[0] = 0.0f;
    f_result->output[1] = 0.0f;

    g_lfs_init(&f_result->lfo, a_sr);
    v_lfs_sync(&f_result->lfo, 0.0f, 1);

    g_svf_init(&f_result->hp, a_sr);
    v_svf_set_res(&f_result->hp, -36.0f);
    v_svf_set_cutoff_base(&f_result->hp, 60.0f);
    v_svf_set_cutoff(&f_result->hp);

    g_svf_init(&f_result->lp, a_sr);
    v_svf_set_res(&f_result->lp, -36.0f);

    f_result->volume_factor = (1.0f / (SGFLT)REVERB_DIFFUSER_COUNT) * 0.5;

    for(f_i = 0; f_i < REVERB_TAP_COUNT; ++f_i){
        g_cmb_init(&f_result->taps[f_i].tap, a_sr, 1);
    }

    for(f_i = 0; f_i < REVERB_DIFFUSER_COUNT; ++f_i){
        g_svf_init(&f_result->diffusers[f_i].diffuser, a_sr);
        v_svf_set_cutoff_base(
            &f_result->diffusers[f_i].diffuser,
            f_result->diffusers[f_i].pitch
        );
        v_svf_set_res(&f_result->diffusers[f_i].diffuser, -6.0f);
        v_svf_set_cutoff(&f_result->diffusers[f_i].diffuser);
    }

    f_result->predelay_counter = 0;
    f_result->last_predelay = -1234.0f;
    f_result->predelay_size = (int)(a_sr * 0.01f);

    v_rvb_reverb_set(f_result, 0.5f, 0.0f, 55.5f, 0.01f, 60.0f);
}

