#include <assert.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include "ipc.h"

int main(int argc, char **argv){
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

void ipc_client_send(
    char* message
){
    int sock;
    struct sockaddr_in server;
    struct hostent *hp;
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("opening stream socket");
        exit(1);
    }
    server.sin_family = AF_INET;
    hp = gethostbyname("localhost");
    if (hp == 0) {
        fprintf(stderr, "%s: unknown host\n");
        exit(2);
    }
    memcpy(
        &server.sin_addr,
        hp->h_addr,
        hp->h_length
    );
    server.sin_port = htons(9999);
    if (
		connect(
			sock,
			(struct sockaddr *)&server,
            sizeof(server)
		) < 0
	){
        perror("connecting stream socket");
        exit(1);
    }
    if(write(sock, message, strlen(message)) < 0){
        perror("writing on stream socket");
    }
    close(sock);
}

