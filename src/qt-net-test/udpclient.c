// Client side implementation of UDP client-server model
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include "ipc.h"

#define PORT 9999

// Driver code
int main(int argc, char** argv) {
    if(argc != 4){
        printf("Usage %s [path] [key] [value]\n", argv[0]);
        return 1;
    }
    struct IpcMessage ipc_msg;
    ipc_message_init(
        &ipc_msg,
        argv[1],
        argv[2],
        argv[3]
    );
    char message[8192];
    memset(message, 0, sizeof(message));
    encode_ipc_message(
        &ipc_msg,
        message
    );
    while(1){
        ipc_client_send(message);
        fflush(stdout);
        sleep(1);
    }
}

void ipc_client_send(char* message){
    int sockfd;
    char buffer[1024];
    struct sockaddr_in     servaddr;

    // Creating socket file descriptor
    if((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ){
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));

    // Filling server information
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(PORT);
    servaddr.sin_addr.s_addr = INADDR_ANY;

    int n, len;

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
        &len);
    buffer[n] = '\0';
    printf("Server : %s\n", buffer);
    close(sockfd);
}

