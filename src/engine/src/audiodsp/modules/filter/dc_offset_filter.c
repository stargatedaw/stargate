#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/filter/dc_offset_filter.h"


SGFLT f_dco_run(t_dco_dc_offset_filter* a_dco,SGFLT a_in){
    SGFLT output =
        (a_in - (a_dco->in_n_m1)) + ((a_dco->out_n_m1) * (a_dco->coeff));
    output = f_remove_denormal(output);

    a_dco->in_n_m1 = a_in;
    a_dco->out_n_m1 = (output);

    return output;
}

void v_dco_reset(t_dco_dc_offset_filter* a_dco){
    a_dco->in_n_m1 = 0.0f;
    a_dco->out_n_m1 = 0.0f;
}

void g_dco_init(t_dco_dc_offset_filter * f_result, SGFLT a_sr){
    f_result->coeff = (1.0f - (6.6f/a_sr));
    v_dco_reset(f_result);
}


t_dco_dc_offset_filter * g_dco_get(SGFLT a_sr)
{
    t_dco_dc_offset_filter * f_result;
    lmalloc((void**)&f_result, sizeof(t_dco_dc_offset_filter));

    g_dco_init(f_result, a_sr);

    return f_result;
}

void stereo_dc_filter_init(struct StereoDCFilter* self, SGFLT sr){
    g_dco_init(&self->left, sr);
    g_dco_init(&self->right, sr);
}

void stereo_dc_filter_reset(struct StereoDCFilter* self){
    v_dco_reset(&self->left);
    v_dco_reset(&self->right);
}

struct SamplePair stereo_dc_filter_run(
    struct StereoDCFilter* self,
    struct SamplePair input
){
    struct SamplePair result = (struct SamplePair){
        .left = f_dco_run(&self->left, input.left),
        .right = f_dco_run(&self->right, input.right),
    };

    return result;
}
