# Overview
This is the procedure for creating the Windows portable executable and
installer.  Note that it may be possible to compile for 32 bit Windows, but at
the present time it is untested and unsupported

The following components must be setup and configured prior to building:
- Python
- MSYS2
- NSIS
- Stargate repo and dependencies

The build steps proceed as follows:
- Pull the source code
- Build the engine exe
- (optional) Strip the DWARF debug symbols and convert them to PDB
- Run pyinstaller to create the portable executable
- Run NSIS to create the Windows installer

# Initial Setup
## Create a fresh 64 bit Windows 10 VM
(or install Windows to your hard drive if you are `into that`).
The VM should have at least 100GB of hard disk space

- Create a user called stargate (the rest of the instructions assume this name
  it is not an actual requirement to have this user name)
- Install [MSYS2 64bit](https://www.msys2.org/wiki/MSYS2-installation/)
- Install [Python3 64bit](https://www.python.org/downloads/windows/), be sure
  to select the option to add Python to PATH / environment variables. At the
  time of this writing, Python3.7 and later are supported.
- Install [NSIS](https://nsis.sourceforge.io/Download)
- Install [Visual C++](https://visualstudio.microsoft.com/vs/)

### Optional
- Install [Visual Studio](https://visualstudio.microsoft.com/downloads/),
- Install [WinDbg](
    https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/debugger-download-tools
  ).  Useful for debugging the engine, but you must do extra steps to enable 
  debug symbols.  You can also use GDB in MSYS2.

## MSYS2 Terminal
```
# Initial update, this will very likely force an MSYS2 terminal restart
pacman -Syu

# Restart terminal
```

```
# Update again
pacman -Syu
cd ~
mkdir src && cd src
pacman -S git make
git clone --recursive https://github.com/stargateaudio/stargate.git
cd stargate/src
./windows/msys2_deps.sh
make mingw_deps
```

## Windows cmd.exe
```
cd C:\msys64\home\starg\src\stargate\src
python -m venv venv\stargate
venv\stargate\scripts\activate.bat
pip install -r windows\requirements.txt
```

# Creating a new release
## MSYS2 Terminal
```
cd ~/src/stargate/src
git pull
# Note that you may need to run this again
# make mingw_deps
cd engine
. mingw64-source-me.sh
make mingw
```

## Visual Studio Terminal
NOTE: Deprecated, no longer required for release, but instructions kept in
case anybody wants Windows debug symbols

There are 2 different ways to execute this command.

Either:
- Open Visual Studio
- When prompted to open a project or folder,
  open folder `C:\msys64\home\starg\src\stargate\src\engine`
- View -> Terminal
- Ensure that `Developer Command Prompt` is selected (not PowerShell)

Or:
- Open Developer Command Prompt for VS 20XX` from the Start Menu
- `cd C:\msys64\home\starg\src\stargate\src\engine`

Finally, execute the command:
- `.\cv2pdb\cv2pdb.exe .\stargate-engine.exe`

## Windows cmd.exe
```
cd C:\msys64\home\starg\src\stargate\src
venv\Scripts\activate.bat
# Build the portable exe and installer exe
python windows\release.py
```

The build artifacts are now in `C:\msys64\home\starg\src\stargate\src\dist\`
