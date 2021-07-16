#!/bin/bash -x

sudo apt-get update

sudo apt-get install -y \
    autoconf \
    automake \
    build-essential \
    cython3 \
    debhelper \
    dh-make \
    ffmpeg \
    g++ \
    gcc \
    gdb \
    genisoimage \
    gettext \
	jq \
    lame \
    libasound2-dev \
    libfftw3-dev \
    liblo-dev \
    libportmidi-dev \
    libsbsms-dev \
    libsndfile1-dev \
    libtool \
    portaudio19-dev \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-pyqt5 \
    rubberband-cli \
    squashfs-tools \
    vorbis-tools

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pip3 install -r ${SCRIPT_DIR}/../src/requirements.txt
