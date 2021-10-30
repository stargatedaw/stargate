#include "audiodsp/modules/distortion/clipper.h"
#include "audiodsp/modules/distortion/foldback.h"
#include "audiodsp/modules/distortion/multi.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"



SGFLT f_multi_dist_off(t_mds_multidist* self, SGFLT a_sample, SGFLT a_out)
{
    return a_sample;
}

SGFLT f_multi_dist_clip(t_mds_multidist* self, SGFLT a_sample, SGFLT a_out)
{
    return f_axf_run_xfade(&self->dist_dry_wet, a_sample,
        f_clp_clip(&self->clipper1, a_sample * self->gain) * a_out);
}

SGFLT f_multi_dist_foldback(t_mds_multidist* self, SGFLT a_sample, SGFLT a_out)
{
    return f_axf_run_xfade(&self->dist_dry_wet, a_sample,
        f_fbk_mono(a_sample * self->gain) * a_out);
}

SG_THREAD_LOCAL fp_multi_dist MULTI_DIST_FP[]
 = {
    f_multi_dist_off, f_multi_dist_clip, f_multi_dist_foldback
};

fp_multi_dist g_mds_get_fp(int index)
{
    sg_assert(
        index >= 0 && index <= 2,
        "g_mds_get_fp: index %i out of range 0 to 2",
        index
    );
    return MULTI_DIST_FP[index];
}

void v_mds_set_gain(t_mds_multidist * self, SGFLT a_db)
{
    if((self->in_db) != a_db)
    {
        self->in_db = a_db;
        self->gain = f_db_to_linear(a_db);
    }
}

void g_mds_init(t_mds_multidist * self)
{
    self->gain = 1.0f;
    self->in_db = -12345.068f;
    g_clp_init(&self->clipper1);
    g_axf_init(&self->dist_dry_wet, -3.0f);
}

