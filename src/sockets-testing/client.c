#include "compiler.h"

#if defined(_WIN32) && !defined(SG_DLL)

#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

#include "ipc.h"

#define PORT 8888

// Need to link with Ws2_32.lib, Mswsock.lib, and Advapi32.lib
#pragma comment (lib, "Ws2_32.lib")
#pragma comment (lib, "Mswsock.lib")
#pragma comment (lib, "AdvApi32.lib")

int __cdecl main(int argc, char** argv){
    if(argc != 4){
        printf("Usage: %s path key value\n", argv[0]);
        return 1;
    }
    char message[IPC_MAX_MESSAGE_SIZE];
    memset(message, 0, sizeof(message));
    sprintf(message, "%s\n%s\n%s", argv[1], argv[2], argv[3]);
    printf("Sending message:\n%s\n", message);
    WSADATA wsa;

    //Initialise winsock
    printf("\nInitialising Winsock...");
    if(WSAStartup(MAKEWORD(2,2),&wsa) != 0){
        printf("Failed. Error Code : %d",WSAGetLastError());
        exit(EXIT_FAILURE);
    }
    printf("Initialised.\n");
    while(1){
        ipc_client_send(message);
        fflush(stdout);
        sleep(1);
    }
    WSACleanup();
    return 0;
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
    si_other.sin_port = htons(PORT);
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

#endif
