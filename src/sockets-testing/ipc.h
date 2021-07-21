#ifndef SG_IPC_H
#define SG_IPC_H

#define IPC_MAX_MESSAGE_SIZE 24576

struct IpcServerThreadArgs{
    int (*callback)(char*, char*, char*);
};

// A message sent to the UI
struct UIMessage{
    char path[128];
    char value[IPC_MAX_MESSAGE_SIZE];
};

// A message sent from the UI to the engine
struct EngineMessage{
    char path[128];
    char key[64];
    char value[IPC_MAX_MESSAGE_SIZE];
};

void ui_message_init(
    struct UIMessage* ui_msg,
    char* path,
    char* value
);
void decode_engine_message(
    struct EngineMessage* self,
    char* message
);
void encode_ui_message(
    struct UIMessage* self,
    char* data
);

void ipc_client_send(char* message);
void* ipc_server_thread(void*);

#endif
