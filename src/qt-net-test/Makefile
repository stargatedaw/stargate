CC ?= gcc

FLAGS ?= -O0 -g -ggdb3
WLINK ?= -lwsock32 -lws2_32

tcp: clean
	$(CC) $(FLAGS) ipc.c client.c -o client
	$(CC) $(FLAGS) ipc.c server.c -o server
	$(CC) $(FLAGS) ipc.c server-select.c -o server-select
udp:
	$(CC) $(FLAGS) ipc.c udpclient.c -o udpclient
	$(CC) $(FLAGS) ipc.c udpserver.c -o udpserver

clean:
	rm -f client server client.exe server.exe udpclient udpserver \
		udpclient.exe udpserver.exe
windows: clean
	$(CC) $(FLAGS) ipc.c wclient.c $(WLINK) -o client
	$(CC) $(FLAGS) ipc.c wserver.c $(WLINK) -o server
