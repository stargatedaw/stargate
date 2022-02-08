#include "globals.h"

volatile int exiting = 0;
volatile int READY = 0;
int SINGLE_THREAD = 0;
int UI_SEND_USLEEP = 30000;
pthread_mutex_t CONFIG_LOCK;

