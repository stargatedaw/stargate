#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/delay/chorus.h"
#include "audiodsp/modules/distortion/clipper.h"
#include "audiodsp/modules/distortion/foldback.h"
#include "audiodsp/modules/distortion/glitch.h"
#include "audiodsp/modules/distortion/lofi.h"
#include "audiodsp/modules/distortion/ring_mod.h"
#include "audiodsp/modules/distortion/sample_and_hold.h"
#include "audiodsp/modules/distortion/saturator.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "audiodsp/modules/filter/comb_filter.h"
#include "audiodsp/modules/filter/formant_filter.h"
#include "audiodsp/modules/filter/peak_eq.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/multifx/multifx3knob.h"
#include "audiodsp/modules/signal_routing/amp_and_panner.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


SG_THREAD_LOCAL
const fp_mf3_run mf3_function_pointers[MULTIFX3KNOB_MAX_INDEX] = {
    v_mf3_run_off, //0
    v_mf3_run_lp2, //1
    v_mf3_run_lp4, //2
    v_mf3_run_hp2, //3
    v_mf3_run_hp4, //4
    v_mf3_run_bp2, //5
    v_mf3_run_bp4, //6
    v_mf3_run_notch2, //7
    v_mf3_run_notch4, //8
    v_mf3_run_eq, //9
    v_mf3_run_dist, //10
    v_mf3_run_comb, //11
    v_mf3_run_amp_panner, //12
    v_mf3_run_limiter, //13
    v_mf3_run_saturator, //14
    v_mf3_run_formant_filter, //15
    v_mf3_run_chorus, //16
    v_mf3_run_glitch, //17
    v_mf3_run_ring_mod, //18
    v_mf3_run_lofi, //19
    v_mf3_run_s_and_h, //20
    v_mf3_run_lp_dw, //21
    v_mf3_run_hp_dw, //22
    v_mf3_run_monofier, //23
    v_mf3_run_lp_hp, //24
    v_mf3_run_growl_filter, //25
    v_mf3_run_screech_lp, //26
    v_mf3_run_metal_comb,   //27
    v_mf3_run_notch_dw, //28
    v_mf3_run_foldback, //29
    v_mf3_run_notch_spread, //30
    v_mf3_run_dc_offset, //31
    v_mf3_run_bp_spread, //32
    v_mf3_run_phaser_static, //33
    v_mf3_run_flanger_static, //34
    v_mf3_run_soft_clipper, //35
    NULL, //36
    v_mf3_run_bp_dw, //37
    v_mf3_run_ladder4, //38
};

SG_THREAD_LOCAL
const fp_mf3_reset mf3_reset_function_pointers[MULTIFX3KNOB_MAX_INDEX] = {
    v_mf3_reset_null, //0
    v_mf3_reset_svf, //1
    v_mf3_reset_svf, //2
    v_mf3_reset_svf, //3
    v_mf3_reset_svf, //4
    v_mf3_reset_svf, //5
    v_mf3_reset_svf, //6
    v_mf3_reset_svf, //7
    v_mf3_reset_svf, //8
    v_mf3_reset_null, //9
    v_mf3_reset_null, //10
    v_mf3_reset_null, //11
    v_mf3_reset_null, //12
    v_mf3_reset_null, //13
    v_mf3_reset_null, //14
    v_mf3_reset_null, //15
    v_mf3_reset_null, //16
    v_mf3_reset_glitch, //17
    v_mf3_reset_null, //18
    v_mf3_reset_null, //19
    v_mf3_reset_null, //20
    v_mf3_reset_svf, //21
    v_mf3_reset_svf, //22
    v_mf3_reset_null, //23
    v_mf3_reset_svf, //24
    v_mf3_reset_null, //25
    v_mf3_reset_svf, //26
    v_mf3_reset_null, //27
    v_mf3_reset_svf, //28
    v_mf3_reset_null, //29
    v_mf3_reset_svf, //30
    v_mf3_reset_dc_offset, //31
    v_mf3_reset_svf, //32
    v_mf3_reset_null, //33
    v_mf3_reset_null, //34
    v_mf3_reset_null, //35
    v_mf3_reset_null, //36
    v_mf3_reset_null, //37
    v_mf3_reset_null, //38
};

void v_mf3_reset_null(t_mf3_multi* self){
    //do nothing
}

void v_mf3_reset_svf(t_mf3_multi* self){
    v_svf2_reset(&self->svf);
    v_svf2_reset(&self->svf2);
}

void v_mf3_reset_glitch(t_mf3_multi* self){
    v_glc_glitch_retrigger(&self->glitch);
}

void v_mf3_reset_dc_offset(t_mf3_multi* self){
    v_dco_reset(&self->dc_offset[0]);
    v_dco_reset(&self->dc_offset[1]);
}

/* void v_mf3_set(t_fx3_multi* self, int a_fx_index)
 */
fp_mf3_run g_mf3_get_function_pointer(int a_fx_index){
    return mf3_function_pointers[a_fx_index];
}

/* void v_mf3_set(t_fx3_multi* self, int a_fx_index)
 */
fp_mf3_reset g_mf3_get_reset_function_pointer(int a_fx_index){
    return mf3_reset_function_pointers[a_fx_index];
}


void v_mf3_set(
    t_mf3_multi* self,
    SGFLT a_control0,
    SGFLT a_control1,
    SGFLT a_control2
){
    self->control[0] = a_control0;
    self->control[1] = a_control1;
    self->control[2] = a_control2;

    self->mod_value[0] = 0.0f;
    self->mod_value[1] = 0.0f;
    self->mod_value[2] = 0.0f;
}

/* void v_mf3_mod(t_mf3_multi* self,
 * SGFLT a_mod, //Expects 0 to 1 or -1 to 1 range from an LFO, envelope, etc...
 * SGFLT a_amt0, SGFLT a_amt1, SGFLT a_amt2)  //Amount, from the GUI.
 *                                              Range:  -100 to 100
 */
void v_mf3_mod(
    t_mf3_multi* self,
    SGFLT a_mod,
    SGFLT a_amt0,
    SGFLT a_amt1,
    SGFLT a_amt2
){
    self->mod_value[0] = (self->mod_value[0]) + (a_mod * a_amt0 * .01f);
    self->mod_value[1] = (self->mod_value[1]) + (a_mod * a_amt1 * .01f);
    self->mod_value[2] = (self->mod_value[2]) + (a_mod * a_amt2 * .01f);
}

/* void v_mf3_mod_single(
 * t_mf3_multi* self,
 * SGFLT a_mod, //The output of the LFO, etc...  -1.0f to 1.0f
 * SGFLT a_amt, //amount, -1.0f to 1.0f
 * int a_index)  //control index
 */
void v_mf3_mod_single(
    t_mf3_multi* self,
    SGFLT a_mod,
    SGFLT a_amt,
    int a_index
){
    //not  * .01 because it's expected you did this at note_on
    self->mod_value[a_index] = (self->mod_value[a_index]) + (a_mod * a_amt);
}

void v_mf3_commit_mod(t_mf3_multi* self){
    self->control[0] = (self->control[0]) + ((self->mod_value[0]) * 127.0f);

    if((self->control[0]) > 127.0f){
        self->control[0] = 127.0f;
    }

    if((self->control[0]) < 0.0f){
        self->control[0] = 0.0f;
    }

    self->control[1] = (self->control[1]) + ((self->mod_value[1]) * 127.0f);

    if((self->control[1]) > 127.0f){
        self->control[1] = 127.0f;
    }

    if((self->control[1]) < 0.0f){
        self->control[1] = 0.0f;
    }

    self->control[2] = (self->control[2]) + ((self->mod_value[2]) * 127.0f);

    if((self->control[2]) > 127.0f){
        self->control[2] = 127.0f;
    }

    if((self->control[2]) < 0.0f){
        self->control[2] = 0.0f;
    }
}

void v_mf3_run_off(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    self->output0 = a_in0;
    self->output1 = a_in1;
}

void v_mf3_run_lp2(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_2_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_lp4(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_4_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_hp2(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_2_pole_hp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_hp4(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_4_pole_hp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_bp2(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_2_pole_bp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_bp4(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_4_pole_bp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_notch2(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_2_pole_notch(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_notch4(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_4_pole_notch(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf3_run_notch_spread(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    // cutoff
    self->control_value[0] = (((self->control[0]) * 0.4375) + 44.0f);
    // res
    self->control_value[1] = ((self->control[1]) * 0.0703125) - 10.0f;
    // spread
    self->control_value[2] = ((self->control[2]) * 0.28125);

    v_svf2_set_cutoff_base(
        &self->svf,
        self->control_value[0] - self->control_value[2]
    );
    v_svf2_set_res(
        &self->svf,
        self->control_value[1]
    );
    v_svf2_set_cutoff(&self->svf);
    v_svf2_run_4_pole_lp(&self->svf, a_in0, a_in1);

    v_svf2_set_cutoff_base(
        &self->svf2,
        self->control_value[0] + self->control_value[2]
    );
    v_svf2_set_res(
        &self->svf2,
        self->control_value[1]
    );
    v_svf2_set_cutoff(&self->svf2);
    v_svf2_run_4_pole_hp(&self->svf2, a_in0, a_in1);

    self->output0 = self->svf.output0 + self->svf2.output0;
    self->output1 = self->svf.output1 + self->svf2.output1;
}

void v_mf3_run_bp_spread(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    // cutoff
    self->control_value[0] = (((self->control[0]) * 0.4375) + 44.0f);
    // res
    self->control_value[1] = ((self->control[1]) * 0.0703125) - 10.0f;
    // spread
    self->control_value[2] = ((self->control[2]) * 0.375);

    v_svf2_set_cutoff_base(
        &self->svf,
        self->control_value[0] + self->control_value[2]
    );
    v_svf2_set_res(
        &self->svf,
        self->control_value[1]
    );
    v_svf2_set_cutoff(&self->svf);
    v_svf2_run_4_pole_lp(&self->svf, a_in0, a_in1);

    v_svf2_set_cutoff_base(
        &self->svf2,
        self->control_value[0] - self->control_value[2]
    );
    v_svf2_set_res(
        &self->svf2,
        self->control_value[1]
    );
    v_svf2_set_cutoff(&self->svf2);
    v_svf2_run_4_pole_hp(
        &self->svf2,
        self->svf.output0,
        self->svf.output1
    );

    self->output0 = self->svf2.output0;
    self->output1 = self->svf2.output1;
}

void v_mf3_run_eq(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    //cutoff
    self->control_value[0] = (((self->control[0]) * 0.818897638f) + 20.0f);
    //width
    self->control_value[1] = ((self->control[1]) * 0.039370079f) + 1.0f;
    //gain
    self->control_value[2] = (self->control[2]) * 0.377952756f - 24.0f;

    v_pkq_calc_coeffs(&self->eq0, self->control_value[0],
            self->control_value[1], self->control_value[2]);

    v_pkq_run(&self->eq0, a_in0, a_in1);

    self->output0 = (self->eq0.output0);
    self->output1 = (self->eq0.output1);
}

void v_mf3_run_dist(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.377952756f);
    self->control_value[1] = ((self->control[1]) * 0.007874016f);
    self->control_value[2] = (((self->control[2]) * 0.236220472f) - 30.0f);
    self->outgain = f_db_to_linear(self->control_value[2]);
    v_clp_set_in_gain(&self->clipper, (self->control_value[0]));
    v_axf_set_xfade(&self->xfader, (self->control_value[1]));

    self->output0 = f_axf_run_xfade(
        &self->xfader,
        a_in0,
        f_clp_clip(&self->clipper, a_in0)
    ) * self->outgain;
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        a_in1,
        f_clp_clip(&self->clipper, a_in1)
    ) * self->outgain;
}

void v_mf3_run_soft_clipper(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = (self->control[0] * 0.09375) - 12.0;
    self->control_value[1] = (self->control[1] * 0.015625);
    self->control_value[2] = ((self->control[2] * 0.1875) - 12.0);
    v_scl_set(
        &self->soft_clipper,
        self->control_value[0],
        self->control_value[1],
        self->control_value[2]
    );
    v_scl_run(&self->soft_clipper, a_in0, a_in1);
    self->output0 = self->soft_clipper.output0;
    self->output1 = self->soft_clipper.output1;
}

void v_mf3_run_comb(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);

    // Freq
    self->control_value[0] = (((self->control[0]) * 0.692913386) + 20.0f);
    // Amt
    self->control_value[1] = ((self->control[1]) * 0.157480315) - 20.0f;

    v_cmb_set_all(
        &self->comb_filter0,
        self->control_value[1],
        self->control_value[1],
        self->control_value[0]
    );

    v_cmb_set_all(
        &self->comb_filter1,
        self->control_value[1],
        self->control_value[1],
        self->control_value[0]
    );

    v_cmb_run(&self->comb_filter0, a_in0);
    v_cmb_run(&self->comb_filter1, a_in1);

    self->output0 = self->comb_filter0.output_sample;
    self->output1 = self->comb_filter1.output_sample;
}

void v_mf3_run_phaser_static(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);

    // Freq: pitch 71 to 123
    self->control_value[0] = (((self->control[0]) * 0.40625) + 71.);
    // Wet -20dB to 0dB
    self->control_value[1] = ((self->control[1]) * 0.157480315) - 20.;
    // Feedback -20dB to -1dB
    self->control_value[2] = ((self->control[2]) * 0.1484375) - 20.;

    v_cmb_set_all(
        &self->comb_filter0,
        self->control_value[1],
        self->control_value[2],
        self->control_value[0]
    );

    v_cmb_set_all(
        &self->comb_filter1,
        self->control_value[1],
        self->control_value[2],
        self->control_value[0]
    );

    v_cmb_run(&self->comb_filter0, a_in0);
    v_cmb_run(&self->comb_filter1, a_in1);

    self->output0 = self->comb_filter0.output_sample;
    self->output1 = self->comb_filter1.output_sample;
}

void v_mf3_run_flanger_static(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);

    // Freq: pitch 20 to 83
    self->control_value[0] = (((self->control[0]) * 0.4921875) + 20.);
    // Wet -20dB to 0dB
    self->control_value[1] = ((self->control[1]) * 0.157480315) - 20.;
    // Feedback -20dB to -1dB
    self->control_value[2] = ((self->control[2]) * 0.1484375) - 20.;

    v_cmb_set_all(
        &self->comb_filter0,
        self->control_value[1],
        self->control_value[2],
        self->control_value[0]
    );

    v_cmb_set_all(
        &self->comb_filter1,
        self->control_value[1],
        self->control_value[2],
        self->control_value[0]
    );

    v_cmb_run(&self->comb_filter0, a_in0);
    v_cmb_run(&self->comb_filter1, a_in1);

    self->output0 = self->comb_filter0.output_sample;
    self->output1 = self->comb_filter1.output_sample;
}

void v_mf3_run_amp_panner(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);

    self->control_value[0] = ((self->control[0]) * 0.007874016f);
    self->control_value[1] = ((self->control[1]) * 0.503937f) - 40.0f;

    v_app_set(&self->amp_and_panner, (self->control_value[1]),
            (self->control_value[0]));
    v_app_run(&self->amp_and_panner, a_in0, a_in1);

    self->output0 = self->amp_and_panner.output0;
    self->output1 = self->amp_and_panner.output1;
}

void f_mfx_transform_svf_filter(t_mf3_multi* self){
    v_mf3_commit_mod(self);
    //cutoff
    self->control_value[0] = (((self->control[0]) * 0.818897638) + 20.0f);
    //res
    self->control_value[1] = ((self->control[1]) * 0.236220472) - 30.0f;

    v_svf2_set_cutoff_base(
        &self->svf,
        self->control_value[0]
    );
    v_svf2_set_res(
        &self->svf,
        self->control_value[1]
    );
    v_svf2_set_cutoff(&self->svf);
}


void v_mf3_run_limiter(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = (((self->control[0]) * 0.236220472f) - 30.0f);
    self->control_value[1] = (((self->control[1]) * 0.093700787f) - 11.9f);
    self->control_value[2] = (((self->control[2]) * 11.417322835f) + 50.0f);

    v_lim_set(&self->limiter, (self->control_value[0]),
            (self->control_value[1]), (self->control_value[2]));
    v_lim_run(&self->limiter, a_in0, a_in1);

    self->output0 = self->limiter.output0;
    self->output1 = self->limiter.output1;
}

void v_mf3_run_saturator(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.188976378) - 12.0f;
    self->control_value[1] = ((self->control[1]) * 0.748031496f) + 5.0f;
    self->control_value[2] = ((self->control[2]) * 0.188976378) - 12.0f;

    v_sat_set(&self->saturator, (self->control_value[0]),
            (self->control_value[1]), (self->control_value[2]));

    v_sat_run(&self->saturator, a_in0, a_in1);

    self->output0 = self->saturator.output0;
    self->output1 = self->saturator.output1;
}

void v_mf3_run_formant_filter(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.07086f);
    self->control_value[1] = ((self->control[1]) * 0.007874016f);

    v_for_formant_filter_set(&self->formant_filter, self->control_value[0],
            self->control_value[1]);
    v_for_formant_filter_run(&self->formant_filter, a_in0, a_in1);

    self->output0 = self->formant_filter.output0;
    self->output1 = self->formant_filter.output1;
}

void v_mf3_run_chorus(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.04488189f) + 0.3f;
    self->control_value[1] = ((self->control[1]) * 0.1889f) - 24.0f;
    self->control_value[2] = ((self->control[2]) * 0.0140625f) + 0.1f;

    v_crs_chorus_set(
        &self->chorus,
        self->control_value[0] * self->control_value[2],
        self->control_value[1]
    );
    v_crs_chorus_run(&self->chorus, a_in0, a_in1);

    self->output0 = self->chorus.output0;
    self->output1 = self->chorus.output1;
}

void v_mf3_run_glitch(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.62992126f) + 5.0f;
    self->control_value[1] = ((self->control[1]) * 0.08661f) + 1.1f;
    self->control_value[2] = ((self->control[2]) * 0.007874016f);

    v_glc_glitch_set(&self->glitch, self->control_value[0],
            self->control_value[1], self->control_value[2]);
    v_glc_glitch_run(&self->glitch, a_in0, a_in1);

    self->output0 = self->glitch.output0;
    self->output1 = self->glitch.output1;
}

void v_mf3_run_ring_mod(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.44094f) + 24.0f;
    self->control_value[1] = ((self->control[1]) * 0.007874f);

    v_rmd_ring_mod_set(
        &self->ring_mod,
        self->control_value[0],
        self->control_value[1]
    );
    v_rmd_ring_mod_run(&self->ring_mod, a_in0, a_in1);

    self->output0 = self->ring_mod.output0;
    self->output1 = self->ring_mod.output1;
}

void v_mf3_run_lofi(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.094488f) + 4.0f;

    v_lfi_lofi_set(&self->lofi, self->control_value[0]);
    v_lfi_lofi_run(&self->lofi, a_in0, a_in1);

    self->output0 = self->lofi.output0;
    self->output1 = self->lofi.output1;
}

void v_mf3_run_s_and_h(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.23622f) + 60.0f;
    self->control_value[1] = ((self->control[1]) * 0.007874016f);

    v_sah_sample_and_hold_set(&self->s_and_h, self->control_value[0],
            self->control_value[1]);
    v_sah_sample_and_hold_run(&self->s_and_h, a_in0, a_in1);

    self->output0 = self->s_and_h.output0;
    self->output1 = self->s_and_h.output1;
}


void v_mf3_run_lp_dw(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(&self->xfader, self->control_value[2]);
    v_svf2_run_2_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = f_axf_run_xfade(&self->xfader, a_in0, self->svf.output0);
    self->output1 = f_axf_run_xfade(&self->xfader, a_in1, self->svf.output1);
}

void v_mf3_run_bp_dw(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(
        &self->xfader,
        self->control_value[2]
    );
    v_svf2_run_2_pole_bp(
        &self->svf,
        a_in0,
        a_in1
    );
    self->output0 = f_axf_run_xfade(
        &self->xfader,
        a_in0,
        self->svf.output0
    );
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        a_in1,
        self->svf.output1
    );
}

void v_mf3_run_hp_dw(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(
        &self->xfader,
        self->control_value[2]
    );
    v_svf2_run_2_pole_hp(
        &self->svf,
        a_in0,
        a_in1
    );
    self->output0 = f_axf_run_xfade(
        &self->xfader,
        a_in0,
        self->svf.output0
    );
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        a_in1,
        self->svf.output1
    );
}

void v_mf3_run_notch_dw(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(
        &self->xfader,
        self->control_value[2]
    );
    v_svf2_run_4_pole_notch(
        &self->svf,
        a_in0,
        a_in1
    );
    self->output0 = f_axf_run_xfade(
        &self->xfader,
        a_in0,
        self->svf.output0
    );
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        a_in1,
        self->svf.output1
    );
}

void v_mf3_run_foldback(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    self->control_value[0] = ((self->control[0]) * 0.094488189f) - 12.0f;
    self->control_value[1] = ((self->control[1]) * 0.094488189f);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(&self->xfader, self->control_value[2]);
    v_fbk_set(
        &self->foldback,
        self->control_value[0],
        self->control_value[1]
    );
    v_fbk_run(&self->foldback, a_in0, a_in1);
    self->output0 = f_axf_run_xfade(
        &self->xfader,
        a_in0,
        self->foldback.output[0]
    );
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        a_in1,
        self->foldback.output[1]
    );
}

void v_mf3_run_monofier(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);

    self->control_value[0] = ((self->control[0]) * 0.007874016f);
    self->control_value[1] = ((self->control[1]) * 0.283464567f) - 30.0f;

    v_app_set(
        &self->amp_and_panner,
        self->control_value[1],
        self->control_value[0]
    );
    v_app_run_monofier(&self->amp_and_panner, a_in0, a_in1);

    self->output0 = self->amp_and_panner.output0;
    self->output1 = self->amp_and_panner.output1;
}

void v_mf3_run_lp_hp(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(&self->xfader, self->control_value[2]);
    v_svf2_run_2_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = f_axf_run_xfade(
        &self->xfader,
        self->svf.filter_kernels[0][0].lp,
        self->svf.filter_kernels[0][0].hp
    );
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        self->svf.filter_kernels[0][1].lp,
        self->svf.filter_kernels[0][1].hp
    );
}

void v_mf3_run_growl_filter(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.0390625f);
    self->control_value[1] = ((self->control[1]) * 0.007874016f);
    self->control_value[2] = ((self->control[2]) * 0.15625f);

    v_grw_growl_filter_set(
        &self->growl_filter,
        self->control_value[0],
        self->control_value[1],
        self->control_value[2]
    );
    v_grw_growl_filter_run(&self->growl_filter, a_in0, a_in1);

    self->output0 = self->growl_filter.output0;
    self->output1 = self->growl_filter.output1;
}

void v_mf3_run_screech_lp(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    f_mfx_transform_svf_filter(self);
    v_svf2_run_4_pole_lp(&self->svf, a_in0, a_in1);

    //self->output0 = self->svf->output0;
    //self->output1 = self->svf->output1;

    v_clp_set_clip_sym(&self->clipper, -3.0f);
    v_sat_set(&self->saturator, 0.0f, 100.0f, 0.0f);
    v_sat_run(&self->saturator, self->svf.output0, self->svf.output1);

    //cutoff
    //self->control_value[0] = (((self->control[0]) * 0.692913386) + 20.0f);
    //res
    //self->control_value[1] = ((self->control[1]) * 0.157480315) - 24.0f;

    v_cmb_set_all(
        &self->comb_filter0,
        self->control_value[1],
        self->control_value[1],
        self->control_value[0]
    );

    v_cmb_set_all(
        &self->comb_filter1,
        self->control_value[1],
        self->control_value[1],
        self->control_value[0]
    );

    v_cmb_run(
        &self->comb_filter0,
        f_clp_clip(
            &self->clipper,
            self->saturator.output0
        )
    );
    v_cmb_run(
        &self->comb_filter1,
        f_clp_clip(
            &self->clipper,
            self->saturator.output1
        )
    );

    self->output0 = (self->saturator.output0 -
        self->comb_filter0.wet_sample);
    self->output1 = (self->saturator.output1 -
        self->comb_filter1.wet_sample);
}


void v_mf3_run_metal_comb(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf3_commit_mod(self);

    //cutoff
    self->control_value[0] = (((self->control[0]) * 0.24) + 30.0f);
    //res
    self->control_value[1] = ((self->control[1]) * 0.157480315) - 20.0f;
    //detune
    self->control_value[2] = ((self->control[2]) * 0.02362f) + 1.0f;

    v_cmb_mc_set_all(
        &self->comb_filter0,
        self->control_value[1],
        self->control_value[0],
        self->control_value[2]
    );

    v_cmb_mc_set_all(
        &self->comb_filter1,
        self->control_value[1],
        self->control_value[0],
        self->control_value[2]
    );

    v_cmb_mc_run(&self->comb_filter0, a_in0);
    v_cmb_mc_run(&self->comb_filter1, a_in1);

    self->output0 = (self->comb_filter0.output_sample);
    self->output1 = (self->comb_filter1.output_sample);
}

void v_mf3_run_dc_offset(
    t_mf3_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    // No knobs
    self->output0 = f_dco_run(&self->dc_offset[0], a_in0);
    self->output1 = f_dco_run(&self->dc_offset[1], a_in1);
}

void v_mf3_run_ladder4(t_mf3_multi* self, SGFLT left, SGFLT right){
    v_mf3_commit_mod(self);
    //cutoff
    self->control_value[0] = (((self->control[0]) * 0.818897638) + 20.0f);
    //res
    self->control_value[1] = ((self->control[1]) * 0.236220472) - 30.0f;
    ladder_set(
        &self->ladder,
        self->control_value[0],
        self->control_value[1]
    );
    struct SamplePair result = ladder_run_stereo(
        &self->ladder,
        (struct SamplePair){
            .left = left,
            .right = right,
        }
    );
    self->output0 = result.left;
    self->output1 = result.right;
}

void g_mf3_init(
    t_mf3_multi * f_result,
    SGFLT a_sample_rate,
    int a_huge_pages
){
    f_result->effect_index = 0;
    f_result->channels = 2;
    g_svf2_init(&f_result->svf, a_sample_rate);
    g_svf2_init(&f_result->svf2, a_sample_rate);
    ladder_init(&f_result->ladder, a_sample_rate);
    g_cmb_init(&f_result->comb_filter0, a_sample_rate, a_huge_pages);
    g_cmb_init(&f_result->comb_filter1, a_sample_rate, a_huge_pages);
    g_pkq_init(&f_result->eq0, a_sample_rate);
    g_clp_init(&f_result->clipper);
    v_clp_set_clip_sym(&f_result->clipper, -3.0f);
    g_lim_init(&f_result->limiter, a_sample_rate, a_huge_pages);
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->control[0] = 0.0f;
    f_result->control[1] = 0.0f;
    f_result->control[2] = 0.0f;
    f_result->control_value[0] = 65.0f;
    f_result->control_value[1] = 65.0f;
    f_result->control_value[2] = 65.0f;
    f_result->mod_value[0] = 0.0f;
    f_result->mod_value[1] = 0.0f;
    f_result->mod_value[2] = 0.0f;
    g_axf_init(&f_result->xfader, -3.0f);
    f_result->outgain = 1.0f;
    g_app_init(&f_result->amp_and_panner);
    g_sat_init(&f_result->saturator);
    g_for_init(&f_result->formant_filter, a_sample_rate);
    g_crs_init(&f_result->chorus, a_sample_rate, a_huge_pages);
    g_glc_init(&f_result->glitch, a_sample_rate);
    g_rmd_init(&f_result->ring_mod, a_sample_rate);
    g_lfi_init(&f_result->lofi);
    g_sah_init(&f_result->s_and_h, a_sample_rate);
    g_grw_init(&f_result->growl_filter, a_sample_rate);
    g_fbk_init(&f_result->foldback);
    g_dco_init(&f_result->dc_offset[0], a_sample_rate);
    g_dco_init(&f_result->dc_offset[1], a_sample_rate);
    soft_clipper_init(&f_result->soft_clipper);
}

/* t_mf3_multi g_mf3_get(
 * SGFLT a_sample_rate)
 */
t_mf3_multi * g_mf3_get(SGFLT a_sample_rate){
    t_mf3_multi * f_result;

    lmalloc((void**)&f_result, sizeof(t_mf3_multi));
    g_mf3_init(f_result, a_sample_rate, 0);

    return f_result;
}

void v_mf3_free(t_mf3_multi * self ){
    if(self){
        v_crs_free(&self->chorus);
        v_cmb_free(&self->comb_filter0);
        v_cmb_free(&self->comb_filter1);
        v_glc_glitch_free(&self->glitch);
        v_lim_free(&self->limiter);
        free(self);
    }
}

