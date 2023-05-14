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

#if SG_OS == _OS_MACOS
    #include <pthread/qos.h>
#elif SG_OS == _OS_WINDOWS
    #include <Windows.h>
    #include <avrt.h>

    void _windows_thread_pro_audio(){
        HRESULT hr;
        HANDLE hTask;
        DWORD taskIndex = 0;
        hTask = AvSetMmThreadCharacteristics(TEXT("Pro Audio"), &taskIndex);
        if (hTask == NULL){
            hr = E_FAIL;
            log_error("Failed to set Windows thread characteristics: %ld", hr);
        }
    }
#endif

void * v_worker_thread(void* a_arg){
    t_thread_args * f_args = (t_thread_args*)(a_arg);
    t_sg_thread_storage * f_storage =
        &STARGATE->thread_storage[f_args->thread_num];
    v_pre_fault_thread_stack(f_args->stack_size);

    int f_thread_num = f_args->thread_num;
    pthread_cond_t * f_track_cond =
        &STARGATE->worker_threads[f_thread_num].track_cond;
    pthread_mutex_t * f_track_block_mutex =
        &STARGATE->worker_threads[f_thread_num].track_block_mutex;
    pthread_spinlock_t * f_lock =
        &STARGATE->worker_threads[f_thread_num].lock;

#if SG_OS == _OS_WINDOWS
    _windows_thread_pro_audio();
#endif

    while(1){
        pthread_mutex_lock(f_track_block_mutex);
        pthread_cond_wait(f_track_cond, f_track_block_mutex);
        pthread_mutex_unlock(f_track_block_mutex);
        pthread_spin_lock(f_lock);

        if(STARGATE->worker_threads[f_thread_num].track_thread_quit_notifier){
            STARGATE->worker_threads[
                f_thread_num].track_thread_quit_notifier = 2;
            pthread_spin_unlock(f_lock);
            log_info("Worker thread %i exiting...", f_thread_num);
            break;
        }

        if(f_storage->current_host == SG_HOST_DAW){
            v_daw_process(f_args->thread_num);
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
    struct SgWorkerThread* _thread;
    int f_stack_size = (1024 * 1024);

    if(SINGLE_THREAD){
        STARGATE->worker_thread_count = 1;
    } else {
        STARGATE->worker_thread_count = a_thread_count;
    }

    log_info("Spawning %i worker threads", STARGATE->worker_thread_count);

    pthread_attr_t threadAttr;
    pthread_attr_init(&threadAttr);

    pthread_attr_setstacksize(&threadAttr, f_stack_size);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
#if SG_OS != _OS_LINUX
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);
#endif
#if SG_OS == _OS_MACOS
    int sched_priority = (int)(
        (float)sched_get_priority_max(RT_SCHED) * 0.9
    );
    log_info("sched_priority: %i", sched_priority);
    int qos_result = pthread_attr_set_qos_class_np(
        &threadAttr,
        QOS_CLASS_USER_INTERACTIVE,
        0
    );
    log_info("qos_result worker: %i", qos_result);
    const struct sched_param rt_sched_param = {
        .sched_priority = sched_priority,
    };
#endif

    int f_i;
    char thread_name[64];

    for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i){
        _thread = &STARGATE->worker_threads[f_i];
        _thread->track_thread_quit_notifier = 0;
        t_thread_args * f_args = (t_thread_args*)malloc(
            sizeof(t_thread_args)
        );
        f_args->thread_num = f_i;
        f_args->stack_size = f_stack_size;

        //pthread_mutex_init(&STARGATE->track_cond_mutex[f_i], NULL);
        pthread_cond_init(&_thread->track_cond, NULL);
        pthread_spin_init(&_thread->lock, 0);
        pthread_mutex_init(&_thread->track_block_mutex, NULL);
#if SG_OS == _OS_MACOS
        pthread_setschedparam(
            STARGATE->worker_threads[f_i].thread,
            RT_SCHED,
            &rt_sched_param
        );
#endif
        pthread_create(
            &STARGATE->worker_threads[f_i].thread,
            &threadAttr,
            v_worker_thread,
            (void*)f_args
        );
        sg_snprintf(thread_name, 64, "Worker %i", f_i);
        set_thread_name(STARGATE->worker_threads[f_i].thread, thread_name);
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
        set_thread_name(STARGATE->audio_recording_thread, "Audio Recording");

        pthread_create(
            &STARGATE->osc_queue_thread,
            &auxThreadAttr,
            v_osc_send_thread,
            (void*)STARGATE
        );
        set_thread_name(STARGATE->osc_queue_thread, "OSC Queue");
        pthread_attr_destroy(&auxThreadAttr);
    }
}

// Crashes in GCC and Clang when optimized
NO_OPTIMIZATION void v_activate(
    int a_thread_count,
    SGPATHSTR* a_project_path,
    SGFLT a_sr,
    t_midi_device_list* a_midi_devices,
    int a_aux_threads
){
    /* Instantiate hosts */
    g_stargate_get(a_sr, a_midi_devices);

    STARGATE->hosts[SG_HOST_DAW] = (t_sg_host){
        .run = v_daw_run_engine,
        .osc_send = v_daw_osc_send,
        .audio_inputs = v_daw_update_audio_inputs,
        .mix = v_default_mix,
    };

    STARGATE->hosts[SG_HOST_WAVE_EDIT] = (t_sg_host){
        .run = v_run_wave_editor,
        .osc_send = v_we_osc_send,
        .audio_inputs = v_we_update_audio_inputs,
        .mix = v_default_mix,
    };

    g_daw_instantiate(a_sr);
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
    struct SgWorkerThread* _thread;

    SGPATHSTR tmp_sndfile_name[2048];

    pthread_mutex_lock(&STARGATE->audio_inputs_mutex);
    STARGATE->audio_recording_quit_notifier = 1;
    pthread_mutex_unlock(&STARGATE->audio_inputs_mutex);

    for(f_i = 0; f_i < AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        if(STARGATE->audio_inputs[f_i].sndfile)
        {
            sf_close(STARGATE->audio_inputs[f_i].sndfile);
            sg_path_snprintf(
                tmp_sndfile_name,
                2048,
#if SG_OS == _OS_WINDOWS
                L"%ls%i.wav",
#else
                "%s%i.wav",
#endif
                STARGATE->audio_tmp_folder,
                f_i
            );
#if SG_OS == _OS_WINDOWS
            log_info("Deleting %ls", tmp_sndfile_name);
            _wremove(tmp_sndfile_name);
#else
            log_info("Deleting %s", tmp_sndfile_name);
            remove(tmp_sndfile_name);
#endif
        }
    }

    pthread_spin_lock(&STARGATE->main_lock);

    for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i){
        _thread = &STARGATE->worker_threads[f_i];
        pthread_mutex_lock(&_thread->track_block_mutex);
        _thread->track_thread_quit_notifier = 1;
        pthread_cond_broadcast(&_thread->track_cond);
        pthread_mutex_unlock(&_thread->track_block_mutex);
    }

    pthread_spin_unlock(&STARGATE->main_lock);

    usleep(300000);

    //abort the application rather than hang indefinitely
    for(f_i = 1; f_i < STARGATE->worker_thread_count; ++f_i){
        _thread = &STARGATE->worker_threads[f_i];
        if(!pthread_spin_trylock(&_thread->lock)){
            log_warn("dtor: Unable to acquire lock for thread %i", f_i);
	}
        sg_assert(
            _thread->track_thread_quit_notifier == 2,
            "v_destructor: track_thread_quit_notifier[%i] %i != 2",
            f_i,
            _thread->track_thread_quit_notifier
        );
        pthread_spin_unlock(&_thread->lock);
    }
}

