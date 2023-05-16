#!/bin/sh

export PATH="/mingw64/bin:${PATH}"
PREFIX=x86_64-w64-mingw32
export CC=clang
export CXX=clang++
export CPP=clang-cpp
export RANLIB=$PREFIX-ranlib
export PREFIX=/usr

