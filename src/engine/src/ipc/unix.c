#include "compiler.h"

#if SG_OS != _OS_WINDOWS

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

#if SG_OS == _OS_MACOS
    #define MSG_CONFIRM SO_NOSIGPIPE
#endif

struct SocketData{
    int sockfd;
    struct sockaddr_in servaddr;
    socklen_t len;
};

static struct SocketData SOCKET_DATA;

void _set_buf_size(int sockfd){
    int bufsize = 500000;
    if(
        setsockopt(
            sockfd,
            SOL_SOCKET,
            SO_RCVBUF,
            (char*)&bufsize,
            sizeof(bufsize)
        ) < 0
    ){
        log_error("Unable to set SO_RCVBUF");
    }
    if(
        setsockopt(
            sockfd,
            SOL_SOCKET,
            SO_SNDBUF,
            (char*)&bufsize,
            sizeof(bufsize)
        ) < 0
    ){
        log_error("Unable to set SO_SNDBUF");
    }
}

void ipc_init(){
    struct timeval tv = (struct timeval){
        .tv_usec = 10000,
    };
    SOCKET_DATA.sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    sg_assert(SOCKET_DATA.sockfd >= 0, "socket creation failed");
    if(
        setsockopt(
            SOCKET_DATA.sockfd,
            SOL_SOCKET,
            SO_RCVTIMEO,
            &tv,
            sizeof(tv)
        ) < 0
    ){
        log_error("Could not set client socket to SO_RCVTIMEO");
    }
    _set_buf_size(SOCKET_DATA.sockfd);
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
        .tv_usec = 100000,
    };

    // Creating socket file descriptor
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    sg_assert(sockfd >= 0, "socket creation failed");
    if(
        setsockopt(
            sockfd,
            SOL_SOCKET,
            SO_RCVTIMEO,
            &tv,
            sizeof(tv)
        ) < 0
    ){
        log_error("Unable to set SO_RCVTIMEO");
    }
    _set_buf_size(sockfd);

    memset(&servaddr, 0, sizeof(servaddr));
    memset(&cliaddr, 0, sizeof(cliaddr));

    // Filling server information
    servaddr = (struct sockaddr_in){
        .sin_family = AF_INET, // IPv4
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(IPC_ENGINE_SERVER_PORT),
    };

    // Bind the socket with the server address
    sg_assert(
        bind(
            sockfd,
            (const struct sockaddr *)&servaddr,
            sizeof(servaddr)
        ) >= 0,
        "bind failed"
    );

    len = (socklen_t)sizeof(cliaddr); //len is value/result

    while(!is_exiting()){
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
