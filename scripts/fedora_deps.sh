#!/bin/sh -x

# This script installs all dependencies needed to build on Fedora

#dependencies
sudo dnf install \
    alsa-lib-devel \
    @development-tools \
    fedora-packager \
    fftw-devel \
    gcc \
    gcc-c++ \
    gettext \
    git \
    lame \
    liblo-devel \
    libsndfile-devel \
    livecd-tools \
    portaudio-devel \
    portmidi-devel \
    python3-Cython \
    python3-devel \
    python3-numpy \
    python3-qt5 \
    rubberband \
    spin-kickstarts \
    vorbis-tools

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pip install -r ${SCRIPT_DIR}/../src/requirements.txt
