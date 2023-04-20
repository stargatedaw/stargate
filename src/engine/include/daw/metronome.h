#ifndef DAW_METRONOME_H
#define DAW_METRONOME_H

#include "compiler.h"

#define METRONOME_POLYPHONY 2

struct MetronomeSample {
    SGFLT samplerate;
    // Whole number ratio of samplerate to playback samplerate, times channels
    int step;  
    // Fractional ratio of samplerate to playback samplerate, times channels
    SGFLT stepf;
    int len;
    float lenf;
    int channels;
    float* samples;
};

struct MetronomeVoice {
    int downbeat;
    int on;
    int active;
    int pos;  // Position within the samples
    SGFLT posf;  // Position between the samples
    struct MetronomeSample* sample;
};

struct Metronome {
    int pos;  // Beat position within the song
    SGFLT samplerate;
    struct MetronomeVoice voices[METRONOME_POLYPHONY];
    struct MetronomeSample samples[METRONOME_POLYPHONY];
};

void metronome_init(struct Metronome* self, SGFLT sr);
void metronome_load(struct Metronome* self);
void metronome_set(struct Metronome* self);
void metronome_run(
    struct Metronome* self, 
    int sample_count, 
    struct SamplePair* buffer,
    double current_beat,
    double next_beat
);

#endif
