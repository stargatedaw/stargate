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
#include "audiodsp/modules/multifx/multifx10knob.h"
#include "audiodsp/modules/signal_routing/amp_and_panner.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"

SG_THREAD_LOCAL const struct MultiFX10MetaData
MULTIFX10_METADATA[MULTIFX10KNOB_FX_COUNT] = {
    {
        v_mf10_run_off,
        v_mf10_reset_null,
        0,
    }, // 0
    {
        v_mf10_run_lp2,
        v_mf10_reset_svf,
        2,
    }, // 1
    {
        v_mf10_run_lp4,
        v_mf10_reset_svf,
        2,
    }, // 2
    {
        v_mf10_run_hp2,
        v_mf10_reset_svf,
        2,
    }, //3
    {
        v_mf10_run_hp4,
        v_mf10_reset_svf,
        2,
    }, //4
    {
        v_mf10_run_bp2,
        v_mf10_reset_svf,
        2,
    },//5
    {
        v_mf10_run_bp4,
        v_mf10_reset_svf,
        2,
    }, //6
    {
        v_mf10_run_notch2,
        v_mf10_reset_svf,
        2,
    }, //7
    {
        v_mf10_run_notch4,
        v_mf10_reset_svf,
        2,
    }, //8
    {
        v_mf10_run_eq,
        v_mf10_reset_null,
        3,
    }, //9
    {
        v_mf10_run_dist,
        v_mf10_reset_null,
        3,
    }, //10
    {
        v_mf10_run_comb,
        v_mf10_reset_null,
        2,
    }, //11
    {
        v_mf10_run_amp_panner,
        v_mf10_reset_null,
        2,
    }, //12
    {
        v_mf10_run_limiter,
        v_mf10_reset_null,
        3,
    }, //13
    {
        v_mf10_run_saturator,
        v_mf10_reset_null,
        3,
    }, //14
    {
        v_mf10_run_formant_filter,
        v_mf10_reset_null,
        2,
    }, //15
    {
        v_mf10_run_chorus,
        v_mf10_reset_null,
        3,
    }, //16
    {
        v_mf10_run_glitch,
        v_mf10_reset_glitch,
        3,
    }, //17
    {
        v_mf10_run_ring_mod,
        v_mf10_reset_null,
        2,
    }, //18
    {
        v_mf10_run_lofi,
        v_mf10_reset_null,
        1,
    }, //19
    {
        v_mf10_run_s_and_h,
        v_mf10_reset_null,
        2,
    }, //20
    {
        v_mf10_run_lp_dw,
        v_mf10_reset_svf,
        3,
    }, //21
    {
        v_mf10_run_hp_dw,
        v_mf10_reset_svf,
        3,
    }, //22
    {
        v_mf10_run_monofier,
        v_mf10_reset_null,
        2,
    }, //23
    {
        v_mf10_run_lp_hp,
        v_mf10_reset_svf,
        3,
    }, //24
    {
        v_mf10_run_growl_filter,
        v_mf10_reset_null,
        3,
    }, //25
    {
        v_mf10_run_screech_lp,
        v_mf10_reset_svf,
        2,
    }, //26
    {
        v_mf10_run_metal_comb,
        v_mf10_reset_null,
        3,
    }, //27
    {
        v_mf10_run_notch_dw,
        v_mf10_reset_svf,
        3,
    }, //28
    {
        v_mf10_run_foldback,
        v_mf10_reset_null,
        3,
    }, //29
    {
        v_mf10_run_notch_spread,
        v_mf10_reset_svf,
        3,
    }, //30
    {
        v_mf10_run_dc_offset,
        v_mf10_reset_dc_offset,
        0,
    }, //31
    {
        v_mf10_run_bp_spread,
        v_mf10_reset_svf,
        3,
    }, //32
    {
        v_mf10_run_phaser_static,
        v_mf10_reset_null,
        3,
    }, //33
    {
        v_mf10_run_flanger_static,
        v_mf10_reset_null,
        3,
    }, //34
    {
        v_mf10_run_soft_clipper,
        v_mf10_reset_null,
        3,
    }, //35
    {
        v_mf10_run_compressor,
        v_mf10_reset_null,
        6,
    }, // 36
    {
        v_mf10_run_bp_dw,
        v_mf10_reset_svf,
        3,
    }, //37
    {
        v_mf10_run_ladder4,
        v_mf10_reset_null,
        2,
    }, //38
};

void v_mf10_reset_null(t_mf10_multi* self){
    //do nothing
}

void v_mf10_reset_svf(t_mf10_multi* self){
    v_svf2_reset(&self->svf);
    v_svf2_reset(&self->svf2);
}

void v_mf10_reset_glitch(t_mf10_multi* self){
    v_glc_glitch_retrigger(&self->glitch);
}

void v_mf10_reset_dc_offset(t_mf10_multi* self){
    v_dco_reset(&self->dc_offset[0]);
    v_dco_reset(&self->dc_offset[1]);
}

struct MultiFX10MetaData mf10_get_meta(int index){
    return MULTIFX10_METADATA[index];
}

void v_mf10_set(
    t_mf10_multi* self,
    SGFLT controls[MULTIFX10KNOB_KNOB_COUNT],
    int knob_count
){
    int i;
    for(i = 0; i < knob_count; ++i){
        self->control[i] = controls[i];
        self->mod_value[i] = 0.0f;
    }
}

void v_mf10_set_from_smoothers(
    t_mf10_multi* self,
    t_smoother_linear smoothers[MULTIFX10KNOB_KNOB_COUNT],
    int knob_count
){
    int i;
    for(i = 0; i < knob_count; ++i){
        self->control[i] = smoothers[i].last_value * 0.1;
        self->mod_value[i] = 0.0f;
    }
}

int mf10_routing_plan_set(
    struct MultiFX10RoutingPlan* plan,
    struct MultiFX10MonoCluster* fx,
    struct SamplePair* output,
    int fx_count
){
    int i, index, route;
    struct MultiFX10MonoCluster* cluster;
    int result = 0;
    int fx_num;
    int active_fx[fx_count];
    int routes[fx_count];
    int routed_to[fx_count + 1];

    for(i = 0; i < fx_count + 1; ++i){
        routed_to[i] = 0;
    }

    plan->active_fx_count = 0;

    for(i = 0; i < fx_count; ++i){
        cluster = &fx[i];
        index = (int)(*(cluster->controls.type));
        cluster->fx_index = index;
        cluster->meta = mf10_get_meta(index);

        if(index){
            route = (int)(*(cluster->controls.route)) + i + 1;
            routes[plan->active_fx_count] = route;
            routed_to[route] = 1;
            active_fx[i] = 1;
            result = 1;
            plan->steps[plan->active_fx_count] = cluster;
            ++plan->active_fx_count;
        } else {
            active_fx[i] = 0;
        }
        // Because routing only goes forward, never backwards
        if(routed_to[i]){
            cluster->input_main = 0;
        } else {
            cluster->input_main = 1;
        }
    }

    for(i = 0; i < plan->active_fx_count; ++i){
        fx_num = routes[i];
        if(
            fx_num == fx_count
            ||
            active_fx[routes[i]] == 0
        ){
            plan->steps[i]->output = output;
        } else {
            plan->steps[i]->output = &fx[fx_num].input;
        }
    }
    return result;
}

void v_mf10_mod(
    t_mf10_multi* self,
    SGFLT a_mod,
    SGFLT a_amt0,
    SGFLT a_amt1,
    SGFLT a_amt2
){
    self->mod_value[0] = (self->mod_value[0]) + (a_mod * a_amt0 * .01f);
    self->mod_value[1] = (self->mod_value[1]) + (a_mod * a_amt1 * .01f);
    self->mod_value[2] = (self->mod_value[2]) + (a_mod * a_amt2 * .01f);
}

/* void v_mf10_mod_single(
 * t_mf10_multi* self,
 * SGFLT a_mod, //The output of the LFO, etc...  -1.0f to 1.0f
 * SGFLT a_amt, //amount, -1.0f to 1.0f
 * int a_index)  //control index
 */
void v_mf10_mod_single(
    t_mf10_multi* self,
    SGFLT a_mod,
    SGFLT a_amt,
    int a_index
){
    //not  * .01 because it's expected you did this at note_on
    self->mod_value[a_index] = (self->mod_value[a_index]) + (a_mod * a_amt);
}

void v_mf10_commit_mod(t_mf10_multi* self){
    int i;

    for(i = 0; i < MULTIFX10KNOB_KNOB_COUNT; ++i){
        self->control[i] =
            self->control[i] + (self->mod_value[i] * 127.0f);

        if(self->control[i] > 127.0f){
            self->control[i] = 127.0f;
        } else if(self->control[i] < 0.0f){
            self->control[i] = 0.0f;
        }
    }
}

void v_mf10_run_off(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    self->output0 = a_in0;
    self->output1 = a_in1;
}

void v_mf10_run_lp2(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_2_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_lp4(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_4_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_hp2(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_2_pole_hp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_hp4(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_4_pole_hp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_bp2(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_2_pole_bp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_bp4(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_4_pole_bp(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_notch2(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_2_pole_notch(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_notch4(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    v_svf2_run_4_pole_notch(&self->svf, a_in0, a_in1);
    self->output0 = self->svf.output0;
    self->output1 = self->svf.output1;
}

void v_mf10_run_notch_spread(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
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

void v_mf10_run_bp_spread(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
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

void v_mf10_run_eq(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
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

void v_mf10_run_dist(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    SGFLT outgain;
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.377952756f);
    self->control_value[1] = ((self->control[1]) * 0.007874016f);
    self->control_value[2] = (((self->control[2]) * 0.236220472f) - 30.0f);
    outgain = f_db_to_linear(self->control_value[2]);
    v_clp_set_in_gain(&self->clipper, (self->control_value[0]));
    v_axf_set_xfade(&self->xfader, (self->control_value[1]));

    self->output0 = f_axf_run_xfade(
        &self->xfader,
        a_in0,
        f_clp_clip(&self->clipper, a_in0)
    ) * outgain;
    self->output1 = f_axf_run_xfade(
        &self->xfader,
        a_in1,
        f_clp_clip(&self->clipper, a_in1)
    ) * outgain;
}

void v_mf10_run_soft_clipper(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
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

void v_mf10_run_comb(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);

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

void v_mf10_run_phaser_static(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);

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

void v_mf10_run_flanger_static(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);

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

void v_mf10_run_amp_panner(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);

    self->control_value[0] = (self->control[0] * 0.007874016f);
    self->control_value[1] = (self->control[1] * 0.503937f) - 40.0f;

    v_app_set(
        &self->amp_and_panner,
        self->control_value[1],
        self->control_value[0]
    );
    v_app_run(&self->amp_and_panner, a_in0, a_in1);

    self->output0 = self->amp_and_panner.output0;
    self->output1 = self->amp_and_panner.output1;
}

void mf10_transform_svf_filter(t_mf10_multi* self){
    v_mf10_commit_mod(self);
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

void v_mf10_run_compressor(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    // threshold
    self->control_value[0] = (self->control[0] * 0.236220472) - 36.0;
    // ratio
    self->control_value[1] = (self->control[1] * 0.070866142) + 1.0;
    // Knee
    self->control_value[2] = self->control[2] * 0.094488189;
    // attack
    self->control_value[3] = self->control[3] * 0.003937008;
    // release
    self->control_value[4] = (self->control[4] * 0.003858268) + 10.0;
    // gain
    self->control_value[5] = (self->control[5] * 0.566929134) - 36.0;

    v_cmp_set(
        &self->compressor,
        self->control_value[0],
        self->control_value[1],
        self->control_value[2],
        self->control_value[3],
        self->control_value[4],
        self->control_value[5]
    );
    v_cmp_run(&self->compressor, a_in0, a_in1);

    self->output0 = self->compressor.output0 * self->compressor.gain_lin;
    self->output1 = self->compressor.output1 * self->compressor.gain_lin;
}

void v_mf10_run_limiter(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = (((self->control[0]) * 0.236220472f) - 30.0f);
    self->control_value[1] = (((self->control[1]) * 0.093700787f) - 11.9f);
    self->control_value[2] = (((self->control[2]) * 11.417322835f) + 50.0f);

    v_lim_set(
        &self->limiter,
        self->control_value[0],
        self->control_value[1],
        self->control_value[2]
    );
    v_lim_run(&self->limiter, a_in0, a_in1);

    self->output0 = self->limiter.output0;
    self->output1 = self->limiter.output1;
}

void v_mf10_run_saturator(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.188976378) - 12.0f;
    self->control_value[1] = ((self->control[1]) * 0.748031496f) + 5.0f;
    self->control_value[2] = ((self->control[2]) * 0.188976378) - 12.0f;

    v_sat_set(&self->saturator, (self->control_value[0]),
            (self->control_value[1]), (self->control_value[2]));

    v_sat_run(&self->saturator, a_in0, a_in1);

    self->output0 = self->saturator.output0;
    self->output1 = self->saturator.output1;
}

void v_mf10_run_formant_filter(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.07086f);
    self->control_value[1] = ((self->control[1]) * 0.007874016f);

    v_for_formant_filter_set(&self->formant_filter, self->control_value[0],
            self->control_value[1]);
    v_for_formant_filter_run(&self->formant_filter, a_in0, a_in1);

    self->output0 = self->formant_filter.output0;
    self->output1 = self->formant_filter.output1;
}

void v_mf10_run_chorus(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.04488189f) + 0.3f;
    self->control_value[1] = ((self->control[1]) * 0.0140625f) + 0.1f;
    self->control_value[2] = ((self->control[2]) * 0.1889f) - 24.0f;

    v_crs_chorus_set(
        &self->chorus,
        self->control_value[0] * self->control_value[1],
        self->control_value[2]
    );
    v_crs_chorus_run(&self->chorus, a_in0, a_in1);

    self->output0 = self->chorus.output0;
    self->output1 = self->chorus.output1;
}

void v_mf10_run_glitch(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.62992126f) + 5.0f;
    self->control_value[1] = ((self->control[1]) * 0.08661f) + 1.1f;
    self->control_value[2] = ((self->control[2]) * 0.007874016f);

    v_glc_glitch_set(&self->glitch, self->control_value[0],
            self->control_value[1], self->control_value[2]);
    v_glc_glitch_run(&self->glitch, a_in0, a_in1);

    self->output0 = self->glitch.output0;
    self->output1 = self->glitch.output1;
}

void v_mf10_run_ring_mod(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
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

void v_mf10_run_lofi(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.094488f) + 4.0f;

    v_lfi_lofi_set(&self->lofi, self->control_value[0]);
    v_lfi_lofi_run(&self->lofi, a_in0, a_in1);

    self->output0 = self->lofi.output0;
    self->output1 = self->lofi.output1;
}

void v_mf10_run_s_and_h(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
    self->control_value[0] = ((self->control[0]) * 0.23622f) + 60.0f;
    self->control_value[1] = ((self->control[1]) * 0.007874016f);

    v_sah_sample_and_hold_set(&self->s_and_h, self->control_value[0],
            self->control_value[1]);
    v_sah_sample_and_hold_run(&self->s_and_h, a_in0, a_in1);

    self->output0 = self->s_and_h.output0;
    self->output1 = self->s_and_h.output1;
}


void v_mf10_run_lp_dw(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
    self->control_value[2] = self->control[2] * 0.007874016f;
    v_axf_set_xfade(&self->xfader, self->control_value[2]);
    v_svf2_run_2_pole_lp(&self->svf, a_in0, a_in1);
    self->output0 = f_axf_run_xfade(&self->xfader, a_in0, self->svf.output0);
    self->output1 = f_axf_run_xfade(&self->xfader, a_in1, self->svf.output1);
}

void v_mf10_run_bp_dw(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
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

void v_mf10_run_hp_dw(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
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

void v_mf10_run_notch_dw(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
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

void v_mf10_run_foldback(
    t_mf10_multi* self,
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

void v_mf10_run_monofier(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);

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

void v_mf10_run_lp_hp(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
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

void v_mf10_run_growl_filter(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);
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

void v_mf10_run_screech_lp(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    mf10_transform_svf_filter(self);
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


void v_mf10_run_metal_comb(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_mf10_commit_mod(self);

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

void v_mf10_run_dc_offset(
    t_mf10_multi* self,
    SGFLT a_in0,
    SGFLT a_in1
){
    // No knobs
    self->output0 = f_dco_run(&self->dc_offset[0], a_in0);
    self->output1 = f_dco_run(&self->dc_offset[1], a_in1);
}

void v_mf10_run_ladder4(t_mf10_multi* self, SGFLT left, SGFLT right){
    v_mf10_commit_mod(self);
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

void g_mf10_init(
    t_mf10_multi * self,
    SGFLT a_sample_rate,
    int a_huge_pages
){
    int i;

    for(i = 0; i < MULTIFX10KNOB_KNOB_COUNT; ++i){
        self->control[i] = 0.0f;
        self->control_value[i] = 64.0f;
        self->mod_value[i] = 0.0f;
    }
    g_svf2_init(&self->svf, a_sample_rate);
    g_svf2_init(&self->svf2, a_sample_rate);
    ladder_init(&self->ladder, a_sample_rate);
    g_cmb_init(&self->comb_filter0, a_sample_rate, a_huge_pages);
    g_cmb_init(&self->comb_filter1, a_sample_rate, a_huge_pages);
    g_pkq_init(&self->eq0, a_sample_rate);
    g_clp_init(&self->clipper);
    v_clp_set_clip_sym(&self->clipper, -3.0f);
    g_lim_init(&self->limiter, a_sample_rate, a_huge_pages);
    g_cmp_init(&self->compressor, a_sample_rate);
    self->output0 = 0.0f;
    self->output1 = 0.0f;
    g_axf_init(&self->xfader, -3.0f);
    g_app_init(&self->amp_and_panner);
    g_sat_init(&self->saturator);
    g_for_init(&self->formant_filter, a_sample_rate);
    g_crs_init(&self->chorus, a_sample_rate, a_huge_pages);
    g_glc_init(&self->glitch, a_sample_rate);
    g_rmd_init(&self->ring_mod, a_sample_rate);
    g_lfi_init(&self->lofi);
    g_sah_init(&self->s_and_h, a_sample_rate);
    g_grw_init(&self->growl_filter, a_sample_rate);
    g_fbk_init(&self->foldback);
    g_dco_init(&self->dc_offset[0], a_sample_rate);
    g_dco_init(&self->dc_offset[1], a_sample_rate);
    soft_clipper_init(&self->soft_clipper);
}

void mf10_mono_cluster_init(
    struct MultiFX10MonoCluster* self,
    SGFLT sr,
    int index
){
    int i;
    g_mf10_init(&self->mf10, sr, 1);
    dry_wet_pan_init(&self->dry_wet_pan);
    self->fx_index = 0;
    self->mf10_index = index;
    self->meta.run = v_mf10_run_off;
    g_pkm_init(&self->input_peak);
    g_pkm_init(&self->output_peak);
    for(i = 0; i < MULTIFX10KNOB_KNOB_COUNT; ++i){
        g_sml_init(&self->smoothers[i], sr, 1270.0f, 0.0f, 0.05f);
    }
    g_sml_init(&self->dry_smoother, sr, 120.0f, -400.0f, 0.05f);
    g_sml_init(&self->wet_smoother, sr, 120.0f, -400.0f, 0.05f);
    g_sml_init(&self->pan_smoother, sr, 100.0f, -100.0f, 0.05f);
}

void v_mf10_free(t_mf10_multi * self ){
    if(self){
        v_crs_free(&self->chorus);
        v_cmb_free(&self->comb_filter0);
        v_cmb_free(&self->comb_filter1);
        v_glc_glitch_free(&self->glitch);
        v_lim_free(&self->limiter);
        // free(self);
    }
}

