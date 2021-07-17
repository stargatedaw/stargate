#!/usr/bin/make -f

CC  ?= g++
CXX ?= g++
MOC ?= moc

PREFIX ?= /usr/local

BASE_FLAGS     = -O0 -gdwarf-3 -mstackrealign -fsingle-precision-constant -fPIC -mtune=generic -msse -msse2 -msse3 -mfpmath=sse
BUILD_CFLAGS   = $(BASE_FLAGS) $(CFLAGS)
BUILD_CXXFLAGS = $(BASE_FLAGS) $(shell pkg-config --cflags sndfile) $(CXXFLAGS)
LINK_CFLAGS    = -ldl -shared -lm $(LDFLAGS) $(shell pkg-config --libs alsa sndfile)
LINK_CXXFLAGS  = -ldl -lm $(shell pkg-config --libs alsa sndfile) $(LDFLAGS)

C_OBJS   = main.o
CXX_OBJS = main.o

# --------------------------------------------------------------

all: wtgen

wtgen: $(CXX_OBJS)
	$(CXX) $(CXX_OBJS) $(LINK_CXXFLAGS) -o $@

# --------------------------------------------------------------

.c.o:
	$(CC) -c $< $(BUILD_CFLAGS) -o $@

.cpp.o:
	$(CXX) -c $< $(BUILD_CXXFLAGS) -o $@

# --------------------------------------------------------------

clean:
	rm -f *.o *.so wtgen

