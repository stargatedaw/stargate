#include "compiler.h"

#if !defined(_WIN32) && !defined(SG_DLL)

#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#include "globals.h"
#include "ipc.h"

void ipc_init(){

}

void ipc_dtor(){

}

void ipc_client_send(
    char* message
){
    int sockfd;
    char buffer[IPC_MAX_MESSAGE_SIZE];
    struct sockaddr_in servaddr;
    int n;
    socklen_t len;

    if((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ){
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));

    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(30321);
    servaddr.sin_addr.s_addr = INADDR_ANY;

    len = (socklen_t)sizeof(servaddr);

    sendto(
        sockfd,
        (const char*)message,
        strlen(message),
        MSG_CONFIRM,
        (const struct sockaddr*)&servaddr,
        sizeof(servaddr)
    );
    n = recvfrom(
        sockfd,
        (char*)buffer,
        1024,
        MSG_WAITALL,
        (struct sockaddr*)&servaddr,
        &len
    );
    buffer[n] = '\0';
    close(sockfd);
}

void* ipc_server_thread(void* _arg){
    struct IpcServerThreadArgs* args = (struct IpcServerThreadArgs*)_arg;
    struct EngineMessage engine_message;

    int sockfd;
    int n;
    socklen_t len;
    char buffer[IPC_MAX_MESSAGE_SIZE];
    char *response = "Message processed";
    int response_len = strlen(response);
    struct sockaddr_in servaddr, cliaddr;
    struct timeval tv = (struct timeval){
        .tv_sec = 0,
        .tv_usec = 100000,
    };

    // Creating socket file descriptor
    if (
        (sockfd = socket(
            AF_INET,
            SOCK_DGRAM,
            0
        )) < 0
    ){
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    if(
        setsockopt(
            sockfd,
            SOL_SOCKET,
            SO_RCVTIMEO,&tv,
            sizeof(tv)
        ) < 0
    ){
        perror("Error");
    }

    memset(&servaddr, 0, sizeof(servaddr));
    memset(&cliaddr, 0, sizeof(cliaddr));

    // Filling server information
    servaddr.sin_family = AF_INET; // IPv4
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(19271);

    // Bind the socket with the server address
    if(
        bind(
            sockfd,
            (const struct sockaddr *)&servaddr,
            sizeof(servaddr)
        ) < 0
    ){
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    len = (socklen_t)sizeof(cliaddr); //len is value/resuslt

    while(!exiting){
        n = recvfrom(
            sockfd,
            (char*)buffer,
            8192,
            MSG_WAITALL,
            (struct sockaddr*)&cliaddr,
            &len
        );
        if(n < 0){
            continue;
        }
        buffer[n] = '\0';
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
        sendto(
            sockfd,
            (const char*)response,
            response_len,
            MSG_CONFIRM,
            (const struct sockaddr*)&cliaddr,
            len
        );
    }
    return 0;
}

#endif
