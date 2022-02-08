#include <stdio.h>
#include <string.h>

#include "compiler.h"
#include "ipc.h"


void ui_message_init(
    struct UIMessage* ui_msg,
    char* path,
    char* value
){
    int length = strlen(path);
    sg_assert(
        length < 128,
        "%i: %s",
        length,
        path
    );
    length = strlen(value);
    sg_assert(
        length < 8192,
        "%i: %s",
        length,
        value
    );
    strcpy(
        ui_msg->path,
        path
    );
    strcpy(
        ui_msg->value,
        value
    );
}

void decode_engine_message(
    struct EngineMessage* self,
    char* message
){
    int i = 0;
    int j = 0;
    int stage = 0;
    char* current = self->path;
    while(1){
        if(message[i] == '\0'){
            current[j] = '\0';
            break;
        } else if(stage < 2 && message[i] == '\n'){
            current[j] = '\0';
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

void encode_ui_message(
    struct UIMessage* self,
    char* data
){
    sg_snprintf(
        data,
        60128,
        "%s\n%s",
        self->path,
        self->value
    );
}
