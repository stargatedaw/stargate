#include <stdio.h>
#include <string.h>

#include "ipc.h"

void ipc_message_init(
    struct IpcMessage* ipc_msg,
    char* path,
    char* key,
    char* value
){
    strncpy(ipc_msg->path, path, 128);
    strncpy(ipc_msg->key, key, 64);
    strncpy(ipc_msg->value, value, 4096);
}

void decode_ipc_message(
    struct IpcMessage* self,
    char* message
){
    int i = 0;
    int j = 0;
    int start = 0;
    int stage = 0;
    char* current = self->path;
    while(1){
        if(message[i] == '\0'){
            current[j] = '\0';
            break;
        } else if(stage < 2 && message[i] == '\n'){
            current[j] = '\0';
            start = i + 1;
            j = 0;
            ++stage;

            if(stage == 1){
                current = self->key;
            } else if(stage == 2) {
                current = self->value;
            }
        } else {
            current[j] = message[i];
            ++j;
        }
        ++i;
    }
}

void encode_ipc_message(
    struct IpcMessage* self,
    char* data
){
    sprintf(
        data,
        "%s\n%s\n%s",
        self->path,
        self->key,
        self->value
    );
}
