CC ?= 
CFLAGS ?= -DCACHE_LINE_SIZE=64
LINK_FLAGS ?= -lws2_32

all:
	$(CC) -o client $(CFLAGS) client.c $(LINK_FLAGS)
	$(CC) -o server $(CFLAGS) server.c $(LINK_FLAGS)
	$(CC) -o udpclient $(CFLAGS) udpclient.c $(LINK_FLAGS)
	$(CC) -o udpserver $(CFLAGS) udpserver.c $(LINK_FLAGS)

