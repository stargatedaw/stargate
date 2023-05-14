#include "globals.h"

volatile int exiting = 0;
volatile int READY = 0;
int SINGLE_THREAD = 0;
int UI_SEND_USLEEP = 30000;
pthread_mutex_t CONFIG_LOCK;
pthread_mutex_t EXIT_MUTEX;

int is_exiting(){
    int _exiting;
    pthread_mutex_lock(&EXIT_MUTEX);
    _exiting = exiting;
    pthread_mutex_unlock(&EXIT_MUTEX);
    return _exiting;
}

void sg_exit(){
    pthread_mutex_lock(&EXIT_MUTEX);
    exiting = 1;
    pthread_mutex_unlock(&EXIT_MUTEX);
}
