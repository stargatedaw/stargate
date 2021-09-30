#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/resampler_linear.h"

void resampler_linear_init(
    struct ResamplerLinear* self,
    int internal_rate,
    int target_rate,
    resample_generate func,
    void* func_arg
){
    self->func = func;
    self->func_arg = func_arg;
    self->same = internal_rate == target_rate;
    self->first = 1;
    self->pos = 0.0;
    self->previous = 0.0;
    self->next = 0.0;
    self->inc = (double)internal_rate / (double)target_rate;
}

SGFLT resampler_linear_run_mono(
    struct ResamplerLinear* self
){
    SGFLT result;

    if(self->same){
        return self->func(self->func_arg);
    }
    if(unlikely(self->first)){
        self->previous = self->func(self->func_arg);
        self->next = self->func(self->func_arg);
        self->first = 0;
    }
    result = f_linear_interpolate(
        self->previous,
        self->next,
        self->pos
    );
    self->pos += self->inc;
    while(self->pos >= 1.0){
        self->previous = self->next;
        self->next = self->func(self->func_arg);
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
