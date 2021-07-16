#!/bin/sh

PREFIX=x86_64-w64-mingw32
export CC=$PREFIX-gcc
export CXX=$PREFIX-g++
export CPP=$PREFIX-cpp
export RANLIB=$PREFIX-ranlib
#export PATH="$HOME/bin:$PATH"
export PREFIX=/usr

