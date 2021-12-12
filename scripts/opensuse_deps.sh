#!/bin/sh -xe

# This script installs all dependencies needed to build on Fedora

#dependencies
sudo zypper install \
    alsa-devel \
    fftw3-devel \
    gcc \
    gcc-c++ \
    gcovr \
    gettext \
    git \
    jq \
    lame \
    libsndfile-devel \
    portaudio-devel \
    portmidi-devel \
    python3-devel \
    python3-numpy \
    python3-qt5 \
    python3-pytest \
    python3-pytest-cov \
    rpm-build \
    rubberband-cli \
    vorbis-tools

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pip install -r ${SCRIPT_DIR}/../src/requirements.txt
pip install yq
