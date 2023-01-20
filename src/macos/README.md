# Description
This document describes the process for building on Mac OS X.

# Procedure
Note that you will need to install [Homebrew](https://brew.sh/) first, as it
will be used to download dependencies.

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
git clone https://github.com/stargateaudio/stargate.git
cd stargate
./scripts/homebrew_deps.sh
cd src
python3 -m venv venv
. venv/bin/activate
pip3 install -r macos/requirements.txt
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

