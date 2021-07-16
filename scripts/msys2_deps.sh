#!/bin/bash -x

pacman -S \
    mingw-w64-x86_64-ffmpeg \
    mingw-w64-x86_64-fftw \
    mingw-w64-x86_64-gcc \
    mingw-w64-x86_64-jq \
    mingw-w64-x86_64-lame \
    mingw-w64-x86_64-liblo \
    mingw-w64-x86_64-libsndfile \
    mingw-w64-x86_64-libvorbis \
    mingw-w64-x86_64-portaudio \
    mingw-w64-x86_64-portmidi \
    mingw-w64-x86_64-python \
    mingw-w64-x86_64-python-numpy \
    mingw-w64-x86_64-python-pip \
    mingw-w64-x86_64-python-pyqt5 \
    mingw-w64-x86_64-rubberband 

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pip install -r ${SCRIPT_DIR}/../src/requirements.txt
