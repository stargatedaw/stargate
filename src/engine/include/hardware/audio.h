#ifndef HARDWARE_AUDIO_H
#define HARDWARE_AUDIO_H

#include <portaudio.h>

#include "compiler.h"
#include "hardware/config.h"

#define PA_SAMPLE_TYPE paFloat32

#define RET_CODE_DEVICE_NOT_FOUND 1000
#define RET_CODE_CONFIG_NOT_FOUND 1001
#define RET_CODE_AUDIO_DEVICE_ERROR 1002
#define RET_CODE_AUDIO_DEVICE_BUSY 1003

int open_audio_device(
    struct HardwareConfig* config,
    PaStreamCallback callback
);
void close_audio_device();
int portaudioCallback(
    const void *inputBuffer,
    void *outputBuffer,
    unsigned long framesPerBuffer,
    const PaStreamCallbackTimeInfo* timeInfo,
    PaStreamCallbackFlags statusFlags,
    void *userData
);

#endif
