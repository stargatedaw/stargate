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
#include <locale.h>
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
#include "audiodsp/lib/fftw_lock.h"
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
#include "soundcheck.h"
#include "stargate.h"
#include "wave_edit.h"
#include "worker.h"
#if SG_OS == _OS_MACOS
    #include <pthread/qos.h>
#endif

#ifndef NO_MIDI
    #include "hardware/midi.h"
#endif

#if SG_OS == _OS_LINUX
    sigset_t _signals;
#endif

#ifndef NO_MIDI
    t_midi_device_list MIDI_DEVICES = {};
    PmError f_midi_err;
#endif

pthread_t SOCKET_SERVER_THREAD;

// Insert a brief sleep between loop runs when running without hardware
static int NO_HARDWARE_USLEEP = 0;

void signalHandler(int sig){
    log_info("signal %d caught, trying to clean up and exit", sig);
    sg_exit();
}

typedef struct{
    int pid;
}ui_thread_args;

#if SG_OS != _OS_WINDOWS
NO_OPTIMIZATION void* ui_process_monitor_thread(
    void * a_thread_args
){
    ui_thread_args * f_thread_args = (ui_thread_args*)(a_thread_args);
    int f_exited = 0;

    while(!is_exiting()){
        sleep(1);
        if(kill(f_thread_args->pid, 0)){
            log_info(
                "UI process %i doesn't exist, exiting.",
                f_thread_args->pid
            );
            sg_exit();
            f_exited = 1;
            break;
        }
    }

    if(f_exited){
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
        "huge_pages frames_per_second worker_threds "
        "[--sleep --no-hardware]\n",
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
        "[huge_pages] [stem] [sequence_uid] [--no-print-progress] "
        "[--no-file]\n"
        "--no-print-progress: Do not print progress updates\n"
        "--no-file: Do not create the rendered file\n\n",
        STARGATE_VERSION
    );
    printf("Sound check (play a short test tone and exit):\n");
    printf("%s soundcheck [/path/to/device.txt]\n\n", STARGATE_VERSION);
}

int _main(int argc, SGPATHSTR** argv){
    setlocale(LC_ALL, "C.UTF-8");
#if SG_OS == _OS_LINUX
    struct timespec load_start, load_finish;
    clock_gettime(CLOCK_REALTIME, &load_start);
#endif
    log_info("Calling engine _main()");
    setup_signal_handling();
    pthread_mutex_init(&FFTW_LOCK, NULL);
    pthread_mutex_init(&CONFIG_LOCK, NULL);
    pthread_mutex_init(&EXIT_MUTEX, NULL);
    int j;

    for(j = 0; j < argc; ++j){
#if SG_OS == _OS_WINDOWS
        log_info("%i: %ls", j, argv[j]);
#else
        log_info("%i: %s", j, argv[j]);
#endif
    }

    if(argc < 2){
        print_help();
        return 1;
#if SG_OS == _OS_WINDOWS
    } else if(!wcscmp(argv[1], L"daw")){
        return daw_render(argc, argv);
    } else if(!wcscmp(argv[1], L"soundcheck")){
        return soundcheck(argc, argv);
#else
    } else if(!strcmp(argv[1], "daw")){
        return daw_render(argc, argv);
    } else if(!strcmp(argv[1], "soundcheck")){
        return soundcheck(argc, argv);
#endif
    } else if(argc < 7){
        print_help();
        return 9996;
    }

    sg_path_snprintf(
        INSTALL_PREFIX, 
        4096,
#if SG_OS == _OS_WINDOWS
        L"%ls",
#else
        "%s",
#endif
        argv[1]
    );
    int f_huge_pages = args_atoi(argv[4]);
    sg_assert(
        (int)(f_huge_pages == 0 || f_huge_pages == 1),
        "huge pages %i out of range 0 to 1 ",
        f_huge_pages
    );

    if(f_huge_pages){
        log_info("Attempting to use hugepages");
    }
    int fps = args_atoi(argv[5]);
    log_info("UI Frames per second: %i", fps);
    int ui_send_usleep = (int)(1000000. / (float)fps);
    int thread_count = args_atoi(argv[6]);
    sg_assert(
        thread_count >= 1 && thread_count <= 16,
        "Thread count %i out of range 1..16",
        thread_count
    );
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

    if(argc > 7){
        for(j = 7; j < argc; ++j){
#if SG_OS == _OS_WINDOWS
            if(!wcscmp(argv[j], L"--sleep")){
                NO_HARDWARE_USLEEP = 1;
                NO_HARDWARE = 1;
            } else if(!wcscmp(argv[j], L"--no-hardware")){
                NO_HARDWARE = 1;
            } else if(!wcscmp(argv[j], L"--single-thread")){
                SINGLE_THREAD = 1;
            } else {
                print_help();
                log_error("Invalid argument [%i] %ls", j, argv[j]);
                exit(1);
            }
#else
            if(!strcmp(argv[j], "--sleep")){
                NO_HARDWARE_USLEEP = 1;
                NO_HARDWARE = 1;
            } else if(!strcmp(argv[j], "--no-hardware")){
                NO_HARDWARE = 1;
            } else if(!strcmp(argv[j], "--single-thread")){
                SINGLE_THREAD = 1;
            } else {
                print_help();
                log_error("Invalid argument [%i] %s", j, argv[j]);
                exit(1);
            }
#endif
        }
    }

    set_thread_params();
    start_socket_thread();

    start_engine(argv[2], thread_count);
#if SG_OS != _OS_WINDOWS
    int ui_pid = args_atoi(argv[3]);
    start_ui_thread(ui_pid);
#endif
#if SG_OS == _OS_LINUX
    clock_gettime(CLOCK_REALTIME, &load_finish);
    v_print_benchmark(
        "project load",
        load_start,
        load_finish
    );
#endif
    int result = main_loop();

    return result;
}

int daw_render(int argc, SGPATHSTR** argv){
    if(argc < 12){
        print_help();
        return 1;
    }

    SG_OFFLINE_RENDER = 1;

    SGPATHSTR* f_project_dir = argv[2];
    SGPATHSTR* f_output_file = argv[3];
    double f_start_beat = args_atof(argv[4]);
    double f_end_beat = args_atof(argv[5]);
    int f_sample_rate = args_atoi(argv[6]);
    int f_buffer_size = args_atoi(argv[7]);
    int f_thread_count = args_atoi(argv[8]);
    int f_huge_pages = args_atoi(argv[9]);
    int f_stem_render = args_atoi(argv[10]);
    int sequence_uid = args_atoi(argv[11]);

    if(f_thread_count < 1 || f_thread_count > MAX_WORKER_THREADS){
        log_error(
            "Error: Thread count out of range 1-%i, exiting",
            MAX_WORKER_THREADS
        );
        exit(1);
    }

    sg_assert(
        (int)(f_huge_pages == 0 || f_huge_pages == 1),
        "huge pages '%i' out of range 0 to 1 ",
        f_huge_pages
    );

    if(f_huge_pages){
        log_info("Attempting to use hugepages");
    }

    USE_HUGEPAGES = f_huge_pages;

    int f_create_file = 1;
    int print_progress = 1;

    int f_i;
    for(f_i = 12; f_i < argc; ++f_i){
#if SG_OS == _OS_WINDOWS
        if(!wcscmp(argv[f_i], L"--no-file")){
            f_create_file = 0;
        } else if(!wcscmp(argv[f_i], L"--no-print-progress")){
            print_progress = 0;
        } else {
            print_help();
            log_error("Invalid argument [%i] %ls", f_i, argv[f_i]);
            exit(1);
        }
#else
        if(!strcmp(argv[f_i], "--no-file")){
            f_create_file = 0;
        } else if(!strcmp(argv[f_i], "--no-print-progress")){
            print_progress = 0;
        } else {
            print_help();
            log_error("Invalid argument [%i] %s", f_i, argv[f_i]);
            exit(1);
        }
#endif
    }

    SGFLT** f_output;
    hpalloc((void**)&f_output, sizeof(SGFLT*) * 2);

    v_activate(f_thread_count, f_project_dir, f_sample_rate, NULL, 0);

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
        sequence_uid,
        print_progress
    );

    v_destructor();

    return 0;
}

NO_OPTIMIZATION void init_main_vol(){
    log_info("Setting main volume");
    char * f_main_vol_str = (char*)malloc(sizeof(char) * TINY_STRING);
#if SG_OS == _OS_WINDOWS
    get_file_setting(f_main_vol_str, L"main_vol", "0.0");
#else
    get_file_setting(f_main_vol_str, "main_vol", "0.0");
#endif
    SGFLT f_main_vol = atof(f_main_vol_str);
    free(f_main_vol_str);

    MAIN_VOL = f_db_to_linear(f_main_vol * 0.1);
    log_info("MAIN_VOL = %f", MAIN_VOL);
}

NO_OPTIMIZATION void start_socket_thread(){
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
        "pthread_create failed with %i",
        result
    );
    set_thread_name(SOCKET_SERVER_THREAD, "Socket Server");
}

#if SG_OS != _OS_WINDOWS
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
        set_thread_name(f_ui_monitor_thread, "UI Monitor");
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
#if SG_OS != _OS_LINUX && SG_OS != _OS_MACOS
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

#if SG_OS == _OS_MACOS
    int qos_result = pthread_set_qos_class_self_np(
        QOS_CLASS_USER_INTERACTIVE,
        0
    );
    log_info("qos_result main: %i", qos_result);
#endif
}

NO_OPTIMIZATION void alloc_output_buffers(){
    log_info("Allocating output buffers");

    hpalloc(
        (void**)&pluginOutputBuffers,
        sizeof(struct SamplePair) * FRAMES_PER_BUFFER
    );
}

NO_OPTIMIZATION int init_audio_hardware(
    struct HardwareConfig* hardware_config
){
    log_info("Initializing audio hardware");
    int result = open_audio_device(hardware_config, portaudioCallback);
    return result;
}

int start_engine(SGPATHSTR* project_dir, int thread_count){
    int retcode = 0;
    struct HardwareConfig* hardware_config = load_hardware_config(
        default_device_file_path()
    );
    alloc_output_buffers();
    init_main_vol();
    log_info("Activating");
#ifdef NO_MIDI
    v_activate(
        thread_count,
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
        thread_count,
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
    READY = 1;
    log_info("Entering main loop");
    while(!is_exiting()){
        if(NO_HARDWARE){
            portaudioCallback(
                f_portaudio_input_buffer,
                f_portaudio_output_buffer,
                128,
                NULL,
                (PaStreamCallbackFlags)0,
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

