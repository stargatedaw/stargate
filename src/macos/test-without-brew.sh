#!/bin/sh

# Remove some brew dependencies to test that Pyinstaller linkage is
# working as expected

brew uninstall -y portaudio portmidi

open -b io.github.stargateaudio

brew install -y portaudio portmidi

