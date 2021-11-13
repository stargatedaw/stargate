#!/bin/sh

# Temporarily rename Homebrew lib directories to test
# Simulates a Mac without Homebrew installed

sudo mv /usr/local/lib /usr/local/lib-bkp
sudo mv /usr/local/opt /usr/local/opt-bkp

open -b io.github.stargateaudio

sudo mv /usr/local/lib-bkp /usr/local/lib
sudo mv /usr/local/opt-bkp /usr/local/opt

