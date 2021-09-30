#ifndef RESAMPLER_LINEAR_H
#define RESAMPLER_LINEAR_H

#include "compiler.h"

struct ResamplerGenerateRet {
    SGFLT samples[2];
};

typedef SGFLT (*resample_generate)(void*);

// Generates audio from a source function at a different (or same) sample
// rate as Stargate, and resamples the audio using linear interpolation
struct ResamplerLinear {
    // 1 if there is no need to resample, otherwise 0
    int same;
    // The first run, or the first run of the current voice
    int first;
    // Difference of internal vs. target clocks, decrements at each tick of
    // the internal clock
    double pos;
    double inc;
    SGFLT previous;
    SGFLT next;
    resample_generate func;
    void* func_arg;
};

/* internal_rate: The internal sample rate to run @func at
 * target_rate: The external sample rate to resample to
 * func: A function to generate samples
 * func_arg: The argument to pass to @func
 */
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

// Reset the resampler at note-on
void resampler_linear_reset(
    struct ResamplerLinear* self
);

#endif
