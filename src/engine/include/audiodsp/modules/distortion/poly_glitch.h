#ifndef POLY_GLITCH_H
#define POLY_GLITCH_H

#include "compiler.h"

struct PolyGlitch {
    struct SamplePair* buffer;
    int buffer_len;  // max size of the buffer
    int input_pos;  // position input has been written to
    int pos;  // position of the playback cursor
    SGFLT last_pitch;
    SGFLT sr;
    int repeat_pos;  // position to reset to zero on
};

void poly_glitch_init(struct PolyGlitch* self, SGFLT sr);
void poly_glitch_trigger(struct PolyGlitch* self);
void poly_glitch_set(struct PolyGlitch* self, SGFLT pitch);
struct SamplePair poly_glitch_run(
    struct PolyGlitch* self,
    struct SamplePair input
);

#endif
