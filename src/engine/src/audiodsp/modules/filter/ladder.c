#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/clip.h"
#include "audiodsp/lib/fast_sine.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/filter/ladder.h"


void ladder_init(struct LadderFilter* self, SGFLT sampleRate){
    *self = (struct LadderFilter){
        ._c = -1.2344556,
        ._r = -123.44556,
        .max_freq = fclip_max(sampleRate * 0.49, 21000.),
        .sampleRate = sampleRate,
        .sr_recip = 1. / sampleRate,
    };
    ladder_set(self, 1000., -18.);
}

SGFLT _ladder_run_mono(
    struct LadderFilter* self,
    struct LadderChannel* ch,
    SGFLT sample
){
    SGFLT x = sample - self->resonance * ch->stage[3];

    // Four cascaded one-pole filters (bilinear transform)
    ch->stage[0] = x * self->p + ch->delay[0] * self->p -
        self->k * ch->stage[0];
    ch->stage[1] = ch->stage[0] * self->p + ch->delay[1] * self->p -
        self->k * ch->stage[1];
    ch->stage[2] = ch->stage[1] * self->p + ch->delay[2] * self->p -
        self->k * ch->stage[2];
    ch->stage[3] = ch->stage[2] * self->p + ch->delay[3] * self->p -
        self->k * ch->stage[3];

    // Clipping band-limited sigmoid
    ch->stage[3] -=
        (ch->stage[3] * ch->stage[3] * ch->stage[3]) * 0.166666666666666;

    ch->delay[0] = x;
    ch->delay[1] = ch->stage[0];
    ch->delay[2] = ch->stage[1];
    ch->delay[3] = ch->stage[2];

    return ch->stage[3];
}

SGFLT ladder_run_mono(
    struct LadderFilter* self,
    SGFLT sample
){
    return _ladder_run_mono(self, &self->channels[0], sample);
}

struct SamplePair ladder_run_stereo(
    struct LadderFilter* self,
    struct SamplePair sample
){
    return (struct SamplePair){
        .left = _ladder_run_mono(self, &self->channels[0], sample.left),
        .right = _ladder_run_mono(self, &self->channels[1], sample.right),
    };
}

void ladder_set(struct LadderFilter* self, SGFLT c, SGFLT r){
    if(c == self->_c && r == self->_r){
        return;
    }
    self->_c = c;
    self->_r = r;
    SGFLT c_hz = fclip(
        f_pit_midi_note_to_hz_fast(c),
        20.,
        self->max_freq
    );
    self->cutoff = 2.0 * c_hz * self->sr_recip;

    self->p = self->cutoff * (1.8 - 0.8 * self->cutoff);
    self->k = 2.0 * f_sine_fast_run_radians(
        self->cutoff * LADDER_PI * 0.5
    ) - 1.0;
    self->t1 = (1.0 - self->p) * 1.386249;
    self->t2 = 12.0 + self->t1 * self->t1;

    self->resonance = f_db_to_linear_fast(r) * (self->t2 + 6.0 * self->t1) /
        (self->t2 - 6.0 * self->t1);
}

