#ifndef UTIL_OSC_H
#define UTIL_OSC_H

#define OSC_SEND_QUEUE_SIZE 256
#define OSC_MAX_MESSAGE_SIZE 65536

struct OscKeyPair {
    char key[32];
    char value[OSC_MAX_MESSAGE_SIZE];
};

typedef struct{
    char f_tmp1[OSC_MAX_MESSAGE_SIZE];
    char f_tmp2[OSC_MAX_MESSAGE_SIZE];
    char f_msg[OSC_MAX_MESSAGE_SIZE];
    struct OscKeyPair messages[OSC_SEND_QUEUE_SIZE];
}t_osc_send_data;

void* v_osc_send_thread(void* a_arg);

/* Send an OSC message to the UI.  The UI will have a handler that accepts
 * key/value pairs as commands.  This is safe to use while processing audio
 * , as it will not context switch.
 *
 * a_key:   A key that the UI host will recognize
 * a_value: The value, or an empty string if not value is required
 */
void v_queue_osc_message(
    char* a_key,
    char * a_val
);

#endif
