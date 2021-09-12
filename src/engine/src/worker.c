//Required for sched.h
#ifndef __USE_GNU
    #define __USE_GNU
#endif

#include <pthread.h>
#include <sched.h>

#include "audio/item.h"
#include "audio/audio_pool.h"
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"
#include "daw.h"
#include "files.h"
#include "globals.h"
#include "osc.h"
#include "project.h"
#include "stargate.h"
#include "wave_edit.h"
#include "worker.h"

int READY = 0;

int getNumberOfCores(){
#if defined(WIN32)
    return atoi(getenv("NUMBER_OF_PROCESSORS"));
#elif defined(MACOS)
    int nm[2];
    size_t len = 4;
    uint32_t count;

    nm[0] = CTL_HW;
    nm[1] = HW_AVAILCPU;
    sysctl(nm, 2, &count, &len, NULL, 0);

    if(count < 1) {
        nm[1] = HW_NCPU;
        sysctl(nm, 2, &count, &len, NULL, 0);
        if(count < 1){
            count = 1;
        }
    }
    return count;
#elif defined(__linux__)
    return sysconf(_SC_NPROCESSORS_ONLN);
#else
    return 2;
#endif
}

void * v_worker_thread(void* a_arg){
    t_thread_args * f_args = (t_thread_args*)(a_arg);
    t_sg_thread_storage * f_storage =
        &STARGATE->thread_storage[f_args->thread_num];
    v_pre_fault_thread_stack(f_args->stack_size);

    int f_thread_num = f_args->thread_num;
    pthread_cond_t * f_track_cond = &STARGATE->track_cond[f_thread_num];
    pthread_mutex_t * f_track_block_mutex =
        &STARGATE->track_block_mutexes[f_thread_num];
    pthread_spinlock_t * f_lock = &STARGATE->thread_locks[f_thread_num];

    while(1)
    {
        pthread_cond_wait(f_track_cond, f_track_block_mutex);
        pthread_spin_lock(f_lock);

        if(STARGATE->track_thread_quit_notifier[f_thread_num])
        {
            pthread_spin_unlock(f_lock);
            STARGATE->track_thread_quit_notifier[f_thread_num] = 2;
            printf("Worker thread %i exiting...\n", f_thread_num);
            break;
        }

        if(f_storage->current_host == SG_HOST_DAW)
        {
            v_daw_process(f_args);
        }
        //else if...

        pthread_spin_unlock(f_lock);
    }

    return (void*)1;
}


void v_init_worker_threads(
    int a_thread_count,
    int a_set_thread_affinity,
    int a_aux_threads
){
    int f_stack_size = (1024 * 1024);
    int f_cpu_core_inc = 1;
    int f_cpu_count = getNumberOfCores();
    printf("Detected %i cpu cores\n", f_cpu_count);

    if(f_cpu_count < 1)
    {
        f_cpu_count = 1;
    }

    if(SINGLE_THREAD){
        STARGATE->worker_thread_count = 1;
    } else if(a_thread_count == 0){  // auto, select for the user
        // 2 thread SMT is assumed now
        // Stargate is very CPU efficient, it is unlikely that anybody needs
        // so much processing power.
        int core_count = f_cpu_count / 2;
        if(core_count >= 9){
            STARGATE->worker_thread_count = 4;
        } else if(core_count >= 6){
            STARGATE->worker_thread_count = 3;
        } else if(core_count == 1){
            STARGATE->worker_thread_count = 1;
        } else {
            STARGATE->worker_thread_count = 2;
        }
    } else {
        if(a_thread_count > f_cpu_count){
            STARGATE->worker_thread_count = f_cpu_count;
        } else {
            STARGATE->worker_thread_count = a_thread_count;
        }
    }

    if((STARGATE->worker_thread_count * 2) <= f_cpu_count){
        f_cpu_core_inc = f_cpu_count / STARGATE->worker_thread_count;

        if(f_cpu_core_inc < 2){
            f_cpu_core_inc = 2;
        } else if(f_cpu_core_inc > 4){
            f_cpu_core_inc = 4;
        }
    }

    printf("Spawning %i worker threads\n", STARGATE->worker_thread_count);

    STARGATE->track_block_mutexes = (pthread_mutex_t*)malloc(
        sizeof(pthread_mutex_t) * (STARGATE->worker_thread_count));
    STARGATE->worker_threads = (pthread_t*)malloc(
        sizeof(pthread_t) * (STARGATE->worker_thread_count));

    hpalloc((void**)&STARGATE->track_thread_quit_notifier,
        (sizeof(int) * (STARGATE->worker_thread_count)));

    hpalloc((void**)&STARGATE->track_cond,
        sizeof(pthread_cond_t) * (STARGATE->worker_thread_count));

    hpalloc((void**)&STARGATE->thread_locks,
        sizeof(pthread_spinlock_t) * (STARGATE->worker_thread_count));

    pthread_attr_t threadAttr;
    pthread_attr_init(&threadAttr);

#ifdef __linux__
    struct sched_param param;
    param.__sched_priority = sched_get_priority_max(RT_SCHED);
    printf(" Attempting to set .__sched_priority = %i\n",
            param.__sched_priority);
    pthread_attr_setschedparam(&threadAttr, &param);
#endif

    pthread_attr_setstacksize(&threadAttr, f_stack_size);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);

    //pthread_t f_self = pthread_self();
    //pthread_setschedparam(f_self, RT_SCHED, &param);

    int f_cpu_core = 0;
    int f_i;

    for(f_i = 0; f_i < (STARGATE->worker_thread_count); ++f_i)
    {
        STARGATE->track_thread_quit_notifier[f_i] = 0;
        t_thread_args * f_args = (t_thread_args*)malloc(
            sizeof(t_thread_args)
        );
        f_args->thread_num = f_i;
        f_args->stack_size = f_stack_size;

        if(f_i == 0){
            STARGATE->main_thread_args = (void*)f_args;
        }
        //pthread_mutex_init(&STARGATE->track_cond_mutex[f_i], NULL);
        pthread_cond_init(&STARGATE->track_cond[f_i], NULL);
        pthread_spin_init(&STARGATE->thread_locks[f_i], 0);
        pthread_mutex_init(&STARGATE->track_block_mutexes[f_i], NULL);
        pthread_create(
            &STARGATE->worker_threads[f_i],
            &threadAttr,
            v_worker_thread,
            (void*)f_args
        );

#ifdef __linux__
        if(a_set_thread_affinity){
            cpu_set_t cpuset;
            CPU_ZERO(&cpuset);
            CPU_SET(f_cpu_core, &cpuset);
            pthread_setaffinity_np(
                STARGATE->worker_threads[f_i],
                sizeof(cpu_set_t),
                &cpuset
            );
            printf(
                "Locked thread %i to core %i\n",
                f_i,
                f_cpu_core
            );
            //sched_setaffinity(0, sizeof(cpu_set_t), &cpuset);
            f_cpu_core += f_cpu_core_inc;
        }

        struct sched_param param2;
        int f_applied_policy = 0;
        pthread_getschedparam(
            STARGATE->worker_threads[f_i],
            &f_applied_policy, &param2
        );

        if(f_applied_policy == RT_SCHED){
            printf("Scheduling successfully applied with priority %i\n ",
                    param2.__sched_priority);
        } else {
            printf("Scheduling was not successfully applied\n");
        }
#endif
    }

    pthread_attr_destroy(&threadAttr);
    STARGATE->audio_recording_quit_notifier = 0;

    if(a_aux_threads){
        pthread_attr_t auxThreadAttr;
        pthread_attr_init(&auxThreadAttr);
        pthread_attr_setdetachstate(&auxThreadAttr, PTHREAD_CREATE_DETACHED);
        pthread_attr_setstacksize(&auxThreadAttr, (1024 * 1024));

        pthread_create(
            &STARGATE->audio_recording_thread,
            &auxThreadAttr,
            v_audio_recording_thread,
            NULL
        );

        pthread_create(
            &STARGATE->osc_queue_thread,
            &auxThreadAttr,
            v_osc_send_thread,
            (void*)STARGATE
        );
        pthread_attr_destroy(&auxThreadAttr);
    }
}

// Crashes in GCC and Clang when optimized
NO_OPTIMIZATION void v_activate(
    int a_thread_count,
    int a_set_thread_affinity,
    char* a_project_path,
    SGFLT a_sr,
    t_midi_device_list* a_midi_devices,
    int a_aux_threads
){
    /* Instantiate hosts */
    g_stargate_get(a_sr, a_midi_devices);

    STARGATE->hosts[SG_HOST_DAW].run = v_daw_run_engine;
    STARGATE->hosts[SG_HOST_DAW].osc_send = v_daw_osc_send;
    STARGATE->hosts[SG_HOST_DAW].audio_inputs = v_daw_update_audio_inputs;
    STARGATE->hosts[SG_HOST_DAW].mix = v_default_mix;

    STARGATE->hosts[SG_HOST_WAVE_EDIT].run = v_run_wave_editor;
    STARGATE->hosts[SG_HOST_WAVE_EDIT].osc_send = v_we_osc_send;
    STARGATE->hosts[SG_HOST_WAVE_EDIT].audio_inputs = v_we_update_audio_inputs;
    STARGATE->hosts[SG_HOST_WAVE_EDIT].mix = v_default_mix;

    g_daw_instantiate();
    g_wave_edit_get();

    printf("Opening project\n");
    v_open_project(a_project_path, 1);

    char * f_host_str = (char*)malloc(sizeof(char) * TINY_STRING);
    get_file_setting(f_host_str, "host", "0");
    int f_host = atoi(f_host_str);
    printf("Last host:  %i\n", f_host);
    free(f_host_str);

    v_set_host(f_host);

    printf("Initializing worker threads\n");
    v_init_worker_threads(
        a_thread_count,
        a_set_thread_affinity,
        a_aux_threads
    );

#ifdef __linux__
    mlockall(MCL_CURRENT | MCL_FUTURE);
#endif

    READY = 1;
}

void v_destructor(){
    int f_i;

    char tmp_sndfile_name[2048];

    pthread_mutex_lock(&STARGATE->audio_inputs_mutex);
    STARGATE->audio_recording_quit_notifier = 1;
    pthread_mutex_unlock(&STARGATE->audio_inputs_mutex);

    for(f_i = 0; f_i < AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        if(STARGATE->audio_inputs[f_i].sndfile)
        {
            sf_close(STARGATE->audio_inputs[f_i].sndfile);
            sprintf(
                tmp_sndfile_name, "%s%i.wav",
                STARGATE->audio_tmp_folder,
                f_i
            );
            printf("Deleting %s\n", tmp_sndfile_name);
            remove(tmp_sndfile_name);
        }
    }

    pthread_spin_lock(&STARGATE->main_lock);

    for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i)
    {
        pthread_mutex_lock(&STARGATE->track_block_mutexes[f_i]);
        STARGATE->track_thread_quit_notifier[f_i] = 1;
        pthread_cond_broadcast(&STARGATE->track_cond[f_i]);
        pthread_mutex_unlock(&STARGATE->track_block_mutexes[f_i]);
    }

    pthread_spin_unlock(&STARGATE->main_lock);

    usleep(300000);

    //abort the application rather than hang indefinitely
    for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i){
        assert(STARGATE->track_thread_quit_notifier[f_i] == 2);
    }
}

