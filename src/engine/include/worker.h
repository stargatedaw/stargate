#ifndef UTIL_WORKER_H
#define UTIL_WORKER_H

#include <unistd.h>

#include "stargate.h"
#include "compiler.h"
#include "hardware/midi.h"

#ifdef MACOS
    #include <sys/param.h>
    #include <sys/sysctl.h>
#endif


void* v_worker_thread(void*);
void v_init_worker_threads(int, int, int);

int getNumberOfCores();
void v_activate(
    int a_thread_count,
    int a_set_thread_affinity,
    char* a_project_path,
    SGFLT a_sr,
    t_midi_device_list* a_midi_devices,
    int a_aux_threads
);
void v_destructor();

#endif
