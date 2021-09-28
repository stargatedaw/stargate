#ifndef RESAMPLER_LINEAR_H
#define RESAMPLER_LINEAR_H

#include "compiler.h"

typedef void (*resample_generate)(void*);

// Generates audio from a source function at a different (or same) sample
// rate as Stargate, and resamples the audio using linear interpolation
struct ResamplerLinear {
    // 1 if there is no need to resample, otherwise 0
    int same;
    int first;
    // Difference of internal vs. target clocks, decrements at each tick of
    // the internal clock
    double pos;
    double inc;
    SGFLT last;
    SGFLT next;
    resample_generate func;
    void* func_arg;
};

void resampler_linear_init(
    struct ResamplerLinear* self,
    int internal_rate,
    int target_rate,
    resample_generate func,
    void* func_arg
);

SGFLT resampler_linear_run_mono(
    struct ResamplerLinear* self
);

#endif
