#ifndef SG_SOUNDCHECK_H
#define SG_SOUNDCHECK_H

#include "audiodsp/modules/modulation/adsr.h"
#include "audiodsp/modules/oscillator/osc_simple.h"
#include "compiler.h"

struct SoundCheck {
    t_adsr adsr;
    t_osc_simple_unison osc;
    SGFLT volume;
};

extern struct SoundCheck SOUNDCHECK;

int soundcheck(int arc, SGPATHSTR** argv);
void soundcheck_init(struct SoundCheck*, SGFLT, int);
SGFLT soundcheck_run(struct SoundCheck*);
int soundcheck_callback(
    const void *inputBuffer,
    void *outputBuffer,
    unsigned long framesPerBuffer,
    const PaStreamCallbackTimeInfo* timeInfo,
    PaStreamCallbackFlags statusFlags,
    void *userData
);

#endif
