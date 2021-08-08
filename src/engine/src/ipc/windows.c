#include "compiler.h"

#if defined(_WIN32)

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

// Need to link with Ws2_32.lib, Mswsock.lib, and Advapi32.lib
#pragma comment (lib, "Ws2_32.lib")
#pragma comment (lib, "Mswsock.lib")
#pragma comment (lib, "AdvApi32.lib")
#pragma comment (lib, "Ws2_32.lib")

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

    printf("Initializing Winsock...\n");
    if(WSAStartup(MAKEWORD(2,2), &wsa) != 0){
        fprintf(
            stderr,
            "Failed to initialize winsock. Error Code : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    printf("Initialised winsock.\n");

    SOCKET_DATA.slen=sizeof(SOCKET_DATA.si_other);
    if(
        (SOCKET_DATA.s=socket(
            AF_INET,
            SOCK_DGRAM,
            IPPROTO_UDP
        )) == SOCKET_ERROR
    ){
        fprintf(
            stderr,
            "socket() failed with error code : %d\n" ,
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
    SOCKET_DATA.si_other.sin_port = htons(30321);
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
        fprintf(
            stderr,
            "ipc_client_send: sendto() failed with error code : %d\n",
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
        fprintf(
            stderr,
            "Warning: ipc_client_send select() returned 0, "
            "UI did not respond\n"
        );
        return;
    }
    if(n == -1){
        fprintf(
            stderr,
            "Warning: ipc_client_send select() returned -1, %i\n",
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
        fprintf(
            stderr,
            "ipc_client_send: recvfrom() failed with error code : %d\n",
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
    struct timeval tv = {
        .tv_sec = 0,
        .tv_usec = 30000,
    };

    slen = sizeof(si_other) ;

    if((s = socket(AF_INET , SOCK_DGRAM , 0 )) == INVALID_SOCKET){
        fprintf(
            stderr,
            "ipc_server_thread: Could not create socket : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    printf("ipc_server_thread: Socket created.\n");

    // Prepare the sockaddr_in structure
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_port = htons(19271);

    if(
        bind(
            s,
            (struct sockaddr*)&server,
            sizeof(server)
        ) == SOCKET_ERROR
    ){
        fprintf(
            stderr,
            "ipc_server_thread: Bind failed with error code : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    printf("UDP server bind finished\n");

    while(!exiting){
        memset(buffer,'\0', IPC_MAX_MESSAGE_SIZE);

        FD_ZERO(&fds);
        FD_SET(s, &fds);
        n = select(s, &fds, NULL, NULL, &tv);
        if(n == 0){  // timeout
            continue;
        } else if(n == -1){  // error
            fprintf(
                stderr,
                "ipc_server_thread: select() returned -1, %i\n",
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
            fprintf(
                stderr,
                "ipc_server_thread: recvfrom() failed with error code : %d\n",
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
            fprintf(
                stderr,
                "ipc_server_thread: sendto() failed with error code : %d\n",
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
