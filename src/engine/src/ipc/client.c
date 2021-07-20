#include "compiler.h"

#if !defined(_WIN32) && !defined(SG_DLL)

#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include "ipc.h"


void ipc_client_send(
    char* message
){
    int sockfd;
    char buffer[8192];
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

    //len = (socklen_t)sizeof(cliaddr); //len is value/resuslt

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
        (struct sockaddr*) &servaddr,
        &len
    );
    buffer[n] = '\0';
    close(sockfd);
}

#endif
