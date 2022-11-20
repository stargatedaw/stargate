#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "audiodsp/lib/lmalloc.h"
#include "stargate.h"
#include "compiler.h"
#include "globals.h"
#include "osc.h"


void* v_osc_send_thread(void* a_arg){
    t_osc_send_data* f_send_data;
    int f_i;
    int quit_notifier;

    hpalloc(
        (void**)&f_send_data,
        sizeof(t_osc_send_data)
    );

    for(f_i = 0; f_i < OSC_SEND_QUEUE_SIZE; ++f_i){
        f_send_data->messages[f_i].key[0] = '\0';
        f_send_data->messages[f_i].value[0] = '\0';
    }

    f_send_data->f_tmp1[0] = '\0';
    f_send_data->f_tmp2[0] = '\0';
    f_send_data->f_msg[0] = '\0';

    while(1){
        pthread_mutex_lock(&STARGATE->audio_inputs_mutex);
        quit_notifier = STARGATE->audio_recording_quit_notifier;
        pthread_mutex_unlock(&STARGATE->audio_inputs_mutex);
        if(quit_notifier){
            break;
        }

        STARGATE->current_host->osc_send(f_send_data);
        usleep(UI_SEND_USLEEP);
    }

    log_info("osc send thread exiting");

    return (void*)1;
}

/* Send an OSC message to the UI.  The UI will have a handler that accepts
 * key/value pairs as commands.  This is safe to use while processing audio
 * , as it will not context switch.
 *
 * a_key:   A key that the UI host will recognize
 * a_value: The value, or an empty string if not value is required
 */
void v_queue_osc_message(char* a_key, char* a_val){
    pthread_spin_lock(&STARGATE->ui_spinlock);
    if(STARGATE->osc_queue_index >= OSC_SEND_QUEUE_SIZE){
        log_info(
            "Dropping OSC event to prevent buffer overrun: %s|%s",
            a_key,
            a_val
        );
    } else {
        sg_snprintf(
            STARGATE->osc_messages[STARGATE->osc_queue_index].key,
            32,
            "%s",
            a_key
        );
        sg_snprintf(
            STARGATE->osc_messages[STARGATE->osc_queue_index].value,
            OSC_MAX_MESSAGE_SIZE,
            "%s",
            a_val
        );
        ++STARGATE->osc_queue_index;
    }
    pthread_spin_unlock(&STARGATE->ui_spinlock);
}

