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

void ipc_init(){
    WSADATA wsa;

    printf("Initializing Winsock...\n");
    if(WSAStartup(MAKEWORD(2,2), &wsa) != 0){
        fprintf(
            stderr,
            "Failed to initialize winsock. Error Code : %d",
            WSAGetLastError()
        );
        exit(EXIT_FAILURE);
    }
    printf("Initialised winsock.\n");
}

void ipc_dtor(){
    WSACleanup();
}

void ipc_client_send(char* message){
    struct sockaddr_in si_other;
    int s, slen=sizeof(si_other);
    char buf[IPC_MAX_MESSAGE_SIZE];

    if(
        (s=socket(
            AF_INET,
            SOCK_DGRAM,
            IPPROTO_UDP
        )) == SOCKET_ERROR
    ){
        printf("socket() failed with error code : %d" , WSAGetLastError());
        exit(EXIT_FAILURE);
    }

    memset((char *) &si_other, 0, sizeof(si_other));
    si_other.sin_family = AF_INET;
    si_other.sin_port = htons(30321);
    si_other.sin_addr.S_un.S_addr = inet_addr("127.0.0.1");

    if (
        sendto(
            s,
            message,
            strlen(message),
            0,
            (struct sockaddr*)&si_other,
            slen
        ) == SOCKET_ERROR
    ){
        printf("sendto() failed with error code : %d" , WSAGetLastError());
        exit(EXIT_FAILURE);
    }

    //receive a reply and print it
    //clear the buffer by filling null, it might have previously received data
    memset(buf,'\0', IPC_MAX_MESSAGE_SIZE);
    //try to receive some data, this is a blocking call
    if(
        recvfrom(
            s,
            buf,
            IPC_MAX_MESSAGE_SIZE,
            0,
            (struct sockaddr*)&si_other,
            &slen
        ) == SOCKET_ERROR
    ){
        printf("recvfrom() failed with error code : %d" , WSAGetLastError());
        exit(EXIT_FAILURE);
    }

    printf("%s\n", buf);

    closesocket(s);
}

void* ipc_server_thread(void* _arg){
    SOCKET s;
    struct sockaddr_in server, si_other;
    int slen , recv_len;
    char buf[IPC_MAX_MESSAGE_SIZE];

    slen = sizeof(si_other) ;

    //Create a socket
    if((s = socket(AF_INET , SOCK_DGRAM , 0 )) == INVALID_SOCKET){
        printf("Could not create socket : %d" , WSAGetLastError());
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
        printf("Bind failed with error code : %d" , WSAGetLastError());
        exit(EXIT_FAILURE);
    }
    printf("Bind finished\n");

    //keep listening for data
    while(1){
        //clear the buffer by filling null, it might have previously received data
        memset(buf,'\0', IPC_MAX_MESSAGE_SIZE);

        //try to receive some data, this is a blocking call
        if (
            (recv_len = recvfrom(
                s,
                buf,
                IPC_MAX_MESSAGE_SIZE,
                0,
                (struct sockaddr*)&si_other,
                &slen
            )) == SOCKET_ERROR
        ){
            printf("recvfrom() failed with error code : %d" , WSAGetLastError());
            exit(EXIT_FAILURE);
        }

        //print details of the client/peer and the data received
        printf(
            "Received packet from %s:%d\n",
            inet_ntoa(si_other.sin_addr),
            ntohs(si_other.sin_port)
        );
        printf("Data: %s\n" , buf);
	fflush(stdout);

        //now reply the client with the same data
        if (
            sendto(
                s,
                buf,
                recv_len,
                0,
                (struct sockaddr*)&si_other,
                slen
            ) == SOCKET_ERROR
        ){
            printf("sendto() failed with error code : %d" , WSAGetLastError());
            exit(EXIT_FAILURE);
        }
    }

    closesocket(s);
    return NULL;
}

#endif
