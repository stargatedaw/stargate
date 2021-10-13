# Overview
This is the procedure for creating Windows build artifacts, both the installer,
and the portable executable suitable for running from a flash drive.  Note
that it may be possible to compile for 32 bit Windows, but at the present time
it is untested and unsupported

# Initial Setup
## Create a fresh 64 bit Windows 10 VM
(or install to your hard drive if you are `into that`)
- Create a user called stargate
- Install [MSYS2 64bit](https://www.msys2.org/wiki/MSYS2-installation/)
- Install [Python3 64bit](https://www.python.org/downloads/windows/), be sure
  to select the option to add Python to PATH / environment variables
- Install [NSIS](https://nsis.sourceforge.io/Download)

## MSYS2 Terminal
```
cd ~
mkdir src && cd src
pacman -S git make
git clone https://github.com/stargateaudio/stargate.git
cd stargate
./scripts/msys2_deps.sh
cd src/
make mingw_deps
# Because git submodule init does not seem to work on Windows
cd vendor
git clone https://github.com/stargateaudio/libcds.git
```

## Windows cmd.exe
```
python -m venv venv\stargate
venv\stargate\scripts\activate.bat
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

The build artifacts are now in `C:\msys64\home\starg\src\stargate\src\dist\`
