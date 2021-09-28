#ifndef RESAMPLER_LINEAR_H
#define RESAMPLER_LINEAR_H

#include "compiler.h"

typedef void (*resample_generate)(void*);

struct ResamplerLinear {
    // 1 if there is no need to resample, otherwise 0
    int same;
    int first;
    // Difference of internal vs. target, decrements at each tick of
    // the internal clock
    double pos;
    double inc;
    SGFLT last;
    SGFLT next;
    resample_generate func;
};

void resampler_linear_init(
    struct ResamplerLinear* self,
    int internal_rate,
    int target_rate,
    resample_generate func
);

SGFLT resampler_linear_run_mono(
    struct ResamplerLinear* self,
    void* func_arg
);

#endif
