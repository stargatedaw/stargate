#include <stdlib.h>
#include <string.h>

#include "compiler.h"
#include "csv/2d.h"
#include "csv/split.h"
#include "files.h"
#include "file/path.h"
#include "hardware/config.h"

int OUTPUT_CH_COUNT = 2;
int MAIN_OUT_L = 0;
int MAIN_OUT_R = 1;
int THREAD_AFFINITY = 0;
int THREAD_AFFINITY_SET = 0;
int AUDIO_INPUT_TRACK_COUNT = 0;
int NO_HARDWARE = 0;


NO_OPTIMIZATION SGPATHSTR* default_device_file_path(){
    SGPATHSTR* result = (SGPATHSTR*)malloc(sizeof(SGPATHSTR) * 2048);
    SGPATHSTR* home = get_home_dir();

#if SG_OS == _OS_WINDOWS
    log_info("using home folder: %ls", home);
#else
    log_info("using home folder: %s", home);
#endif

    sg_path_snprintf(
        result,
	2048,
#if SG_OS == _OS_WINDOWS
	L"%ls/%s/config/device.txt",
#else
	"%s/%s/config/device.txt",
#endif
        home, 
	STARGATE_VERSION
    );

    return result;
}

NO_OPTIMIZATION struct HardwareConfig* load_hardware_config(
    SGPATHSTR* config_path
){
    struct HardwareConfig* result = (struct HardwareConfig*)malloc(
        sizeof(struct HardwareConfig)
    );
    *result = (struct HardwareConfig){
        .sample_rate = 44100.0,
        .host_api_name = "",
        .device_name = "",
        .input_name = "",
        .audio_input_count = 0,
        .audio_output_count = 2,
        .frame_count = DEFAULT_FRAMES_PER_BUFFER,
        .performance = 0,
        .thread_affinity = 0,
        .thread_count = 0,
        .midi_in_device_count = 0,
        .test_volume = -15,
    };

    char * f_key_char = (char*)malloc(sizeof(char) * TINY_STRING);
    char * f_value_char = (char*)malloc(sizeof(char) * TINY_STRING);

    if(!i_file_exists(config_path)){
#if SG_OS == _OS_WINDOWS
        log_info("%ls does not exist", config_path);
#else
        log_info("%s does not exist", config_path);
#endif
        return NULL;
    }
#if SG_OS == _OS_WINDOWS
    log_info("%ls exists, loading", config_path);
#else
    log_info("%s exists, loading", config_path);
#endif

    t_2d_char_array * f_current_string = g_get_2d_array_from_file(
        config_path,
        LARGE_STRING
    );
    while(1)
    {
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof){
            break;
        }
        if(
            !strcmp(f_current_string->current_str, "")
            ||
            f_current_string->eol
        ){
            continue;
        }

        strcpy(f_key_char, f_current_string->current_str);
        v_iterate_2d_char_array_to_next_line(f_current_string);
        strcpy(f_value_char, f_current_string->current_str);

        if(!strcmp(f_key_char, "hostApi")){
            strncpy(result->host_api_name, f_value_char, 127);
        } else if(!strcmp(f_key_char, "name")){
            strncpy(result->device_name, f_value_char, 255);
        } else if(!strcmp(f_key_char, "inputName")){
            strncpy(result->input_name, f_value_char, 255);
            log_info("input name: %s", result->input_name);
        } else if(!strcmp(f_key_char, "bufferSize")){
            result->frame_count = atoi(f_value_char);
            log_info("bufferSize: %i", result->frame_count);
        } else if(!strcmp(f_key_char, "audioEngine")){
            int f_engine = atoi(f_value_char);
            log_info("audioEngine: %i", f_engine);
            if(f_engine == 4 || f_engine == 5 || f_engine == 7){
                NO_HARDWARE = 1;
            } else {
                //NO_HARDWARE = 0;
            }
        } else if(!strcmp(f_key_char, "sampleRate")){
            result->sample_rate = atof(f_value_char);
            log_info("sampleRate: %i", (int)result->sample_rate);
        } else if(!strcmp(f_key_char, "threads")){
            result->thread_count = atoi(f_value_char);
            if(result->thread_count > 8){
                result->thread_count = 8;
            } else if(result->thread_count < 0){
                result->thread_count = 0;
            }
            log_info("threads: %i", result->thread_count);
        } else if(!strcmp(f_key_char, "threadAffinity")){
            result->thread_affinity = atoi(f_value_char);
            THREAD_AFFINITY = result->thread_affinity;
            log_info("threadAffinity: %i", result->thread_affinity);
        } else if(!strcmp(f_key_char, "performance")){
            result->performance = atoi(f_value_char);

            log_info("performance: %i", result->performance);
        } else if(!strcmp(f_key_char, "midiInDevice")){
            sg_snprintf(
                result->midi_in_device_names[result->midi_in_device_count],
                127,
                "%s",
                f_value_char
            );
            result->midi_in_device_count++;
        } else if(!strcmp(f_key_char, "audioInputs")){
            result->audio_input_count = atoi(f_value_char);
            log_info("audioInputs: %s", f_value_char);
            sg_assert(
                result->audio_input_count >= 0
                &&
                result->audio_input_count <= 128,
                "load_hardware_config: audio_input_count %i out of "
                "range 0 to 128",
                result->audio_input_count
            );
            AUDIO_INPUT_TRACK_COUNT = result->audio_input_count;
        } else if(!strcmp(f_key_char, "testVolume")){
            result->test_volume = atoi(f_value_char);
            sg_assert(
                result->test_volume >= -50
                &&
                result->test_volume <= -6,
                "test_volume out of range -36 to -6: %i",
                result->test_volume
            );
        } else if(!strcmp(f_key_char, "audioOutputs")){
            t_line_split * f_line = g_split_line(
                '|',
                f_value_char
            );
            if(f_line->count != 3){
                log_info(
                    "audioOutputs: invalid value: '%s'",
                    f_value_char
                );
                return NULL;
            }
            log_info("audioOutputs: %s", f_value_char);

            result->audio_output_count = atoi(f_line->str_arr[0]);
            sg_assert(
                result->audio_output_count >= 1
                &&
                result->audio_output_count <= 128,
                "load_hardware_config: audio output count %i out of "
                "range 1 to 128",
                result->audio_output_count
            );
            OUTPUT_CH_COUNT = result->audio_output_count;
            MAIN_OUT_L = atoi(f_line->str_arr[1]);
            MAIN_OUT_R = atoi(f_line->str_arr[2]);
            sg_assert(
                MAIN_OUT_L >= 0
                &&
                MAIN_OUT_L < result->audio_output_count,
                "load_hardware_config: MAIN_OUT_L %i out of range 0 to %i",
                MAIN_OUT_L,
                result->audio_output_count
            );
            sg_assert(
                MAIN_OUT_R >= 0
                &&
                MAIN_OUT_R < result->audio_output_count,
                "load_hardware_config: MAIN_OUT_R %i out of range 0 to %i",
                MAIN_OUT_R,
                result->audio_output_count
            );

            v_free_split_line(f_line);
        } else {
            log_warn(
                "Unknown key|value pair: %s|%s",
                f_key_char,
                f_value_char
            );
        }
    }

    free(f_key_char);
    free(f_value_char);

    g_free_2d_char_array(f_current_string);

    return result;
}
