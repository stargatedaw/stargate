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

### Build and run
```
# Download and build the source code
git clone https://github.com/stargateaudio/stargate.git
cd stargate
./scripts/homebrew_deps.sh
cd src
pip3 install --user -r requirements-mac.txt

# Run locally
make mac_osx
python3 ./scripts/stargate

# Package
./macos/release.py
```
