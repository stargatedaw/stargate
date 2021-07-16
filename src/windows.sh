#!/bin/sh -xe

export PATH="/mingw64/bin:$PATH"
CC=/mingw64/bin/gcc make -C engine engine
#make mingw
#make PREFIX= DESTDIR=/mingw64 install_non_linux
