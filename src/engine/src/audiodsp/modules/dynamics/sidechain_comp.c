#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/lib/peak_meter.h"
#include "audiodsp/modules/dynamics/sidechain_comp.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/env_follower2.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


void g_scc_init(t_scc_sidechain_comp * self, SGFLT a_sr)
{
    g_enf_init(&self->env_follower, a_sr);
    g_axf_init(&self->xfade, -3.0f);
    self->attack = 999.99f;
    self->release = 999.99f;
    self->pitch = 999.99f;
    self->ratio = 999.99f;
    self->thresh = 999.99f;
    self->wet = 999.99f;
    g_svf_init(&self->filter, a_sr);
    v_svf_set_cutoff_base(&self->filter, 66.0f);
    v_svf_set_res(&self->filter, -24.0f);
    v_svf_set_cutoff(&self->filter);
    self->output0 = 0.0f;
    self->output1 = 0.0f;
    g_pkm_redux_init(&self->peak_tracker, a_sr);
}

void v_scc_set(
    t_scc_sidechain_comp *self,
    SGFLT a_thresh,
    SGFLT a_ratio,
    SGFLT a_attack,
    SGFLT a_release,
    SGFLT a_wet
){
    self->thresh = a_thresh;
    self->ratio = a_ratio;

    if(self->attack != a_attack || self->release != a_release)
    {
        self->attack = a_attack;
        self->release = a_release;
        v_enf_set(&self->env_follower, a_attack, a_release);
    }

    if(self->wet != a_wet)
    {
        self->wet = a_wet;
        v_axf_set_xfade(&self->xfade, a_wet);
    }
}

void v_scc_run_comp(
    t_scc_sidechain_comp* self,
    SGFLT a_input0,
    SGFLT a_input1,
    SGFLT a_output0,
    SGFLT a_output1
){
    SGFLT f_gain;

    v_enf_run(
        &self->env_follower,
        f_sg_max(f_sg_abs(a_input0), f_sg_abs(a_input1))
    );

    f_gain = self->thresh - f_linear_to_db_fast(self->env_follower.envelope);

    if(f_gain < 0.0f)
    {
        f_gain *= self->ratio;
        f_gain = f_db_to_linear_fast(f_gain);
        f_gain = v_svf_run_4_pole_lp(&self->filter, f_gain);

        self->output0 = f_axf_run_xfade(
            &self->xfade,
            a_output0,
            a_output0 * f_gain
        );
        self->output1 = f_axf_run_xfade(
            &self->xfade,
            a_output1,
            a_output1 * f_gain
        );
        v_pkm_redux_run(&self->peak_tracker, f_gain);
    } else {
        self->output0 = a_output0;
        self->output1 = a_output1;
        v_pkm_redux_run(&self->peak_tracker, 1.0f);
    }
}
