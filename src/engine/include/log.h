#ifndef SG_LOG_H
#define SG_LOG_H

void log_info(const char* format, ...) __attribute__((format(printf, 1, 2)));
void log_warn(const char* format, ...) __attribute__((format(printf, 1, 2)));
void log_error(const char* format, ...) __attribute__((format(printf, 1, 2)));

#endif
