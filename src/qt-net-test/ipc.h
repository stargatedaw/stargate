
struct IpcMessage{
    char path[128];
    char key[64];
    char value[4096];
};

void ipc_message_init(
    struct IpcMessage* ipc_msg,
    char* path,
    char* key,
    char* value
);
void decode_ipc_message(
    struct IpcMessage* self,
    char* message
);
void encode_ipc_message(
    struct IpcMessage* self,
    char* data
);

void ipc_client_send(char* message);
void ipc_server_thread();

