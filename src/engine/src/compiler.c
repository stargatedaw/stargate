#include <assert.h>
#include <unistd.h>

#include "compiler.h"


#ifdef __APPLE__

void pthread_spin_init(OSSpinLock * a_lock, void * a_opts){
    *a_lock = 0;
}

#endif

#ifdef __linux__

void prefetch_range(void *addr, size_t len){
    char *cp;
    char *end = (char*)addr + len;

    for(cp = (char*)addr; cp < end; cp += PREFETCH_STRIDE){
        prefetch(cp);
    }
}

#endif

#if defined(_WIN32)
    #define REAL_PATH_SEP "\\"
    char * get_home_dir(){
        char * f_result = getenv("USERPROFILE");
        assert(f_result);
        return f_result;
    }
#else
    #define REAL_PATH_SEP "/"
    char * get_home_dir(){
        char * f_result = getenv("HOME");
        assert(f_result);
        return f_result;
    }
#endif

NO_OPTIMIZATION void v_self_set_thread_affinity(){
    v_pre_fault_thread_stack(1024 * 512);

#ifdef __linux__
    pthread_attr_t threadAttr;
    struct sched_param param;
    param.__sched_priority = sched_get_priority_max(RT_SCHED);
    printf(
        " Attempting to set pthread_self to .__sched_priority = %i\n",
        param.__sched_priority
    );
    pthread_attr_init(&threadAttr);
    pthread_attr_setschedparam(&threadAttr, &param);
    pthread_attr_setstacksize(&threadAttr, 1024 * 1024);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);

    pthread_t f_self = pthread_self();
    pthread_setschedparam(f_self, RT_SCHED, &param);
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    pthread_setaffinity_np(f_self, sizeof(cpu_set_t), &cpuset);

    pthread_attr_destroy(&threadAttr);
#endif
}

void v_pre_fault_thread_stack(int stacksize){
#ifdef __linux__
    int pagesize = sysconf(_SC_PAGESIZE);
    stacksize -= pagesize * 20;

    volatile char buffer[stacksize];
    int i;

    for (i = 0; i < stacksize; i += pagesize)
    {
        buffer[i] = i;
    }

    if(buffer[0]){}  //avoid a compiler warning
#endif
}

