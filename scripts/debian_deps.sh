#!/bin/bash -xe

# Ubuntu, and maybe some of it's derivatives
sudo add-apt-repository universe || true
sudo add-apt-repository multiverse || true

sudo apt-get update

sudo apt-get install -y \
    autoconf \
    automake \
    build-essential \
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
    libportmidi-dev \
    libsndfile1-dev \
    libtool \
    portaudio19-dev \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-pyqt5 \
    python3-pyqt5.qtsvg \
    rpm \
    rubberband-cli \
    squashfs-tools \
    vorbis-tools

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pip3 install -r ${SCRIPT_DIR}/../src/requirements.txt
