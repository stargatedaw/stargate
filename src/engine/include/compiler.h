#ifndef SG_COMPILER_H
#define SG_COMPILER_H

#define _OS_LINUX 0
#define _OS_WINDOWS 1
#define _OS_MACOS 2

#include <sndfile.h>

#if defined(_WIN64) || defined(_WIN32) || defined(__MINGW32__) || defined(__MINGW64__)
    #define SG_OS _OS_WINDOWS
    #define _UNICODE
    #define UNICODE
    #include <wchar.h>
    // Throws compiler warnings if not included before windows.h
    #include <winsock2.h>
    #include <windows.h>
    #define SGPATHSTR wchar_t
    #define args_atoi _wtoi
    #define args_atof _wtof
    SNDFILE* SG_SF_OPEN(wchar_t*, int, SF_INFO*);
#elif defined(__linux__)
    #define SG_OS _OS_LINUX
    #define SGPATHSTR char
    #define args_atoi atoi
    #define args_atof atof
    SNDFILE* SG_SF_OPEN(char*, int, SF_INFO*);
#elif defined(__APPLE__)
    #define SG_OS _OS_MACOS
    #define SGPATHSTR char
    #define args_atoi atoi
    #define args_atof atof
    SNDFILE* SG_SF_OPEN(char*, int, SF_INFO*);

#endif

extern SGPATHSTR INSTALL_PREFIX[4096];

//Required for sched.h
#ifndef __USE_GNU
    #define __USE_GNU
#endif

#ifndef _GNU_SOURCE
    #define _GNU_SOURCE
#endif


#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#if SG_OS == _OS_LINUX
    #include <sys/resource.h>
#else
    #include <sched.h>
    #ifndef RT_SCHED
        #define RT_SCHED SCHED_FIFO
    #endif
#endif

#include "log.h"

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

typedef SGFLT PluginData;

struct SamplePair {
    SGFLT left;
    SGFLT right;
};

#if SG_OS == _OS_MACOS

    #include <libkern/OSAtomic.h>
    #include <os/lock.h>

    #define pthread_spinlock_t os_unfair_lock
    #define pthread_spin_lock os_unfair_lock_lock
    #define pthread_spin_trylock os_unfair_lock_trylock
    #define pthread_spin_unlock os_unfair_lock_unlock

    void pthread_spin_init(os_unfair_lock * a_lock, void * a_opts);

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


#if SG_OS == _OS_LINUX

    void prefetch_range(void *addr, size_t len);

#endif

SGPATHSTR* get_home_dir();

#if SG_OS == _OS_WINDOWS
    #define REAL_PATH_SEP "\\"
#else
    #define REAL_PATH_SEP "/"
#endif

void v_self_set_thread_affinity();
void v_pre_fault_thread_stack(int stacksize);
/* Similar to stdlib assert(...), but prints a message and a stack trace
 * @cond: The condition to assert is true
 * @msg:  The message to print
 */
void sg_assert(int cond, char* msg, ...)
    __attribute__((format(printf, 2, 3)));
void sg_assert_ptr(void* cond, char* msg, ...)
    __attribute__((format(printf, 2, 3)));
void sg_abort(char* msg, ...) __attribute__((format(printf, 1, 2)));

// snprintf that aborts and logs a message when @size is exceeded
size_t sg_snprintf(
    char* str,
    size_t size,
    char* fmt,
    ...
) __attribute__((format(printf, 3, 4)));

// Sprintf function specifically for joining paths together
size_t sg_path_snprintf(
    SGPATHSTR* str,
    size_t size,
    SGPATHSTR* fmt,
    ...
); // __attribute__((format(printf, 3, 4)));

typedef struct {
    char padding1[CACHE_LINE_SIZE];
    SGFLT sample_rate;
    SGFLT sr_recip;
    int current_host;
    int five_ms;  // Standard 5ms audio fade out, in samples
    SGFLT five_ms_recip;
    char padding2[CACHE_LINE_SIZE];
} t_sg_thread_storage;

void sg_print_stack_trace();
void set_thread_name(pthread_t thread, const char* name);

#endif
