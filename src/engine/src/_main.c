/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/


#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <portaudio.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include "_main.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"
#include "csv/split.h"
#include "daw.h"
#include "file/path.h"
#include "file/pidfile.h"
#include "files.h"
#include "plugin.h"
#include "hardware/audio.h"
#include "hardware/config.h"
#include "hardware/midi.h"
#include "stargate.h"
#include "wave_edit.h"
#include "worker.h"

#ifndef NO_MIDI
    #include "hardware/midi.h"
#endif

#if defined(__linux__) && !defined(SG_DLL)
    sigset_t _signals;
#endif

#ifndef NO_MIDI
    t_midi_device_list MIDI_DEVICES;
    PmError f_midi_err;
#endif

#ifdef WITH_LIBLO
    lo_server_thread serverThread;
#endif

// Insert a brief sleep between loop runs when running without hardware
static int NO_HARDWARE_USLEEP = 0;

void signalHandler(int sig){
    printf("signal %d caught, trying to clean up and exit\n", sig);
    pthread_mutex_lock(&STARGATE->exit_mutex);
    exiting = 1;
    pthread_mutex_unlock(&STARGATE->exit_mutex);
}

typedef struct
{
    int pid;
}ui_thread_args;

NO_OPTIMIZATION void * ui_process_monitor_thread(
    void * a_thread_args)
{
    char f_proc_path[256];
    f_proc_path[0] = '\0';
    ui_thread_args * f_thread_args = (ui_thread_args*)(a_thread_args);
    sprintf(f_proc_path, "/proc/%i", f_thread_args->pid);
    struct stat sts;
    int f_exited = 0;

    while(!exiting)
    {
        sleep(1);
        if (stat(f_proc_path, &sts) == -1 && errno == ENOENT)
        {
            printf("UI process doesn't exist, exiting.\n");
            pthread_mutex_lock(&STARGATE->exit_mutex);
            exiting = 1;
            pthread_mutex_unlock(&STARGATE->exit_mutex);
            f_exited = 1;
            break;
        }
    }

    if(f_exited)
    {
        sleep(3);
        stop_engine();
        exit(1);
    }

    return (void*)0;
}


void print_help(){
    printf("Usage:\n\nStart the engine:\n");
    printf("%s install_prefix project_dir ui_pid "
            "huge_pages[--sleep --no-hardware]\n", STARGATE_VERSION);
    printf(
        "--no-hardware: Do not use audio or MIDI hardware, for debugging\n"
    );
    printf("--sleep: Sleep for 1ms between loops.  Implies --no-hardware\n\n");
    printf("Offline render:\n");
    printf("%s daw [project_dir] [output_file] [start_beat] "
        "[end_beat] [sample_rate] [buffer_size] [thread_count] "
        "[huge_pages] [stem] [sequence_uid]\n\n", STARGATE_VERSION);
}

#ifndef SG_DLL
int _main(int argc, char** argv){
    int j;

    for(j = 0; j < argc; ++j){
        printf("%i: %s\n", j, argv[j]);
    }

    if(argc < 2){
        print_help();
        return 1;
    } else if(!strcmp(argv[1], "daw")){
        return daw_render(argc, argv);
    } else if(argc < 5){
        print_help();
        return 9996;
    }

    int ui_pid = atoi(argv[3]);
    int f_huge_pages = atoi(argv[4]);
    assert(f_huge_pages == 0 || f_huge_pages == 1);

    if(f_huge_pages){
        printf("Attempting to use hugepages\n");
    }

    USE_HUGEPAGES = f_huge_pages;

    if(argc > 5){
        for(j = 5; j < argc; ++j){
            if(!strcmp(argv[j], "--sleep")){
                NO_HARDWARE_USLEEP = 1;
                NO_HARDWARE = 1;
            } else if(!strcmp(argv[j], "--no-hardware")){
                NO_HARDWARE = 1;
            } else {
                printf("Invalid argument [%i] %s\n", j, argv[j]);
            }
        }
    }

    set_thread_params();
    setup_signal_handling();
    start_ui_thread(ui_pid);
    start_osc_thread();

    char* _pidfile_path = pidfile_path();
    create_pidfile(_pidfile_path);

    start_engine(argv[2]);
    int result = main_loop();

    delete_file(_pidfile_path);
    free(_pidfile_path);

    return result;
}
#endif

int daw_render(int argc, char** argv){
    if(argc < 12){
        print_help();
        return 1;
    }

    SG_OFFLINE_RENDER = 1;

    char * f_project_dir = argv[2];
    char * f_output_file = argv[3];
    double f_start_beat = atof(argv[4]);
    double f_end_beat = atof(argv[5]);
    int f_sample_rate = atoi(argv[6]);
    int f_buffer_size = atoi(argv[7]);
    int f_thread_count = atoi(argv[8]);
    int f_huge_pages = atoi(argv[9]);
    int f_stem_render = atoi(argv[10]);
    int sequence_uid = atoi(argv[11]);

    assert(f_huge_pages == 0 || f_huge_pages == 1);

    if(f_huge_pages){
        printf("Attempting to use hugepages\n");
    }

    USE_HUGEPAGES = f_huge_pages;

    int f_create_file = 1;

    int f_i;
    for(f_i = 12; f_i < argc; ++f_i){
        if(!strcmp(argv[f_i], "--no-file")){
            f_create_file = 0;
        }
    }

    SGFLT** f_output;
    hpalloc((void**)&f_output, sizeof(SGFLT*) * 2);

    v_activate(f_thread_count, 0, f_project_dir, f_sample_rate, NULL, 0);

    /*
    AUDIO_INPUT_TRACK_COUNT = 2;
    v_activate(f_thread_count, 0, f_project_dir, f_sample_rate, NULL, 1);
    v_we_test();
    */

    for(f_i = 0; f_i < 2; ++f_i){
        hpalloc(
            (void**)&f_output[f_i],
            sizeof(SGFLT) * f_buffer_size
        );
    }

    for(f_i = 0; f_i < f_buffer_size; ++f_i){
        f_output[0][f_i] = 0.0f;
        f_output[1][f_i] = 0.0f;
    }

    STARGATE->sample_count = f_buffer_size;

    v_daw_offline_render_prep(DAW);

    v_daw_offline_render(
        DAW,
        f_start_beat,
        f_end_beat,
        f_output_file,
        f_create_file,
        f_stem_render,
        sequence_uid
    );

    v_destructor();

    return 0;
}

NO_OPTIMIZATION void init_master_vol(){
    printf("Setting master volume\n");
    char * f_master_vol_str = (char*)malloc(sizeof(char) * TINY_STRING);
    get_file_setting(f_master_vol_str, "master_vol", "0.0");
    SGFLT f_master_vol = atof(f_master_vol_str);
    free(f_master_vol_str);

    MASTER_VOL = f_db_to_linear(f_master_vol * 0.1);
    printf("MASTER_VOL = %f\n", MASTER_VOL);
}

#if defined(__linux__) && !defined(SG_DLL)
    NO_OPTIMIZATION void start_osc_thread(){
        printf("Starting OSC server thread\n");
        serverThread = lo_server_thread_new("19271", osc_error);
        lo_server_thread_add_method(
            serverThread,
            NULL,
            NULL,
            osc_message_handler,
            NULL
        );
        lo_server_thread_start(serverThread);
    }

    NO_OPTIMIZATION void start_ui_thread(int pid){
        printf("Starting UI monitor thread\n");
        pthread_attr_t f_ui_threadAttr;
        pthread_attr_init(&f_ui_threadAttr);

#ifdef __linux__
        struct sched_param param;
        param.__sched_priority = 1; //90;
        pthread_attr_setschedparam(&f_ui_threadAttr, &param);
#endif

        pthread_attr_setstacksize(&f_ui_threadAttr, 1000000); //8388608);
        pthread_attr_setdetachstate(&f_ui_threadAttr, PTHREAD_CREATE_DETACHED);

        pthread_t f_ui_monitor_thread;
        ui_thread_args * f_ui_thread_args = (ui_thread_args*)malloc(
            sizeof(ui_thread_args)
        );
        f_ui_thread_args->pid = pid;
        pthread_create(
            &f_ui_monitor_thread,
            &f_ui_threadAttr,
            ui_process_monitor_thread,
            (void*)f_ui_thread_args
        );
    }

    NO_OPTIMIZATION void setup_signal_handling(){
        printf("Setting up signal handling\n");
        setsid();
        sigemptyset (&_signals);
        sigaddset(&_signals, SIGHUP);
        sigaddset(&_signals, SIGINT);
        sigaddset(&_signals, SIGQUIT);
        sigaddset(&_signals, SIGPIPE);
        sigaddset(&_signals, SIGTERM);
        sigaddset(&_signals, SIGUSR1);
        sigaddset(&_signals, SIGUSR2);
        pthread_sigmask(SIG_BLOCK, &_signals, 0);

        signal(SIGINT, signalHandler);
        signal(SIGTERM, signalHandler);
        signal(SIGHUP, signalHandler);
        signal(SIGQUIT, signalHandler);
        pthread_sigmask(SIG_UNBLOCK, &_signals, 0);
    }

    NO_OPTIMIZATION void destruct_signal_handling(){
        printf("Destroying signal handling\n");
        sigemptyset(&_signals);
        sigaddset(&_signals, SIGHUP);
        pthread_sigmask(SIG_BLOCK, &_signals, 0);
        kill(0, SIGHUP);
    }
#endif

NO_OPTIMIZATION void set_thread_params(){
    printf("Setting thread params\n");
    if(setpriority(PRIO_PROCESS, 0, -20))
    {
        printf(
            "Unable to renice process (this was to be expected if "
            "the process is not running as root)\n"
        );
    }

    int f_current_proc_sched = sched_getscheduler(0);

    if(f_current_proc_sched == RT_SCHED){
        printf("Process scheduler already set to real-time.");
    } else {
        printf(
            "\n\nProcess scheduler set to %i, attempting to set "
            "real-time scheduler.\n",
            f_current_proc_sched
        );
        //Attempt to set the process priority to real-time
        const struct sched_param f_proc_param = {
            sched_get_priority_max(RT_SCHED)
        };
        printf("Attempting to set scheduler for process\n");
        sched_setscheduler(0, RT_SCHED, &f_proc_param);
        printf("Process scheduler is now %i\n\n", sched_getscheduler(0));
    }
}

NO_OPTIMIZATION void alloc_output_buffers(){
    printf("Allocating output buffers\n");
    hpalloc(
        (void**)&pluginOutputBuffers,
        2 * sizeof(SGFLT*)
    );

    int f_i;
    for(f_i = 0; f_i < 2; ++f_i){
        hpalloc(
            (void**)&pluginOutputBuffers[f_i],
            sizeof(SGFLT) * FRAMES_PER_BUFFER
        );
    }
}

NO_OPTIMIZATION int init_hardware(
    struct HardwareConfig* hardware_config
){
    printf("Initializing MIDI hardware\n");
#ifndef NO_MIDI
    open_midi_devices(hardware_config);
#endif
    printf("Initializing audio hardware\n");
    int result = open_audio_device(hardware_config);
    return result;
}

int start_engine(char* project_dir){
    int retcode = 0;
    struct HardwareConfig* hardware_config = load_hardware_config(
        default_device_file_path()
    );
    alloc_output_buffers();
    init_master_vol();
    printf("Activating\n");
#ifdef NO_MIDI
    v_activate(
        hardware_config->thread_count,
        hardware_config->thread_affinity,
        project_dir,
        hardware_config->sample_rate,
        NULL,
        1
    );
#else
    v_activate(
        hardware_config->thread_count,
        hardware_config->thread_affinity,
        project_dir,
        hardware_config->sample_rate,
        &MIDI_DEVICES,
        1
    );
#endif

    if(!NO_HARDWARE){
        retcode = init_hardware(hardware_config);
    }

#ifdef WITH_LIBLO
    printf("Sending ready message to the UI\n");
    v_queue_osc_message("ready", "");
#endif

    return retcode;
}

void stop_engine(){
    if(!NO_HARDWARE){
        close_audio_device();
    }

#ifndef NO_MIDI
    close_midi_devices();
#endif

    v_destructor();

#if defined(__linux__) && !defined(SG_DLL)
    destruct_signal_handling();
#endif
}

NO_OPTIMIZATION int main_loop(){
    int f_i;
    // only for no-hardware mode
    SGFLT * f_portaudio_input_buffer = NULL;
    SGFLT * f_portaudio_output_buffer = NULL;

    if(NO_HARDWARE){
        lmalloc(
            (void**)&f_portaudio_input_buffer,
            sizeof(SGFLT) * FRAMES_PER_BUFFER
        );
        lmalloc(
            (void**)&f_portaudio_output_buffer,
            sizeof(SGFLT) * FRAMES_PER_BUFFER
        );

        for(f_i = 0; f_i < FRAMES_PER_BUFFER; ++f_i){
            f_portaudio_input_buffer[f_i] = 0.0f;
            f_portaudio_output_buffer[f_i] = 0.0f;
        }
    }
    printf("Entering main loop\n");
    while(1){
        pthread_mutex_lock(&STARGATE->exit_mutex);
        if(exiting){
            pthread_mutex_unlock(&STARGATE->exit_mutex);
            break;
        }
        pthread_mutex_unlock(&STARGATE->exit_mutex);

        if(NO_HARDWARE){
            portaudioCallback(
                f_portaudio_input_buffer,
                f_portaudio_output_buffer,
                128,
                NULL,
                (PaStreamCallbackFlags)NULL,
                NULL
            );

            if(NO_HARDWARE_USLEEP){
                usleep(1000);
            }
        } else {
            sleep(1);
        }
    }

    printf("Exiting main loop\n");
    stop_engine();
    printf("Stargate main() returning\n\n\n");
    return 0;
}

int v_configure(
    const char * path,
    const char * key,
    const char * value
){
    if(!READY){
        int i;

        for(i = 0; i < 20; ++i){
            usleep(100000);

            if(READY){
                break;
            }
        }

        if(!READY){
            return 1;
        }
    }

    if(!strcmp(path, "/stargate/wave_edit"))
    {
        v_we_configure(key, value);
        return 0;
    }
    else if(!strcmp(path, "/stargate/daw"))
    {
        v_daw_configure(key, value);
        return 0;
    }
    else if(!strcmp(path, "/stargate/master"))
    {
        v_sg_configure(key, value);
        return 0;
    }

    return 1;
}

#ifdef WITH_LIBLO

int osc_debug_handler(
    const char *path,
    const char *types,
    lo_arg **argv,
    int argc,
    void *data,
    void *user_data
){
    int i;

    printf("got unhandled OSC message:\npath: <%s>\n", path);
    for(i = 0; i < argc; ++i){
        printf("arg %d '%c' ", i, types[i]);
        lo_arg_pp((lo_type)types[i], argv[i]);
        printf("\n");
    }

    return 1;
}

int osc_message_handler(
    const char *path,
    const char *types,
    lo_arg **argv,
    int argc,
    void *data,
    void *user_data
){
    const char *key = (const char *)&argv[0]->s;
    const char *value = (const char *)&argv[1]->s;

    printf("types: '%s'\n", types);
    assert(!strcmp(types, "ss"));

    if(v_configure(path, key, value)){
        return osc_debug_handler(path, types, argv, argc, data, user_data);
    } else {
        return 0;
    }
}

#endif

