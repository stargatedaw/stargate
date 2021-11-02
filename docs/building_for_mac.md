# Description
This article describes the process for building on Mac OS X.  Note that it is
very much still a work-in-progress.  We hope to eventually offer an app bundle
if there is sufficient demand.

# Procedure
Note that you will need to install [Homebrew](https://brew.sh/) first, as it
will be used to download dependencies.

Also note that you may need to disable the Mac OS X firewall or add an
exception, as it may block the Stargate UI and engine from communicating over
UDP sockets on localhost.

```
# Download and build the source code
git clone https://github.com/stargateaudio/stargate.git
cd stargate
sh ./scripts/homebrew_deps.sh
cd src
python3 -m pip install requirements-windows.txt
make mac_osx

# and run Stargate locally
./scripts/stargate
```
