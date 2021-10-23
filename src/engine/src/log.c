#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "log.h"

void log_info(const char * format, ...){
    va_list args;
    va_start(args, format);
    vprintf(format, args);
    va_end (args);
}

void log_warn(const char * format, ...){
    va_list args;
    char _format[strlen(format) + 20];
    sprintf(_format, "WARNING: %s", format);
    va_start(args, format);
    vfprintf(stderr, _format, args);
    va_end(args);
}

void log_error(const char * format, ...){
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
}
