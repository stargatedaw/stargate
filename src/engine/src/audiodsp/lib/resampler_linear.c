#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/resampler_linear.h"

void resampler_linear_init(
    struct ResamplerLinear* self,
    int internal_rate,
    int target_rate,
    resample_generate func
){
    self->func = func;
    self->same = internal_rate == target_rate;
    self->first = 1;
    self->pos = 0.0;
    resampler_stereo_pair_init(&self->previous);
    resampler_stereo_pair_init(&self->next);
    self->inc = (double)internal_rate / (double)target_rate;
}

struct ResamplerStereoPair resampler_linear_run(
    struct ResamplerLinear* self,
    void* func_arg
){
    struct ResamplerStereoPair result;

    if(self->same){
        return self->func(func_arg);
    }
    if(unlikely(self->first)){
        self->previous = self->func(func_arg);
        self->next = self->func(func_arg);
        self->first = 0;
    }
    result.left = f_linear_interpolate(
        self->previous.left,
        self->next.left,
        self->pos
    );
    result.right = f_linear_interpolate(
        self->previous.right,
        self->next.right,
        self->pos
    );
    self->pos += self->inc;
    while(self->pos >= 1.0){
        self->previous = self->next;
        self->next = self->func(func_arg);
        self->pos -= 1.0;
    }
    return result;
}

void resampler_linear_reset(
    struct ResamplerLinear* self
){
    self->first = 1;
    self->pos = 0.0;
}

void resampler_stereo_pair_init(
    struct ResamplerStereoPair* self
){
    self->left = 0.0;
    self->right = 0.0;
}
