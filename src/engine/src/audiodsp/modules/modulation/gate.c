#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/modulation/gate.h"


/*
 *  void v_gat_set(t_gat_gate* a_gat, SGFLT a_pitch)
 */
void v_gat_set(t_gat_gate* a_gat, SGFLT a_pitch, SGFLT a_wet)
{
    if(a_pitch != a_gat->last_cutoff)
    {
        a_gat->last_cutoff = a_pitch;
        v_svf_set_cutoff_base(&a_gat->svf, a_pitch);
        v_svf_set_cutoff(&a_gat->svf);
    }

    if(a_wet != a_gat->last_wet)
    {
        a_gat->last_wet = a_wet;
        v_axf_set_xfade(&a_gat->xfade, a_wet);
    }
}

/*
 * void v_gat_run(t_gat_gate * a_gat, SGFLT a_on, SGFLT a_in0, SGFLT a_in1)
 */
void v_gat_run(t_gat_gate * a_gat, SGFLT a_on, SGFLT a_in0, SGFLT a_in1)
{
    a_gat->value = v_svf_run_2_pole_lp(&a_gat->svf, a_on);

    a_gat->output[0] = f_axf_run_xfade(
            &a_gat->xfade, a_in0, a_gat->value * a_in0);
    a_gat->output[1] = f_axf_run_xfade(
            &a_gat->xfade, a_in1, a_gat->value * a_in1);
}

void g_gat_init(t_gat_gate * f_result, SGFLT a_sr)
{
    f_result->value = 0.0f;
    f_result->output[0] = 0.0f;
    f_result->output[1] = 0.0f;
    f_result->last_cutoff = 6699.0f;
    f_result->last_wet = -3210.0f;
    g_svf_init(&f_result->svf, a_sr);

    g_axf_init(&f_result->xfade, -3.0f);

    v_svf_set_cutoff_base(&f_result->svf, 66.0f);
    v_svf_set_res(&f_result->svf, -12.0f);
    v_svf_set_cutoff(&f_result->svf);
}

