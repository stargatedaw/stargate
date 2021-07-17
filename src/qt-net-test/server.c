#include <arpa/inet.h>
#include <assert.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include "ipc.h"


int main(){
    ipc_server_thread();
    return 0;
}

void ipc_server_thread(){
    int sock, length;
    struct sockaddr_in server;
    struct IpcMessage ipc_message;
    int msgsock;
    char buf[1024];
    int rval;
    int i;

    /* Create socket */
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("opening stream socket");
        exit(1);
    }
    /* Name socket using wildcards */
    server.sin_family = AF_INET;
    server.sin_port = htons(9999);
    server.sin_addr.s_addr = INADDR_ANY;
    //server.sin_addr.s_addr = INADDR_ANY;
    if(
        bind(
            sock,
            (struct sockaddr *)&server,
            sizeof(server)
        )
    ){
        perror("binding stream socket");
        exit(1);
    }
    /* Find out assigned port number and print it out */
    length = sizeof(server);
    if(
		getsockname(
			sock,
			(struct sockaddr *)&server,
            &length
		)
	){
        perror("getting socket name");
        exit(1);
    }
    printf("Socket has port #%d\n", ntohs(server.sin_port));

    /* Start accepting connections */
    listen(sock, 5);
    do {
        msgsock = accept(sock, 0, 0);
        if (msgsock == -1) {
            perror("accept");
            return;
        } else do {
            memset(buf, 0, sizeof(buf));
            if ((rval  = read(msgsock, buf,  1024)) < 0){
                perror("reading stream message");
            } else if (rval == 0){
                printf("Ending connection\n");
            } else{
                decode_ipc_message(
                    &ipc_message,
                    buf
                );
                printf(
                    "path: %s\nkey: %s\nvalue: %s\n",
                    ipc_message.path,
                    ipc_message.key,
                    ipc_message.value
                );
            }
        } while (rval > 0);
        close(msgsock);
    } while(1);
}
