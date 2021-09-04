# Overview
This is the procedure for creating Windows build artifacts, both the installer,
and the portable executable suitable for running from a flash drive.

# Initial Setup
## Create a fresh 64 bit Windows 10 VM
(or install to your hard drive if you are `into that`)
- Create a user called stargate
- Install MSYS2
- Download and install Python for Windows, the Visual Studio compiled variant
  from python.org
- Install NSIS

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

# Creating a new release
```
cd engine
source mingw64-source-me.sh
make mingw
```
## Windows cmd.exe
```
venv\stargate\Scripts\activate.bat
cd C:\mingw64\home\starg\src
python -m venv C:\Users\starg\venv\stargate
pip install pyinstaller
pip install -r requirements-windows.txt
# Build the portable exe and installer exe
python windows\release.py
```

The build artifacts are now in `dist/`
