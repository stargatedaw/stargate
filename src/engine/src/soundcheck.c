#include <portaudio.h>
#include <string.h>
#include <unistd.h>

#include "files.h"
#include "hardware/audio.h"
#include "soundcheck.h"

struct SoundCheck SOUNDCHECK;

int soundcheck(int argc, SGPATHSTR** argv){
    if(argc != 3){
        printf("Usage: %s soundcheck /path/to/device-config.txt\n", argv[0]);
        exit(33);
    }
    if(!i_file_exists(argv[2])){
        printf("'%s' does not exist\n", argv[2]);
        exit(33);
    }

    int retcode = 0;
    struct HardwareConfig* hardware_config = load_hardware_config(argv[2]);
    if(!hardware_config){
        printf("Failed to load hardware config %s\n", argv[2]);
        exit(321);
    }
    soundcheck_init(
        &SOUNDCHECK,
        hardware_config->sample_rate,
        hardware_config->test_volume
    );
    retcode = open_audio_device(
        hardware_config,
        soundcheck_callback
    );

    if(retcode){
        return retcode;
    }

    sleep(2);

    close_audio_device();

    return 0;
}

void soundcheck_init(struct SoundCheck* sc, SGFLT sr, int volume){
    g_adsr_init(&sc->adsr, sr);
    sc->volume = f_db_to_linear((SGFLT)volume);

    g_osc_simple_unison_init(&sc->osc, sr, 0);
    v_osc_set_uni_voice_count(&sc->osc, 1);
    v_osc_set_unison_pitch(&sc->osc, 0.5, 48.);
    v_osc_set_simple_osc_unison_type_v2(&sc->osc, 3);
}

SGFLT soundcheck_run(struct SoundCheck* sc){
    return f_osc_run_unison_osc(&sc->osc) * sc->volume;
}

int soundcheck_callback(
    const void *inputBuffer,
    void *outputBuffer,
    unsigned long framesPerBuffer,
    const PaStreamCallbackTimeInfo* timeInfo,
    PaStreamCallbackFlags statusFlags,
    void *userData
){
    SGFLT sample;
    int f_i;
    float* out = (float*)outputBuffer;

    if(OUTPUT_CH_COUNT > 2){
        int f_i2 = 0;
        memset(
            out,
            0,
            sizeof(float) * framesPerBuffer * OUTPUT_CH_COUNT
        );

        for(f_i = 0; f_i < framesPerBuffer; ++f_i){
            sample = soundcheck_run(&SOUNDCHECK);
            out[f_i2 + MAIN_OUT_L] = sample;
            out[f_i2 + MAIN_OUT_R] = sample;
            f_i2 += OUTPUT_CH_COUNT;
        }
    } else {
        for(f_i = 0; f_i < framesPerBuffer; ++f_i){
            sample = soundcheck_run(&SOUNDCHECK);
            *out = sample;  // left
            ++out;
            *out = sample;  // right
            ++out;
        }
    }

    return paContinue;
}
