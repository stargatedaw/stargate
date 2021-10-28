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
#include "files.h"
#include "globals.h"
#include "ipc.h"
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

#if SG_OS == _OS_LINUX
    sigset_t _signals;
#endif

#ifndef NO_MIDI
    t_midi_device_list MIDI_DEVICES;
    PmError f_midi_err;
#endif

pthread_t SOCKET_SERVER_THREAD;

// Insert a brief sleep between loop runs when running without hardware
static int NO_HARDWARE_USLEEP = 0;

void signalHandler(int sig){
    log_info("signal %d caught, trying to clean up and exit", sig);
    pthread_mutex_lock(&STARGATE->exit_mutex);
    exiting = 1;
    pthread_mutex_unlock(&STARGATE->exit_mutex);
}

typedef struct{
    int pid;
}ui_thread_args;

#if SG_OS == _OS_LINUX
NO_OPTIMIZATION void * ui_process_monitor_thread(
    void * a_thread_args
){
    char f_proc_path[256];
    f_proc_path[0] = '\0';
    ui_thread_args * f_thread_args = (ui_thread_args*)(a_thread_args);
    sprintf(f_proc_path, "/proc/%i", f_thread_args->pid);
    struct stat sts;
    int f_exited = 0;

    while(!exiting){
        sleep(1);
        if (stat(f_proc_path, &sts) == -1 && errno == ENOENT){
            log_info("UI process doesn't exist, exiting.");
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
#endif

void print_help(){
    printf("Usage:\n\nStart the engine:\n");
    printf(
        "%s-engine install_prefix project_dir ui_pid "
        "huge_pages frames_per_second [--sleep --no-hardware]\n",
        STARGATE_VERSION
    );
    printf(
        "--no-hardware: Do not use audio or MIDI hardware, for debugging\n"
    );
    printf("--sleep: Sleep for 1ms between loops.  Implies --no-hardware\n\n");
    printf("Offline render:\n");
    printf(
        "%s daw [project_dir] [output_file] [start_beat] "
        "[end_beat] [sample_rate] [buffer_size] [thread_count] "
        "[huge_pages] [stem] [sequence_uid]\n\n",
        STARGATE_VERSION
    );
}

int _main(int argc, char** argv){
    log_info("Calling engine _main()");
    setup_signal_handling();
    int j;

    for(j = 0; j < argc; ++j){
        log_info("%i: %s", j, argv[j]);
    }

    if(argc < 2){
        print_help();
        return 1;
    } else if(!strcmp(argv[1], "daw")){
        return daw_render(argc, argv);
    } else if(argc < 6){
        print_help();
        return 9996;
    }

    int ui_pid = atoi(argv[3]);
    int f_huge_pages = atoi(argv[4]);
    sg_assert(
        (int)(f_huge_pages == 0 || f_huge_pages == 1),
        argv[4]
    );

    if(f_huge_pages){
        log_info("Attempting to use hugepages");
    }
    int fps = atoi(argv[5]);
    log_info("UI Frames per second: %i", fps);
    int ui_send_usleep = (int)(1000000. / (float)fps);
    if(ui_send_usleep < 15000){
        log_error(
            "Invalid FPS received: %i",
            fps
        );
        ui_send_usleep = 10000;
    } else if(ui_send_usleep > 100000){
        log_error(
            "Invalid FPS received: %i",
            fps
        );
        ui_send_usleep = 100000;
    }
    UI_SEND_USLEEP = ui_send_usleep;

    USE_HUGEPAGES = f_huge_pages;

    if(argc > 6){
        for(j = 6; j < argc; ++j){
            if(!strcmp(argv[j], "--sleep")){
                NO_HARDWARE_USLEEP = 1;
                NO_HARDWARE = 1;
            } else if(!strcmp(argv[j], "--no-hardware")){
                NO_HARDWARE = 1;
            } else if(!strcmp(argv[j], "--single-thread")){
                SINGLE_THREAD = 1;
            } else {
                log_info("Invalid argument [%i] %s", j, argv[j]);
            }
        }
    }

    set_thread_params();
#if SG_OS == _OS_LINUX
    start_ui_thread(ui_pid);
#endif
    start_osc_thread();

    start_engine(argv[2]);
    int result = main_loop();

    return result;
}

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

    sg_assert(
        (int)(f_huge_pages == 0 || f_huge_pages == 1),
        argv[9]
    );

    if(f_huge_pages){
        log_info("Attempting to use hugepages");
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

NO_OPTIMIZATION void init_main_vol(){
    log_info("Setting main volume");
    char * f_main_vol_str = (char*)malloc(sizeof(char) * TINY_STRING);
    get_file_setting(f_main_vol_str, "main_vol", "0.0");
    SGFLT f_main_vol = atof(f_main_vol_str);
    free(f_main_vol_str);

    MAIN_VOL = f_db_to_linear(f_main_vol * 0.1);
    log_info("MAIN_VOL = %f", MAIN_VOL);
}

NO_OPTIMIZATION void start_osc_thread(){
    ipc_init();
    log_info("Starting socket server thread");
    struct IpcServerThreadArgs* args = (struct IpcServerThreadArgs*)malloc(
        sizeof(struct IpcServerThreadArgs)
    );
    args->callback = v_configure;

    int result = pthread_create(
        &SOCKET_SERVER_THREAD,
        NULL,
        &ipc_server_thread,
        (void*)args
    );
    sg_assert(
        (int)(result == 0),
        NULL
    );
}

#if SG_OS == _OS_LINUX
    NO_OPTIMIZATION void start_ui_thread(int pid){
        log_info("Starting UI monitor thread");
        pthread_attr_t f_ui_threadAttr;
        pthread_attr_init(&f_ui_threadAttr);

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
#endif

NO_OPTIMIZATION void sigsegv_handler(int sig){
    log_error("Engine received SIGSEGV");
    sg_print_stack_trace();
    exit(SIGSEGV);
}

NO_OPTIMIZATION void setup_signal_handling(){
    log_info("Setting up signal handling");
#if SG_OS == _OS_LINUX
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
#endif
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    signal(SIGSEGV, sigsegv_handler);
#if SG_OS == _OS_LINUX
    signal(SIGHUP, signalHandler);
    signal(SIGQUIT, signalHandler);
    pthread_sigmask(SIG_UNBLOCK, &_signals, 0);
#endif
}


NO_OPTIMIZATION void destruct_signal_handling(){
#if SG_OS == _OS_LINUX
    log_info("Destroying signal handling");
    sigemptyset(&_signals);
    sigaddset(&_signals, SIGHUP);
    pthread_sigmask(SIG_BLOCK, &_signals, 0);
    kill(0, SIGHUP);
#endif
}


NO_OPTIMIZATION void set_thread_params(){
#if SG_OS != _OS_LINUX
    log_info("Setting thread params");
    int f_current_proc_sched = sched_getscheduler(0);

    if(f_current_proc_sched == RT_SCHED){
        log_info("Process scheduler already set to real-time.");
    } else {
        log_info(
            "Process scheduler set to %i, attempting to set "
            "real-time scheduler.",
            f_current_proc_sched
        );
        //Attempt to set the process priority to real-time
        const struct sched_param f_proc_param = {
            sched_get_priority_max(RT_SCHED) / 2
        };
        log_info("Attempting to set scheduler for process");
        sched_setscheduler(0, RT_SCHED, &f_proc_param);
        log_info("Process scheduler is now %i", sched_getscheduler(0));
    }
#endif
}

NO_OPTIMIZATION void alloc_output_buffers(){
    log_info("Allocating output buffers");
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

NO_OPTIMIZATION int init_audio_hardware(
    struct HardwareConfig* hardware_config
){
    log_info("Initializing audio hardware");
    int result = open_audio_device(hardware_config);
    return result;
}

int start_engine(char* project_dir){
    int retcode = 0;
    struct HardwareConfig* hardware_config = load_hardware_config(
        default_device_file_path()
    );
    alloc_output_buffers();
    init_main_vol();
    log_info("Activating");
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
    if(!NO_HARDWARE){
        log_info("Initializing MIDI hardware");
        open_midi_devices(hardware_config);
    }
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
        retcode = init_audio_hardware(hardware_config);
    }

    log_info("Sending ready message to the UI");
    v_queue_osc_message("ready", "");

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

    destruct_signal_handling();
    ipc_dtor();
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
    log_info("Entering main loop");
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

    log_info("Exiting main loop");
    stop_engine();
    log_info("Stargate main() returning");
    return 0;
}

int v_configure(
    char* path,
    char* key,
    char* value
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

    if(!strcmp(path, "/stargate/wave_edit")){
        v_we_configure(key, value);
        return 0;
    } else if(!strcmp(path, "/stargate/daw")){
        v_daw_configure(key, value);
        return 0;
    } else if(!strcmp(path, "/stargate/main")){
        v_sg_configure(key, value);
        return 0;
    }

    return 1;
}

