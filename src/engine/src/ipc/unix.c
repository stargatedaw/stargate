#include "compiler.h"

#if !defined(SG_OS_WINDOWS)

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

struct SocketData{
    int sockfd;
    struct sockaddr_in servaddr;
    socklen_t len;
};

static struct SocketData SOCKET_DATA;

void ipc_init(){
    if((SOCKET_DATA.sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ){
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(
        &SOCKET_DATA.servaddr,
        0,
        sizeof(SOCKET_DATA.servaddr)
    );
    SOCKET_DATA.servaddr.sin_family = AF_INET;
    SOCKET_DATA.servaddr.sin_port = htons(IPC_UI_SERVER_PORT);
    SOCKET_DATA.servaddr.sin_addr.s_addr = inet_addr("127.0.0.1");
    SOCKET_DATA.len = (socklen_t)sizeof(SOCKET_DATA.servaddr);
}

void ipc_dtor(){
    close(SOCKET_DATA.sockfd);
}

void ipc_client_send(
    char* message
){
    int n;
    char buffer[1024];

    sendto(
        SOCKET_DATA.sockfd,
        (const char*)message,
        strlen(message),
        MSG_CONFIRM,
        (const struct sockaddr*)&SOCKET_DATA.servaddr,
        sizeof(SOCKET_DATA.servaddr)
    );
    n = recvfrom(
        SOCKET_DATA.sockfd,
        (char*)buffer,
        1024,
        MSG_WAITALL,
        (struct sockaddr*)&SOCKET_DATA.servaddr,
        &SOCKET_DATA.len
    );
    buffer[n] = '\0';
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
            SO_RCVTIMEO,
            &tv,
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
    servaddr.sin_port = htons(IPC_ENGINE_SERVER_PORT);

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
            IPC_MAX_MESSAGE_SIZE,
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
