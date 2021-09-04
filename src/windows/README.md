# Overview
This is the procedure for creating Windows build artifacts, both the installer,
and the portable executable suitable for running from a flash drive.
Note that our compiler (MSYS2) no longer supports 32 bit Windows builds, and
by extension, neither do we.

# Initial Setup
## Create a fresh 64 bit Windows 10 VM
(or install to your hard drive if you are `into that`)
- Create a user called stargate
- Install [MSYS2](https://www.msys2.org/wiki/MSYS2-installation/)
- Install [Python3](https://www.python.org/downloads/windows/)
- Install [NSIS](https://nsis.sourceforge.io/Download)

## MSYS2 Terminal
```
cd ~
mkdir src && cd src
git clone https://github.com/stargateaudio/stargate.git
cd stargate
./scripts/msys2_deps.sh
cd src/
make mingw_deps
```

## Windows cmd.exe
```
python -m venv C:\Users\starg\venv\stargate
pip install pyinstaller
cd C:\msys64\home\starg\src\stargate\src
pip install -r requirements-windows.txt
```

# Creating a new release
## MSYS2 Terminal
```
cd ~/src/stargate/src
git pull
# Note that you may need to run this again
# make mingw_deps
cd engine
source mingw64-source-me.sh
make mingw
```

## Windows cmd.exe
```
venv\stargate\Scripts\activate.bat
cd C:\msys64\home\starg\src\stargate\src
# Build the portable exe and installer exe
python windows\release.py
```

The build artifacts are now in `C:\msys64\home\starg\src\stargate\dist\`
