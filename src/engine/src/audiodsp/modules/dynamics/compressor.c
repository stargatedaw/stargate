#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower2.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/peak_meter.h"
#include "audiodsp/modules/dynamics/compressor.h"


void g_cmp_init(t_cmp_compressor* self, SGFLT a_sr){
    self->thresh = 0.0f;
    self->knee_thresh = 0.0f;
    self->ratio = 1.0f;
    self->knee = 0.0f;
    self->gain = 0.0f;
    self->gain_lin = 1.0f;
    self->output0 = 0.0f;
    self->output1 = 0.0f;
    self->sr = a_sr;
    self->rms_count = 100;
    self->rms_counter = 0;
    self->rms_time = -123.456f;
    self->rms_last = 0.0f;
    self->rms_sum = 0.0f;
    g_svf_init(&self->filter, a_sr);
    v_svf_set_cutoff_base(&self->filter, 66.0f);
    v_svf_set_res(&self->filter, -24.0f);
    v_svf_set_cutoff(&self->filter);
    g_enf_init(&self->env_follower, a_sr);
    g_pkm_redux_init(&self->peak_tracker, a_sr);
}

void v_cmp_set(
    t_cmp_compressor * self,
    SGFLT thresh,
    SGFLT ratio,
    SGFLT knee,
    SGFLT attack,
    SGFLT release,
    SGFLT gain
){
    v_enf_set(&self->env_follower, attack, release);

    self->knee = knee;
    self->thresh = thresh;
    self->knee_thresh = thresh - knee;

    if(self->ratio != ratio){
        self->ratio = ratio;
        self->ratio_recip = (1.0f - (1.0f / ratio)) * -1.0f;
    }

    if(self->gain != gain){
        self->gain = gain;
        self->gain_lin = f_db_to_linear_fast(gain);
    }
}

void v_cmp_run(t_cmp_compressor* self, SGFLT a_in0, SGFLT a_in1){
    SGFLT f_max = f_sg_max(f_sg_abs(a_in0), f_sg_abs(a_in1));
    v_enf_run(&self->env_follower, f_max);
    SGFLT f_db = f_linear_to_db_fast(self->env_follower.envelope);
    SGFLT f_vol = 1.0f;
    SGFLT f_gain = 0.0f;

    if(f_db > self->thresh){
        f_gain = (f_db - self->thresh) * self->ratio_recip;
        f_vol = f_db_to_linear_fast(f_gain);
        f_vol = v_svf_run_4_pole_lp(&self->filter, f_vol);
        self->output0 = a_in0 * f_vol;
        self->output1 = a_in1 * f_vol;
    } else if(f_db > self->knee_thresh){
        SGFLT f_diff = (f_db - self->knee_thresh);
        SGFLT f_percent = f_diff / self->knee;
        SGFLT f_ratio = ((self->ratio - 1.0f) * f_percent) + 1.0f;
        f_vol = f_db_to_linear_fast(f_diff / f_ratio);
        f_vol = v_svf_run_4_pole_lp(&self->filter, f_vol);
        self->output0 = a_in0 * f_vol;
        self->output1 = a_in1 * f_vol;
    } else {
        self->output0 = a_in0;
        self->output1 = a_in1;
    }

    v_pkm_redux_run(&self->peak_tracker, f_vol);
}

void v_cmp_set_rms(t_cmp_compressor * self, SGFLT rms_time){
    if(self->rms_time != rms_time){
        self->rms_time = rms_time;
        self->rms_count = rms_time * self->sr;
        self->rms_count_recip = 1.0f / (SGFLT)self->rms_count;
    }
}

void v_cmp_run_rms(t_cmp_compressor * self, SGFLT a_in0, SGFLT a_in1){
    SGFLT f_vol = 1.0f;
    SGFLT f_gain = 0.0f;
    self->rms_sum += f_sg_max(a_in0 * a_in0, a_in1 * a_in1);
    ++self->rms_counter;

    if(self->rms_counter >= self->rms_count){
        self->rms_counter = 0;
        self->rms_last = sqrt(self->rms_sum * self->rms_count_recip);
        self->rms_sum = 0.0f;
    }

    v_enf_run(&self->env_follower, self->rms_last);
    SGFLT f_db = f_linear_to_db_fast(self->env_follower.envelope);

    if(f_db > self->thresh){
        f_gain = (f_db - self->thresh) * self->ratio_recip;
        f_vol = f_db_to_linear_fast(f_gain);
        f_vol = v_svf_run_4_pole_lp(&self->filter, f_vol);
        self->output0 = a_in0 * f_vol;
        self->output1 = a_in1 * f_vol;
    } else if(f_db > self->knee_thresh){
        SGFLT f_diff = (f_db - self->knee_thresh);
        SGFLT f_percent = f_diff / self->knee;
        SGFLT f_ratio = ((self->ratio - 1.0f) * f_percent) + 1.0f;
        f_gain = f_diff / f_ratio;
        f_vol = f_db_to_linear_fast(f_gain);
        f_vol = v_svf_run_4_pole_lp(&self->filter, f_vol);
        self->output0 = a_in0 * f_vol;
        self->output1 = a_in1 * f_vol;
    } else {
        self->output0 = a_in0;
        self->output1 = a_in1;
    }

    v_pkm_redux_run(&self->peak_tracker, f_vol);
}

