#ifndef SG_GLOBALS_H
#define SG_GLOBALS_H

#include <pthread.h>

// 0 when the application is running, 1 after the shutdown sequence has begun
extern volatile int exiting;
extern volatile int READY;
// Override the hardware config to force a single thread
extern int SINGLE_THREAD;
extern int UI_SEND_USLEEP;
extern pthread_mutex_t CONFIG_LOCK;

#endif
