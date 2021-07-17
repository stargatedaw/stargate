// Server side implementation of UDP client-server model
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#define PORT 9999
#define MAXLINE 1024

int exiting = 0;

// Driver code
int main() {
    int sockfd;
    int len, n;
    char buffer[MAXLINE];
    char *hello = "Hello from server";
    struct sockaddr_in servaddr, cliaddr;
    struct timeval tv = (struct timeval){
        .tv_sec = 0,
        .tv_usec = 100000,
    };

    // Creating socket file descriptor
    if ( (sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ) {
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
    servaddr.sin_port = htons(PORT);

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

    len = sizeof(cliaddr); //len is value/resuslt

    while(!exiting){
        n = recvfrom(
            sockfd,
            (char *)buffer, MAXLINE,
            MSG_WAITALL,
            (struct sockaddr*)&cliaddr,
            &len
        );
        if(n < 0){
            continue;
        }
        buffer[n] = '\0';
        printf("Client : %s\n", buffer);
        sendto(
            sockfd,
            (const char*)hello,
            strlen(hello),
            MSG_CONFIRM,
            (const struct sockaddr*)&cliaddr,
            len
        );
    }
    return 0;
}

