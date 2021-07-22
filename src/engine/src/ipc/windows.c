#include "compiler.h"

#if defined(_WIN32) && !defined(SG_DLL)

#define WIN32_LEAN_AND_MEAN
#undef UNICODE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>

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

    memset((char *) &SOCKET_DATA.si_other, 0, sizeof(SOCKET_DATA.si_other));
    SOCKET_DATA.si_other.sin_family = AF_INET;
    SOCKET_DATA.si_other.sin_port = htons(30321);
    SOCKET_DATA.si_other.sin_addr.S_un.S_addr = inet_addr("127.0.0.1");
}

void ipc_dtor(){
    closesocket(SOCKET_DATA.s);
    WSACleanup();
}

void ipc_client_send(char* message){
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
            "UDP Client: sendto() failed with error code : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }

    //receive a reply and print it
    //clear the buffer by filling null, it might have previously received data
    memset(buffer,'\0', IPC_MAX_MESSAGE_SIZE);
    //try to receive some data, this is a blocking call
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
            "recvfrom() failed with error code : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }

    //printf("%s\n", buffer);

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

    slen = sizeof(si_other) ;

    //Create a socket
    if((s = socket(AF_INET , SOCK_DGRAM , 0 )) == INVALID_SOCKET){
        fprintf(
            stderr,
            "Could not create socket : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    printf("Socket created.\n");

    //Prepare the sockaddr_in structure
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_port = htons(19271);

    //Bind
    if(
        bind(
            s,
            (struct sockaddr*)&server,
            sizeof(server)
        ) == SOCKET_ERROR
    ){
        fprintf(
            stderr,
            "Bind failed with error code : %d\n",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    printf("UDP server bind finished\n");

    //keep listening for data
    while(1){
        //clear the buffer by filling null, it might have previously received data
        memset(buffer,'\0', IPC_MAX_MESSAGE_SIZE);

        //try to receive some data, this is a blocking call
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
                "recvfrom() failed with error code : %d\n",
                WSAGetLastError()
            );
            exit(EXIT_FAILURE);
        }

        buffer[recv_len] = '\0';
        decode_engine_message(
            &engine_message,
            buffer
        );
        printf(
            "path: %s\nkey: %s\nvalue: %s\n",
            engine_message.path,
            engine_message.key,
            engine_message.value
        );
        args->callback(
            engine_message.path,
            engine_message.key,
            engine_message.value
        );
        //now reply the client with the same data
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
                "UDP Server: sendto() failed with error code : %d\n",
                WSAGetLastError()
            );
            exit(EXIT_FAILURE);
        }
    }

    closesocket(s);
    return NULL;
}

#endif
