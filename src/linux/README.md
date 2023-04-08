# Building
## Note
If building for ARM or any architecture other than x86, you must override
`PLAT_FLAGS` when calling `make`.  For example:
```
PLAT_FLAGS='-march=native' make
```
[See the ARM documentation](./ARM)

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
# From the root of the Stargate repo
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
./scripts/stargate
```

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

## Building for packages
```
# The following targets are useful for packaging, see src/Makefile for details
make distro

# Install without vendored dependencies
make install_distro

# Install everything into a single folder, in this example /opt/stargate
PREFIX=/opt/stargate make install_self_contained
# You can then:
ln -s /opt/stargate/scripts/stargate /usr/bin/stargate
ln -s /opt/stargate/files/share/doc/stargate /usr/share/doc/stargate
ln -s /opt/stargate/files/share/pixmaps/stargate.png /usr/share/pixmaps/stargate.png
ln -s /opt/stargate/files/share/pixmaps/stargate.ico /usr/share/pixmaps/stargate.ico
ln -s /opt/stargate/files/share/applications/stargate.desktop /usr/share/applications/stargate.desktop
ln -s /opt/stargate/files/share/mime/packages/stargate.xml /usr/share/mime/packages/stargate.xml
```
