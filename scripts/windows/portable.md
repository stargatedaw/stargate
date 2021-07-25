# Overview
This is the current working-ish procedure for creating a portable Windows
executable.  This is a single file that can be run on any 64 bit Windows,
including from a flash drive.  Note that there is no more 32 bit MSYS2,
so we are not able to support 32 bit Windows.

# Create a fresh 64 bit Windows 10 VM
(or install to your hard drive if you are "into that")
- Create a user called stargate
- Install MSYS2
- Download and install Python for Windows, the Visual Studio compiled variant
  from python.org
## MSYS2 Terminal
```
cd ~
mkdir src && cd src
git clone https://github.com/stargateaudio/stargate.git
cd stargate
source scripts/mingw64-source-me.sh
./scripts/msys2_deps.sh
cd src/
make mingw_deps
cd engine
make mingw
```
## Windows Cmd.exe
```
cd C:\mingw64\home\starg\src
python -m venv C:\Users\starg\venv\stargate
C:\Users\starg\venv\stargate\bin\activate.bat
pip install pyinstaller
pip install -r requirements-windows.txt
pyinstaller windows.spec
```
# ..and that is it
File is dist\stargate.exe

