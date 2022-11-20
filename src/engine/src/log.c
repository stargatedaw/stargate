#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "log.h"

void _log_format(char* buffer, char* prefix, const char* format){
    sprintf(buffer, "%s%s\n", prefix, format);
}

void log_info(
    const char * format,
    ...
){
    va_list args;
    char buffer[strlen(format) + 20];
    _log_format(buffer, "", format);
    va_start(args, format);
    vprintf(buffer, args);
    va_end (args);
}

void log_warn(
    const char * format,
    ...
){
    va_list args;
    char buffer[strlen(format) + 20];
    _log_format(buffer, "WARNING: ", format);
    va_start(args, format);
    vfprintf(stderr, buffer, args);
    va_end(args);
}

void log_error(
    const char * format,
    ...
){
    va_list args;
    char buffer[strlen(format) + 20];
    _log_format(buffer, "", format);
    va_start(args, format);
    vfprintf(stderr, buffer, args);
    va_end(args);
}
