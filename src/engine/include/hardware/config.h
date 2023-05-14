#ifndef HARDWARE_CONFIG_H
#define HARDWARE_CONFIG_H

#define DEFAULT_FRAMES_PER_BUFFER 512

extern int OUTPUT_CH_COUNT;
extern int MAIN_OUT_L;
extern int MAIN_OUT_R;
extern int THREAD_AFFINITY;
extern int THREAD_AFFINITY_SET;
extern int AUDIO_INPUT_TRACK_COUNT;
extern int NO_HARDWARE;


struct HardwareConfig{
    SGFLT sample_rate;
    char host_api_name[128];
    char device_name[256];
    char input_name[256];
    int audio_input_count;
    int audio_output_count;
    int frame_count;
    int performance;
    int thread_affinity;
    int thread_count;
    char midi_in_device_names[10][128];
    int midi_in_device_count;
    int test_volume;
};

/* Return the default device config path
 */
SGPATHSTR* default_device_file_path();

/* Load a hardware config from a file
 * @hardware_config_path: The path to the config to load
 * @return:
 */
struct HardwareConfig* load_hardware_config(
    SGPATHSTR* config_path
);

#endif
