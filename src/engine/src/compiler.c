#include "compiler.h"
#if SG_OS == _OS_WINDOWS
    #include <windows.h>
    #include <DbgHelp.h>
#else
    #include <execinfo.h>
#endif

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>


SGPATHSTR INSTALL_PREFIX[4096];

#if SG_OS == _OS_MACOS
    #include <os/lock.h>
    void pthread_spin_init(os_unfair_lock * a_lock, void * a_opts){
        os_unfair_lock lock = OS_UNFAIR_LOCK_INIT;
        *a_lock = lock;
    }
#endif

#if SG_OS == _OS_LINUX
    void prefetch_range(void *addr, size_t len){
        char *cp;
        char *end = (char*)addr + len;

        for(cp = (char*)addr; cp < end; cp += PREFETCH_STRIDE){
            prefetch(cp);
        }
    }

#endif

#if SG_OS == _OS_WINDOWS
    SGPATHSTR* get_home_dir(){
        wchar_t * f_result = _wgetenv(L"USERPROFILE");
        sg_assert_ptr(f_result, "_wgetenv(USERPROFILE) returned NULL");
        return f_result;
    }
    SNDFILE* SG_SF_OPEN(wchar_t* path, int mode, SF_INFO* info){
        SNDFILE* result = sf_wchar_open((LPCWSTR)path, mode, info);
	sg_assert_ptr(result, "Could not open %ls", path);
	return result;
    }
#else
    SGPATHSTR* get_home_dir(){
        char * f_result = getenv("HOME");
        sg_assert_ptr(f_result, "getenv(HOME) returned NULL");
        return f_result;
    }
    SNDFILE* SG_SF_OPEN(char* path, int mode, SF_INFO* info){
        SNDFILE* result = sf_open((const char*)path, mode, info);
	sg_assert_ptr(result, "Could not open %s", path);
	return result;
    }
#endif

NO_OPTIMIZATION void v_self_set_thread_affinity(){
    v_pre_fault_thread_stack(1024 * 512);

#if SG_OS == _OS_LINUX
    pthread_attr_t threadAttr;
    pthread_attr_init(&threadAttr);
    pthread_attr_setstacksize(&threadAttr, 1024 * 1024);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);

    pthread_t f_self = pthread_self();
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    pthread_setaffinity_np(f_self, sizeof(cpu_set_t), &cpuset);
    pthread_attr_destroy(&threadAttr);
#endif
}

void v_pre_fault_thread_stack(int stacksize){
#if SG_OS == _OS_LINUX
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


void sg_print_stack_trace(){
#if SG_OS == _OS_WINDOWS
    size_t i;
    int line_num;
    char sym_name[256];
    char file_name[1024];
    HANDLE process = GetCurrentProcess();
    HANDLE thread = GetCurrentThread();

    CONTEXT context;
    memset(&context, 0, sizeof(CONTEXT));
    context.ContextFlags = CONTEXT_FULL;
    RtlCaptureContext(&context);

    SymInitialize(process, NULL, TRUE);

    DWORD image;
    STACKFRAME64 stackframe;
    IMAGEHLP_LINE64 line64;
    ZeroMemory(&stackframe, sizeof(STACKFRAME64));

#ifdef _M_IX86
    image = IMAGE_FILE_MACHINE_I386;
    stackframe.AddrPC.Offset = context.Eip;
    stackframe.AddrPC.Mode = AddrModeFlat;
    stackframe.AddrFrame.Offset = context.Ebp;
    stackframe.AddrFrame.Mode = AddrModeFlat;
    stackframe.AddrStack.Offset = context.Esp;
    stackframe.AddrStack.Mode = AddrModeFlat;
#elif _M_X64
    image = IMAGE_FILE_MACHINE_AMD64;
    stackframe.AddrPC.Offset = context.Rip;
    stackframe.AddrPC.Mode = AddrModeFlat;
    stackframe.AddrFrame.Offset = context.Rsp;
    stackframe.AddrFrame.Mode = AddrModeFlat;
    stackframe.AddrStack.Offset = context.Rsp;
    stackframe.AddrStack.Mode = AddrModeFlat;
#endif

    log_info("Traceback (most recent call first):");
    for(i = 0; i < 100; i++){
        BOOL result = StackWalk64(
            image,
            process,
            thread,
            &stackframe,
            &context,
            NULL,
            SymFunctionTableAccess64,
            SymGetModuleBase64,
            NULL
        );

        if(!result){
            break;
        }

        char buffer[sizeof(SYMBOL_INFO) + MAX_SYM_NAME * sizeof(TCHAR)];
        PSYMBOL_INFO symbol = (PSYMBOL_INFO)buffer;
        symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
        symbol->MaxNameLen = MAX_SYM_NAME;

        DWORD64 displacement64 = 0;
        DWORD displacement32 = 0;
        if(SymFromAddr(
            process,
            stackframe.AddrPC.Offset,
            &displacement64,
            symbol
        )){
            strcpy(sym_name, symbol->Name);
        } else {
            strcpy(sym_name, "???");
        }
        if(SymGetLineFromAddr64(
            process,
            stackframe.AddrPC.Offset,
            &displacement32,
            &line64
        )){
            line_num = line64.LineNumber;
            strcpy(file_name, line64.FileName);
        } else {
            line_num = -1;
            sprintf(file_name, "???");
        }

        log_info("[%i] %s %s:%i", (int)i, sym_name, file_name, line_num);
    }

    SymCleanup(process);
#else
    void* callstack[128];
    int frames;

    frames = backtrace(callstack, 128);
    backtrace_symbols_fd(callstack + 2, frames - 2, STDERR_FILENO);
#endif
}

static void _sg_abort(va_list args, char* msg){
    char _str[4096];
    if(msg){
        vsprintf(_str, msg, args);
        log_error("Assertion failed: %s", _str);
    } else {
        log_error("Assertion failed: no message provided");
    }
    sg_print_stack_trace();
    abort();
}

void sg_abort(char* msg, ...){
    va_list args;
    va_start(args, msg);
    _sg_abort(args, msg);
}

void sg_assert(int cond, char* msg, ...){
    if(unlikely(!cond)){
        va_list args;
        va_start(args, msg);
        _sg_abort(args, msg);
    }
}

void sg_assert_ptr(void* cond, char* msg, ...){
    if(unlikely(!cond)){
        va_list args;
        va_start(args, msg);
        _sg_abort(args, msg);
    }
}

size_t sg_snprintf(
    char* str,
    size_t size,
    char* fmt,
    ...
){
    size_t length;
    va_list args;
    va_start(args, fmt);
    length = vsnprintf(str, size, fmt, args);
    va_end(args);
    sg_assert(
        length < size,
        "length %i < size %i",
        (int)length,
        (int)size
    );
    return length;
}

size_t sg_path_snprintf(
    SGPATHSTR* str,
    size_t size,
    SGPATHSTR* fmt,
    ...
){
    size_t length;
    va_list args;
    va_start(args, fmt);
#if SG_OS == _OS_WINDOWS
    length = vswprintf(str, size, fmt, args);
#else
    length = vsnprintf(str, size, fmt, args);
#endif
    va_end(args);
    sg_assert(
        length < size,
        "length %i < size %i",
        (int)length,
        (int)size
    );
    return length;
}

void set_thread_name(pthread_t thread, const char* name){
#if SG_OS == _OS_LINUX
    pthread_setname_np(thread, name);
#endif
}
