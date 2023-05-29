# Description
This document describes the process for building on Mac OS X.

# Procedure
Note that you will need to install [Homebrew](https://brew.sh/) first, as it
will be used to download dependencies.

*IMPORTANT*: Homebrew has a number of problems on Intel Macs, namely that it
may build only for currently supported hardware, which causes `illegal
instruction` crashes on some older hardware which we aim to support..  It is
probably a good idea to supplement packages like Rubberband with the versions
from pkgsrc archives, which tend to have more conservative compiler flags.
However, pkgsrc is not easy to automate the install and creation of, so likely
you will need to hack your homebrew root to include some pkgsrc binaries, and
check with `otool -L $lib-or-exe` to verify that it links to pkgsrc libraries.
Eventually, these will likely become problems for M1 Macs too.  The moral of
the story:  Don't update Homebrew or any dependencies, ever, especially once
your hardware is out of support.

Also note that you may need to disable the Mac OS X firewall (if enabled) or
add rules, as it may block the Stargate UI and engine from communicating over
UDP sockets on localhost.  You will need the following rules:
```
stargate: 31909
stargate-engine: 31999
```

### Build and run locally
```
# Download and build the source code
git clone --recursive https://github.com/stargateaudio/stargate.git
cd stargate/src
./macos/homebrew_deps.sh
python3 -m venv venv
. venv/bin/activate
pip3 install -r macos/requirements-intel.txt
# OR
pip3 install -r macos/requirements-m1.txt
pip3 install -e .
make sbsms

# Run locally
make mac_osx
python3 ./scripts/stargate

# Package
./macos/release.py
```

## Build a DMG package
This requires that you have already done the setup to build locally
```
cd src/
./macos/release.py
# dmg file will be in dist/
```

