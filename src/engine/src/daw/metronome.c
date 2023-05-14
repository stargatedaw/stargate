#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/interpolate-cubic.h"
#include "daw.h"
#include "daw/metronome.h"
#include "globals.h"

#include <sndfile.h>
#include <string.h>


void metronome_init(struct Metronome* self, SGFLT sr){
    *self = (struct Metronome){
        .pos = 9999999,
        .samplerate = sr,
    };
    struct MetronomeVoice* voice;
    for(int i = 0; i < METRONOME_POLYPHONY; ++i){
        voice = &self->voices[i];
        voice->pos = 32;
        voice->posf = 0.0;
    }
}

void metronome_normalize(float* samples, int len, SGFLT db){
    float _min = 0.0;
    float _max = 0.0;
    for(int i = 32; i < len; ++i){
        if(samples[i] > _max){
            _max = samples[i];
        } else if(samples[i] < _min){
            _min = samples[i];
        }
    }
    _min *= -1.0;
    if(_min > _max){
        _max = _min;
    }
    float _factor = _max / f_db_to_linear(db);
    for(int i = 32; i < len; ++i){
        samples[i] *= _factor;
    }
}

void metronome_envelope(struct MetronomeSample* self){
    float env_len = 0.005 * self->samplerate;
    float env_recip = 1.0 / env_len;
    int env_pos = self->len - (env_len * self->channels);
    for(int i = 0; i < (int)env_len; ++i){
        for(int j = 0; j < self->channels; ++j){
            self->samples[env_pos] *= 1.0 - (env_recip * i);
            ++env_pos;
        }
    }
}

void metronome_load_sample(
    struct MetronomeSample* self, 
    SGPATHSTR* path, 
    SGFLT sr
){
    SF_INFO info;
    SNDFILE *file;

    info.format = 0;

    file = SG_SF_OPEN(path, SFM_READ, &info);

    sf_count_t frames = (sf_count_t)((double)info.samplerate * 0.25);
    if(info.frames < frames){
        frames = info.frames;
    }

    sg_assert(
        info.channels == 1 || info.channels == 2,
#if SG_OS == _OS_WINDOWS
        "%ls: Invalid number of channels: %d",
#else
        "%s: Invalid number of channels: %d",
#endif
        path,
        info.channels
    );

    if(self->samples){
        free(self->samples);
        self->samples = NULL;
    }
    size_t arr_size = (
        frames * info.channels * sizeof(float)
    ) + (64 * sizeof(float));
    self->samples = (float*)malloc(arr_size);
    memset((void*)self->samples, 0, arr_size);
    sf_readf_float(file, &self->samples[32], frames);
    sf_close(file);

    self->channels = info.channels;
    self->samplerate = info.samplerate;
    self->len = (frames * info.channels) + 32;
    self->lenf = self->len;
    double step = (self->samplerate / sr) * (double)self->channels;
    self->step = (int)step;
    self->stepf = step - (float)self->step;
    metronome_normalize(self->samples, self->len, -6.0);
    metronome_envelope(self);
}

void metronome_load(struct Metronome* self){
    SGPATHSTR path[1024];
    sg_path_snprintf(
        path, 
        1024, 
#if SG_OS == _OS_WINDOWS
        L"%ls/files/metronome/square/up.wav", 
#else
        "%s/files/metronome/square/up.wav", 
#endif
        INSTALL_PREFIX
    );
    metronome_load_sample(&self->samples[0], path, self->samplerate);
    sg_path_snprintf(
        path, 
        1024, 
#if SG_OS == _OS_WINDOWS
        L"%ls/files/metronome/square/down.wav", 
#else
        "%s/files/metronome/square/down.wav", 
#endif
        INSTALL_PREFIX
    );
    metronome_load_sample(&self->samples[1], path, self->samplerate);
}

struct MetronomeBeat metronome_beat_at_pos(int pos){
    if(pos < DAW->en_song->sequences->metronome.len){
        return DAW->en_song->sequences->metronome.beats[pos];
    } else {
        int offset = pos - (int)STARGATE->current_tsig->beat;
        int num = STARGATE->current_tsig->tsig.num;
        int downbeat = offset % num == 0 ? 1: 0;
        return (struct MetronomeBeat){
            .downbeat = downbeat,
            .beat = (SGFLT)pos,
        };
    }
}

void metronome_process_event(
    struct Metronome* self,
    struct MetronomeBeat* beat,
    double current_beat,
    double next_beat,
    int sample_count
){
    int tick = (
        (beat->beat - current_beat) / (next_beat - current_beat)
    ) * sample_count;
    int voice_num = beat->downbeat;
    struct MetronomeVoice* voice = &self->voices[voice_num];
    voice->active = 1;
    voice->on = tick;
    voice->downbeat = beat->downbeat;
    voice->sample = &self->samples[beat->downbeat];
    voice->pos = 32;
    voice->posf = 0.0;
}

int _metronome_increment(struct MetronomeVoice* voice, int voice_num){
    voice->pos += voice->sample->step;    
    voice->posf += voice->sample->stepf;
    while(voice->posf >= 1.0){
        voice->posf -= 1.0;
        ++voice->pos;
    }
    if(voice->pos >= voice->sample->len){
        return 1;
    }
    return 0;
}

void metronome_voice_run(
    struct Metronome* self, 
    int voice_num,
    int sample_count, 
    struct SamplePair* buffer
){
    int i;
    int start = 0;
    float samples[4];
    SGFLT output;
    struct MetronomeVoice* voice = &self->voices[voice_num];
    if(!voice->sample){
        voice->active = 0;
        return;
    }
    if(voice->on >= 0){
        start = voice->on;
        voice->on = -1;
    }

    if(voice->sample->channels == 1){
        for(i = start; i < sample_count; ++i){
            samples[0] = voice->sample->samples[voice->pos - 2];
            samples[1] = voice->sample->samples[voice->pos - 1];
            samples[2] = voice->sample->samples[voice->pos];
            samples[3] = voice->sample->samples[voice->pos + 1];
            output = f_cubic_interpolate_ptr_ifh(samples, 2, voice->posf);
            buffer[i].left += output;
            buffer[i].right += output;
            if(_metronome_increment(voice, voice_num)){
                voice->active = 0;
                break;
            }
        }
    } else if(voice->sample->channels == 2){
        for(i = start; i < sample_count; ++i){
            samples[0] = voice->sample->samples[voice->pos - 4];
            samples[1] = voice->sample->samples[voice->pos - 2];
            samples[2] = voice->sample->samples[voice->pos];
            samples[3] = voice->sample->samples[voice->pos + 2];
            output = f_cubic_interpolate_ptr_ifh(samples, 2, voice->posf);
            buffer[i].left += output;
            samples[0] = voice->sample->samples[voice->pos - 3];
            samples[1] = voice->sample->samples[voice->pos - 1];
            samples[2] = voice->sample->samples[voice->pos + 1];
            samples[3] = voice->sample->samples[voice->pos + 3];
            output = f_cubic_interpolate_ptr_ifh(samples, 2, voice->posf);
            buffer[i].right += output;
            if(_metronome_increment(voice, voice_num)){
                voice->active = 0;
                break;
            }
        }
    }
}

void metronome_run(
    struct Metronome* self, 
    int sample_count, 
    struct SamplePair* buffer,
    double current_beat,
    double next_beat
){
    int i;
    struct MetronomeBeat beat;
    beat = metronome_beat_at_pos(self->pos);
    if(beat.beat < current_beat || beat.beat - current_beat > 1.0){
        self->pos = (int)current_beat;
        if(self->pos < current_beat){
            ++self->pos;
        }
        beat = metronome_beat_at_pos(self->pos);
    }
    if(beat.beat <= next_beat){
        ++self->pos;
        metronome_process_event(
            self, 
            &beat, 
            current_beat, 
            next_beat, 
            sample_count
        );
    }
    for(i = 0; i < METRONOME_POLYPHONY; ++i){
        if(self->voices[i].active){
            metronome_voice_run(self, i, sample_count, buffer);
        }
    }
}

