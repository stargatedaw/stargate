#include "compiler.h"

#if SG_OS == _OS_WINDOWS

#define WIN32_LEAN_AND_MEAN
#undef UNICODE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#include "globals.h"
#include "ipc.h"

struct SocketData{
    struct sockaddr_in si_other;
    int s;
    int slen;
    fd_set fds;
    struct timeval tv;
};

static struct SocketData SOCKET_DATA;

void ipc_init(){
    WSADATA wsa;

    log_info("Initializing Winsock...");
    if(WSAStartup(MAKEWORD(2,2), &wsa) != 0){
        log_error(
            "Failed to initialize winsock. Error Code : %d",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    log_info("Initialised winsock.");

    SOCKET_DATA.slen=sizeof(SOCKET_DATA.si_other);
    if(
        (SOCKET_DATA.s=socket(
            AF_INET,
            SOCK_DGRAM,
            IPPROTO_UDP
        )) == SOCKET_ERROR
    ){
        log_error(
            "socket() failed with error code : %d" ,
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }

    memset(
        (char*) &SOCKET_DATA.si_other,
        0,
        sizeof(SOCKET_DATA.si_other)
    );
    SOCKET_DATA.si_other.sin_family = AF_INET;
    SOCKET_DATA.si_other.sin_port = htons(IPC_UI_SERVER_PORT);
    SOCKET_DATA.si_other.sin_addr.S_un.S_addr = inet_addr("127.0.0.1");

    SOCKET_DATA.tv.tv_sec = 0;
    SOCKET_DATA.tv.tv_usec = 50000;
}

void ipc_dtor(){
    closesocket(SOCKET_DATA.s);
    WSACleanup();
}

void ipc_client_send(char* message){
    int n;
    char buffer[IPC_MAX_MESSAGE_SIZE];

    if(
        sendto(
            SOCKET_DATA.s,
            message,
            strlen(message),
            0,
            (struct sockaddr*)&SOCKET_DATA.si_other,
            SOCKET_DATA.slen
        ) == SOCKET_ERROR
    ){
        log_error(
            "ipc_client_send: sendto() failed with error code : %d",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }

    memset(buffer,'\0', IPC_MAX_MESSAGE_SIZE);
    FD_ZERO(&SOCKET_DATA.fds);
    FD_SET(SOCKET_DATA.s, &SOCKET_DATA.fds);
    n = select(
        SOCKET_DATA.s,
        &SOCKET_DATA.fds,
        NULL,
        NULL,
        &SOCKET_DATA.tv
    );
    if(n == 0){
        log_warn("ipc_client_send select() returned 0, UI did not respond");
        return;
    }
    if(n == -1){
        log_warn(
            "ipc_client_send select() returned -1, %i",
            WSAGetLastError()
        );
        return;
    }
    if(
        recvfrom(
            SOCKET_DATA.s,
            buffer,
            IPC_MAX_MESSAGE_SIZE,
            0,
            (struct sockaddr*)&SOCKET_DATA.si_other,
            &SOCKET_DATA.slen
        ) == SOCKET_ERROR
    ){
        log_error(
            "ipc_client_send: recvfrom() failed with error code : %d",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
}

void* ipc_server_thread(void* _arg){
    struct IpcServerThreadArgs* args = (struct IpcServerThreadArgs*)_arg;
    struct EngineMessage engine_message;

    SOCKET s;
    struct sockaddr_in server, si_other;
    int slen , recv_len;
    char buffer[IPC_MAX_MESSAGE_SIZE];
    char *response = "Message processed";
    int response_len = strlen(response);

    fd_set fds;
    int n;
    struct timeval tv = (struct timeval){
        .tv_sec = 0,
        .tv_usec = 30000,
    };
    int err;

    slen = sizeof(si_other) ;

    if((s = socket(AF_INET , SOCK_DGRAM , 0 )) == INVALID_SOCKET){
        log_error(
            "ipc_server_thread: Could not create socket : %d",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    log_info("ipc_server_thread: Socket created.");

    // Prepare the sockaddr_in structure
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_port = htons(IPC_ENGINE_SERVER_PORT);

    int bufsize;
    unsigned int max_msg_size;
    int optsize;

    optsize = sizeof(bufsize);
    bufsize = 1024 * 1024;
    err = setsockopt(
        s,
        SOL_SOCKET,
        SO_RCVBUF,
        (char*)&bufsize,
        optsize
    );
    if(err){
        log_error(
            "ipc_server_thread: Unable to set recvbuf size, %i",
            WSAGetLastError()
        );
    }

    err = getsockopt(
        s,
        SOL_SOCKET,
        SO_RCVBUF,
        (char*)&bufsize,
        &optsize
    );
    if(err){
        log_error(
            "ipc_server_thread: Unable to get recvbuf size, %i",
            WSAGetLastError()
        );
    } else {
        log_info(
            "ipc_server_thread: recv buffer size: %i",
            bufsize
        );
    }

    optsize = sizeof(max_msg_size);
    err = getsockopt(
        s,
        SOL_SOCKET,
        SO_MAX_MSG_SIZE,
        (char*)&max_msg_size,
        &optsize
    );
    if(err){
        log_error(
            "ipc_server_thread: Unable to get max_msg_size, %i",
            WSAGetLastError()
        );
    } else {
        log_info(
            "ipc_server_thread: max_msg_size: %i",
            max_msg_size
        );
    }

    if(
        bind(
            s,
            (struct sockaddr*)&server,
            sizeof(server)
        ) == SOCKET_ERROR
    ){
        log_error(
            "ipc_server_thread: Bind failed with error code : %d",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    log_info("UDP server bind finished");

    while(!is_exiting()){
        memset(buffer,'\0', IPC_MAX_MESSAGE_SIZE);

        FD_ZERO(&fds);
        FD_SET(s, &fds);
        n = select(s, &fds, NULL, NULL, &tv);
        if(n == 0){  // timeout
            continue;
        } else if(n == -1){  // error
            log_error(
                "ipc_server_thread: select() returned -1, %i",
                WSAGetLastError()
            );
            continue;
        }
        // Try to receive some data, this is a blocking call
        if (
            (recv_len = recvfrom(
                s,
                buffer,
                IPC_MAX_MESSAGE_SIZE,
                0,
                (struct sockaddr*)&si_other,
                &slen
            )) == SOCKET_ERROR
        ){
            log_error(
                "ipc_server_thread: recvfrom() failed with error code : %d",
                WSAGetLastError()
            );
            exit(EXIT_FAILURE);
        }

        if (
            sendto(
                s,
                response,
                response_len,
                0,
                (struct sockaddr*)&si_other,
                slen
            ) == SOCKET_ERROR
        ){
            log_error(
                "ipc_server_thread: sendto() failed with error code : %d",
                WSAGetLastError()
            );
            exit(EXIT_FAILURE);
        }

        buffer[recv_len] = '\0';
        decode_engine_message(
            &engine_message,
            buffer
        );
        args->callback(
            engine_message.path,
            engine_message.key,
            engine_message.value
        );
    }

    closesocket(s);
    return NULL;
}

#endif
