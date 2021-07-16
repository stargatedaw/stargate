#!/usr/bin/make -f

CC  ?= gcc
CXX ?= g++

PREFIX ?= /usr

#Default flags are mostly x86 specific
PLAT_FLAGS     ?=
#-mstackrealign -msse -msse2 -msse3 -mfpmath=sse -mtune=generic

BASE_FLAGS     = -ffast-math -fprefetch-loop-arrays \
-fsingle-precision-constant -funroll-loops -Wall \
-Isrc -I../include -fstrength-reduce -fstrict-aliasing -finline-functions

BUILD_CFLAGS    = -O3 $(PLAT_FLAGS) $(BASE_FLAGS)

LINK_CFLAGS    = ../src/.libs/libsbsms.a -lpthread $(LDFLAGS) $(shell pkg-config --libs sndfile) -lm

C_OBJS   = src/pcm.o src/audiobuffer.o src/convert.o src/import.o src/test.o

# --------------------------------------------------------------

all:
	make sbsms

sbsms: $(C_OBJS)
	$(CXX) $(C_OBJS) $(LINK_CFLAGS) -o $@

# --------------------------------------------------------------

.cpp.o:
	$(CXX) -c $< $(BUILD_CFLAGS) -o $@

# --------------------------------------------------------------

install:
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 sbsms $(DESTDIR)$(PREFIX)/bin

clean:
	rm -f src/*.o sbsms

