# Building
## Prequisites
```
# Install dependencies using one of:
scripts/ubuntu_deps.sh
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
## Windows, Mac
We will take care of that for you, it is quite complicated and time consuming
to setup.

