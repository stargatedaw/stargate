#include <string.h>
#include <unistd.h>

#include "hardware/audio.h"
#include "stargate.h"

PaStream* PA_STREAM;

NO_OPTIMIZATION int open_audio_device(
    struct HardwareConfig* config,
    PaStreamCallback callback
){
    int f_i;
    int f_host_api_index = -1;
    /*Initialize Portaudio*/
    PaStreamParameters inputParameters = (PaStreamParameters){};
    PaStreamParameters outputParameters = (PaStreamParameters){};
    PaStream* stream = NULL;
    PaError err;
    log_info("Opening audio device");
    err = Pa_Initialize();
    if(err != paNoError){
        log_error(
            "Pa_Initialize error:  %s",
            Pa_GetErrorText(err)
        );
        return 1;
    }
    /* default input device */
    int f_api_count = Pa_GetHostApiCount();
    if(f_api_count <= 0){
        log_error(
            "Pa_GetHostApiCount error:  %s",
            Pa_GetErrorText(f_api_count)
        );
        return 1;
    }

    char f_host_apis[f_api_count][256];

    for(f_i = 0; f_i < f_api_count; ++f_i){
        strncpy(
            f_host_apis[f_i],
            Pa_GetHostApiInfo(f_i)->name,
            256
        );
    }

    for(f_i = 0; f_i < f_api_count; ++f_i){
        if(!strcmp(config->host_api_name, f_host_apis[f_i])){
            f_host_api_index = f_i;
            break;
        }
    }
    log_info("host api: %s", config->host_api_name);
    log_info("host api index %i", f_host_api_index);

    inputParameters.channelCount = config->audio_input_count;
    inputParameters.sampleFormat = PA_SAMPLE_TYPE;
    inputParameters.hostApiSpecificStreamInfo = NULL;

    outputParameters.channelCount = config->audio_output_count;
    outputParameters.sampleFormat = PA_SAMPLE_TYPE;
    outputParameters.hostApiSpecificStreamInfo = NULL;

    int f_found_index = 0;
    for(f_i = 0; f_i < Pa_GetDeviceCount(); ++f_i){
        const PaDeviceInfo* f_padevice = Pa_GetDeviceInfo(f_i);
        const PaHostApiInfo* host_api = Pa_GetHostApiInfo(f_padevice->hostApi);
        log_info(
            "device: '%s' host api: '%s' output channels: %i",
            f_padevice->name,
            host_api->name,
            f_padevice->maxOutputChannels
        );
        if(
            !strcmp(f_padevice->name, config->device_name)
            &&
            f_host_api_index == f_padevice->hostApi
        ){
            if(!f_padevice->maxOutputChannels){
                log_error(
                    "PaDevice->maxOutputChannels == 0, "
                    "device may already be open by another application"
                );
                return RET_CODE_AUDIO_DEVICE_BUSY;
            }

            outputParameters.device = f_i;
            inputParameters.device = f_i;
            f_found_index = 1;
            break;
        }
    }

    if(!f_found_index){
        log_error("'%s' not found", config->device_name);
        return RET_CODE_DEVICE_NOT_FOUND;
    }

    const PaDeviceInfo * f_device_info = Pa_GetDeviceInfo(
        outputParameters.device
    );

    outputParameters.suggestedLatency = f_device_info->defaultLowOutputLatency;

#if SG_OS == _OS_WINDOWS || SG_OS == _OS_MACOS
    if(config->input_name[0] == '\0'){
        inputParameters.channelCount = 0;
    } else {
        f_found_index = 0;
        for(f_i = 0; f_i < Pa_GetDeviceCount(); ++f_i){
            const PaDeviceInfo * f_padevice = Pa_GetDeviceInfo(f_i);
            if(
                !strcmp(f_padevice->name, config->input_name)
                &&
                f_host_api_index == f_padevice->hostApi
                &&
                f_padevice->maxInputChannels
            ){
                inputParameters.device = f_i;
                f_found_index = 1;
                break;
            }
        }

        if(!f_found_index){
            log_error("Device not found");
            return RET_CODE_DEVICE_NOT_FOUND;
        }

        f_device_info = Pa_GetDeviceInfo(inputParameters.device);

        inputParameters.suggestedLatency =
            f_device_info->defaultLowInputLatency;
    }
#else
    inputParameters.device = outputParameters.device;
#endif

    if(!NO_HARDWARE){
        PaStreamParameters * f_input_params = NULL;

        if(inputParameters.channelCount > 0){
            f_input_params = &inputParameters;
        }

        err = Pa_OpenStream(
            &stream,
            f_input_params,
            &outputParameters,
            config->sample_rate,
            config->frame_count,
            0, // paClipOff
            callback,
            NULL
        );

        if(err != paNoError){
            log_error(
                "Error while opening audio device: %s",
                Pa_GetErrorText(err)
            );
            return RET_CODE_AUDIO_DEVICE_ERROR;
        }
    }

    err = Pa_StartStream(stream);
    if(err != paNoError){
        log_error(
            "'%s' while starting device.  Please "
            "re-configure your device and try starting Stargate again.",
            Pa_GetErrorText(err)
        );
        return RET_CODE_AUDIO_DEVICE_ERROR;
    }
    const PaStreamInfo * f_stream_info = Pa_GetStreamInfo(stream);
    log_info(
        "Actual output latency: %fs, %fms, %i samples",
        f_stream_info->outputLatency,
        f_stream_info->outputLatency * 1000.0,
        (int)(f_stream_info->outputLatency * f_stream_info->sampleRate)
    );
    if((int)f_stream_info->sampleRate != (int)config->sample_rate){
        log_warn(
            "Samplerate reported by the device (%f)  does not "
            "match the selected sample rate %f.",
            f_stream_info->sampleRate,
            config->sample_rate
        );
    }

    PA_STREAM = stream;
    return 0;
}

NO_OPTIMIZATION void close_audio_device(){
    log_info("Closing audio device");
    PaError err;
    err = Pa_CloseStream(PA_STREAM);
    if(err != paNoError){
        log_error(
            "Pa_CloseStream error:  %s",
            Pa_GetErrorText(err)
        );

        usleep(50000);

        err = Pa_IsStreamStopped(PA_STREAM);

        if(err < 1)
        {
            if(err == 0)
                log_info("Pa_IsStreamStopped returned 0");
            if(err < 0)
                log_error(
                    "Pa_IsStreamStopped error:  %s",
                    Pa_GetErrorText(err)
                );
            err = Pa_AbortStream(PA_STREAM);
            if(err != paNoError)
                log_error(
                    "Pa_AbortStream error:  %s",
                    Pa_GetErrorText(err)
                );
        }
    }
    err = Pa_Terminate();
    if(err != paNoError){
        log_error(
            "Pa_Terminate error:  %s",
            Pa_GetErrorText(err)
        );
    }
}

int portaudioCallback(
    const void *inputBuffer,
    void *outputBuffer,
    unsigned long framesPerBuffer,
    const PaStreamCallbackTimeInfo* timeInfo,
    PaStreamCallbackFlags statusFlags,
    void *userData
){
    STARGATE->out = (float*)outputBuffer;
    SGFLT *in = (SGFLT*)inputBuffer;

    if(unlikely(framesPerBuffer > FRAMES_PER_BUFFER)){
        /*
        fprintf(
            stderr,
            "WARNING:  Audio device requested buffer size %i, "
            "truncating to max buffer size:  %i\n",
            (int)framesPerBuffer,
            FRAMES_PER_BUFFER
        );
        */
        framesPerBuffer = FRAMES_PER_BUFFER;
    }

    /*
    // Try one time to set thread affinity
    if(unlikely(THREAD_AFFINITY && !THREAD_AFFINITY_SET)){
        v_self_set_thread_affinity();
        THREAD_AFFINITY_SET = 1;
    }
    */

    v_run(pluginOutputBuffers, in, framesPerBuffer);

    return paContinue;
}

