#!/bin/sh -xe

# This script installs all dependencies needed to build on Fedora

#dependencies
sudo dnf install \
    alsa-lib-devel \
    ccache \
    @development-tools \
    fedora-packager \
    fftw-devel \
    gcc \
    gcc-c++ \
    gcovr \
    gettext \
    git \
    jq \
    lame \
    libsndfile-devel \
    livecd-tools \
    patchelf \
    portaudio-devel \
    portmidi-devel \
    python3-devel \
    python3-numpy \
    python3-qt5 \
    python3-pytest \
    python3-pytest-cov \
    rubberband \
    spin-kickstarts \
    vorbis-tools

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pip install -r ${SCRIPT_DIR}/../src/requirements.txt
pip install yq
