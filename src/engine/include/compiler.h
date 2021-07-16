#ifndef SG_COMPILER_H
#define SG_COMPILER_H

//Required for sched.h
#ifndef __USE_GNU
    #define __USE_GNU
#endif

#ifndef _GNU_SOURCE
    #define _GNU_SOURCE
#endif


#include <pthread.h>
#include <sched.h>
#include <stdlib.h>
#include <stdio.h>
#ifdef __linux__
    #include <sys/resource.h>
#endif

#ifdef SCHED_DEADLINE
    //#define RT_SCHED SCHED_DEADLINE
    #define RT_SCHED SCHED_FIFO
#else
    #define RT_SCHED SCHED_FIFO
#endif

#ifndef SG_THREAD_LOCAL
    #define SG_THREAD_LOCAL
#endif

#define STARGATE_VERSION "stargate"
#define prefetch __builtin_prefetch
#define PREFETCH_STRIDE 64
#define likely(x)   __builtin_expect((x),1)
#define unlikely(x) __builtin_expect((x),0)
// Use forward-slash on all OS
#define PATH_SEP "/"


// Uncomment or pass in from the compiler to use double precision for audio
//#define SG_USE_DOUBLE
#ifdef SG_USE_DOUBLE
    #define SGFLT double
    #define sg_write_audio sf_writef_double
    #define sg_read_audio sf_readf_double
#else
    #define SGFLT float
    #define sg_write_audio sf_writef_float
    #define sg_read_audio sf_readf_float
#endif

#ifdef __APPLE__

    #include <libkern/OSAtomic.h>

    #define pthread_spinlock_t OSSpinLock
    #define pthread_spin_lock OSSpinLockLock
    #define pthread_spin_unlock OSSpinLockUnlock

    void pthread_spin_init(OSSpinLock * a_lock, void * a_opts);

#endif

#if defined(__linux__) && !defined(SG_DLL)
    #include <lo/lo.h>
    #define WITH_LIBLO
#endif

#if !defined(CACHE_LINE_SIZE)
    #define CACHE_LINE_SIZE 64
    #warning "CACHE_LINE_SIZE not defined by compiler defaulting to 64"
#elif (CACHE_LINE_SIZE < 64) || (CACHE_LINE_SIZE > 128)
    #undef CACHE_LINE_SIZE
    #define CACHE_LINE_SIZE 64
    #warning "CACHE_LINE_SIZE < 64 or > 128, using 64 as CACHE_LINE_SIZE"
#endif

// LLVM defines __GNUC__ , but doesn't implement it's built-ins
// GCC offers no defines that only mean it's compiled with GCC

#ifdef __clang__
    #define assume_aligned(x, y) (x)
    #define NO_OPTIMIZATION
#else
    #define assume_aligned(x, y) __builtin_assume_aligned((x), (y))
    #define NO_OPTIMIZATION __attribute__((optimize("-O0")))
#endif


#ifdef __linux__

    void prefetch_range(void *addr, size_t len);

#endif

char * get_home_dir();

#if defined(__MINGW32__) && !defined(_WIN32)
    #define _WIN32
#endif

#if defined(_WIN32)
    #define REAL_PATH_SEP "\\"
#else
    #define REAL_PATH_SEP "/"
#endif

void v_self_set_thread_affinity();
void v_pre_fault_thread_stack(int stacksize);

#endif

