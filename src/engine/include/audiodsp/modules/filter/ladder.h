#ifndef STARGATE_LADDER_H
#define STARGATE_LADDER_H

#include "compiler.h"

#define LADDER_PI 3.14159265358979323846264338327950288

struct LadderChannel {
    double stage[4];
    double delay[4];
};

struct LadderFilter {
    SGFLT _c;
    SGFLT _r;

    SGFLT cutoff;
    SGFLT resonance;
    SGFLT sampleRate;
    SGFLT sr_recip;
    SGFLT max_freq;

    double p;
    double k;
    double t1;
    double t2;

    struct LadderChannel channels[2];
};

void ladder_init(struct LadderFilter* self, SGFLT sampleRate);
SGFLT ladder_run_mono(
    struct LadderFilter* self,
    SGFLT sample
);
struct SamplePair ladder_run_stereo(
    struct LadderFilter* self,
    struct SamplePair sample
);
void ladder_set(struct LadderFilter* self, SGFLT c, SGFLT r);

#endif
