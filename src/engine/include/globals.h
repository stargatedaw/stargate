#ifndef SG_GLOBALS_H
#define SG_GLOBALS_H

#include <pthread.h>

typedef struct _t_stargate t_stargate;
extern t_stargate* STARGATE;
// 0 when the application is running, 1 after the shutdown sequence has begun
extern volatile int exiting;
extern volatile int READY;
// Override the hardware config to force a single thread
extern int SINGLE_THREAD;
extern int UI_SEND_USLEEP;
extern pthread_mutex_t CONFIG_LOCK;
extern pthread_mutex_t EXIT_MUTEX;

// Return 0 if the application is running, 1 if preparing to exit
int is_exiting();

// Initiate an orderly shutdown, this causes various thread loops to
// exit so that various threads may finish
void sg_exit();

#endif
