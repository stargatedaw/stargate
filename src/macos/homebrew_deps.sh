#!/bin/sh -x

# Used for creating the app bundle and dmg
# Note that "System Integrity Protection" and Homebrew's insistence
# on not running as root makes it impossible to directly install
# Stargate DAW from a Homebrew tap

brew install \
    create-dmg \
    ffmpeg \
    fftw \
    flac \
    jq \
    lame \
    libogg \
    libsamplerate \
    libsndfile \
    libvorbis \
    opus \
    portaudio \
    portmidi \
    rubberband \
    theora

