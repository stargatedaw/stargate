# Overview
This is the procedure for creating Windows build artifacts, both the installer.
Note that it may be possible to compile for 32 bit Windows, but at the
present time it is untested and unsupported

# Initial Setup
## Create a fresh 64 bit Windows 10 VM
(or install Windows to your hard drive if you are `into that`).
The VM should have at least 100GB of hard disk space

- Create a user called stargate
- Install [MSYS2 64bit](https://www.msys2.org/wiki/MSYS2-installation/)
- Install [Python3 64bit](https://www.python.org/downloads/windows/), be sure
  to select the option to add Python to PATH / environment variables
- Install [NSIS](https://nsis.sourceforge.io/Download)
- Install [Visual Studio](https://visualstudio.microsoft.com/downloads/),
  select the `Desktop Development with C++` package

## MSYS2 Terminal
```
cd ~
mkdir src && cd src
pacman -S git make
git clone https://github.com/stargateaudio/stargate.git
cd stargate
./scripts/msys2_deps.sh
cd src/vendor
# Because git submodule init does not seem to work on Windows
git clone https://github.com/stargateaudio/libcds.git
git clone https://github.com/spatialaudio/portaudio-binaries.git
# Build our dependencies
cd ..
make mingw_deps
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

## Visual Studio Terminal
- Open Visual Studio
- When prompted to open a project or folder,
  open folder `C:\msys64\home\starg\src\stargate\src\engine`
- View -> Terminal
- Ensure that `Developer Command Prompt` is selected (not PowerShell)
- `.\cv2pdb\cv2pdb.exe .\stargate-engine.exe`

## Windows cmd.exe
```
venv\stargate\Scripts\activate.bat
cd C:\msys64\home\starg\src\stargate\src
# Build the portable exe and installer exe
python windows\release.py
```

The build artifacts are now in `C:\msys64\home\starg\src\stargate\src\dist\`
