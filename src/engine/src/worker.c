#include <pthread.h>

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
            log_info("Worker thread %i exiting...", f_thread_num);
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
    int a_aux_threads
){
    int f_stack_size = (1024 * 1024);

    if(SINGLE_THREAD){
        STARGATE->worker_thread_count = 1;
    } else {
        STARGATE->worker_thread_count = a_thread_count;
    }

    log_info("Spawning %i worker threads", STARGATE->worker_thread_count);

    STARGATE->track_block_mutexes = (pthread_mutex_t*)malloc(
        sizeof(pthread_mutex_t) * (STARGATE->worker_thread_count)
    );
    STARGATE->worker_threads = (pthread_t*)malloc(
        sizeof(pthread_t) * (STARGATE->worker_thread_count)
    );

    hpalloc(
        (void**)&STARGATE->track_thread_quit_notifier,
        sizeof(int) * STARGATE->worker_thread_count
    );

    hpalloc(
        (void**)&STARGATE->track_cond,
        sizeof(pthread_cond_t) * STARGATE->worker_thread_count
    );

    hpalloc(
        (void**)&STARGATE->thread_locks,
        sizeof(pthread_spinlock_t) * STARGATE->worker_thread_count
    );

    pthread_attr_t threadAttr;
    pthread_attr_init(&threadAttr);

    pthread_attr_setstacksize(&threadAttr, f_stack_size);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
#if SG_OS != _OS_LINUX
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);
#endif
#if SG_OS == _OS_MACOS
    int sched_priority = (int)((float)sched_get_priority_max(RT_SCHED) * 0.9);
    log_info("sched_priority: %i", sched_priority);
    const struct sched_param rt_sched_param = {
        .sched_priority = sched_priority,
    };
#endif

    int f_i;

    for(f_i = 0; f_i < STARGATE->worker_thread_count; ++f_i){
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
#if SG_OS == _OS_MACOS
        pthread_setschedparam(
            STARGATE->worker_threads[f_i],
            RT_SCHED,
            &rt_sched_param
        );
#endif
        pthread_create(
            &STARGATE->worker_threads[f_i],
            &threadAttr,
            v_worker_thread,
            (void*)f_args
        );
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

    log_info("Opening project");
    v_open_project(a_project_path, 1);

    v_set_host(SG_HOST_DAW);

    log_info("Initializing worker threads");
    v_init_worker_threads(
        a_thread_count,
        a_aux_threads
    );

#if SG_OS == _OS_LINUX
    mlockall(MCL_CURRENT | MCL_FUTURE);
#endif
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
            sg_snprintf(
                tmp_sndfile_name,
                2048,
                "%s%i.wav",
                STARGATE->audio_tmp_folder,
                f_i
            );
            log_info("Deleting %s", tmp_sndfile_name);
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
        sg_assert(
            STARGATE->track_thread_quit_notifier[f_i] == 2,
            "v_destructor: track_thread_quit_notifier %i != 2",
            STARGATE->track_thread_quit_notifier[f_i]
        );
    }
}

