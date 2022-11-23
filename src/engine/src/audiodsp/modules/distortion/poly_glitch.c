#include "audiodsp/modules/distortion/poly_glitch.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/pitch_core.h"


void poly_glitch_init(struct PolyGlitch* self, SGFLT sr){
    int buffer_len = (int)(sr / 15.);
    *self = (struct PolyGlitch){
        .buffer_len = buffer_len,
        .last_pitch = -123.456,
        .sr = sr,
    };
    hpalloc((void**)&self->buffer, sizeof(struct SamplePair) * buffer_len);
}

void poly_glitch_trigger(struct PolyGlitch* self){
    self->pos = 0;
    self->input_pos = 0;
}

void poly_glitch_set(struct PolyGlitch* self, SGFLT pitch){
    if(pitch != self->last_pitch){
        self->last_pitch = pitch;
        SGFLT hz = f_pit_midi_note_to_hz_fast(pitch);
        self->repeat_pos = (int)(self->sr / hz);
        if(self->repeat_pos >= self->buffer_len){
            self->repeat_pos = self->buffer_len - 1;
        } else if(self->repeat_pos < 2){
            self->repeat_pos = 2;
        }
    }
}

struct SamplePair poly_glitch_run(
    struct PolyGlitch* self,
    struct SamplePair input
){
    if(self->input_pos < self->buffer_len - 1){
        self->buffer[self->input_pos] = input;
        ++self->input_pos;
    }
    struct SamplePair result = self->buffer[self->pos];
    ++self->pos;
    if(self->pos >= self->repeat_pos){
        self->pos = 0;
    }
    return result;
}

