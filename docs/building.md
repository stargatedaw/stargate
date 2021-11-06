# Building
##Note
If building for ARM or any architecture other than x86, you must override
`PLAT_FLAGS` when calling `make`.  For example:
```
PLAT_FLAGS='-march=native' make
```

## Prerequisites
```
# Install dependencies using one of:
scripts/debian_deps.sh
scripts/fedora_deps.sh
# Or find the equivalent dependencies for your distro of choice

# Initialize the vendored dependencies
git submodule init
git submodule update

```
## Linux
### Option 1: Packaging scripts
```
# See --help for additional options
# Create a Debian package, works on Debian, Ubuntu and their derivatives
scripts/deb.py
# or
# Create an RPM package, works on Fedora, RHEL, CentOS, Rocky Linux and their
# derivatives
scripts/rpm.py
```
### Option 2: Roll your own
```
cd src/
# Build
make

# Install
PREFIX=/usr/local make install
# Or, run locally without installing
scripts/stargate
```
## Windows
[See this document](../src/windows/README.md)

## Mac
[See this document](./building_for_mac.md)

# Distro Packagers
## Dependencies
### Build time
- alsa-lib-devel
- fftw-devel
- gcc
- gcc-c++
- jq
- libsndfile-devel
- portaudio-devel
- portmidi-devel
- python3-devel

### Run time
- alsa-lib
- fftw
- libsndfile
- portaudio
- portmidi
- python3
- python3-jinja2
- python3-mido
- python3-mutagen
- python3-numpy
- python3-psutil
- python3-pyyaml
- python3-pymarshal
- python3-wavefile
- (python3-qt6 or python3-qt5)
- rubberband

#### Recommended
- lame
- vorbis-tools
- ffmpeg
