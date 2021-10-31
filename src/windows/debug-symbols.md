# Debug Symbols
This document describes how to install Windows .pdb debug symbols for 
dependencies, to allow using WinDbg and enable better stack traces when a
library segfaults.

# Procedure
## From the MSYS2 shell
Get the MINGW packages repo if you have not already done so, or just
`git pull` if you already have it
```
cd ~/src
git clone https://github.com/msys2/MINGW-packages.git
cd MINGW-packages
```

Set the current working directory to the package you want to build, for 
example: `cd mingw-w64-portmidi`

`vim /etc/makepkg-mingw.conf` and ensure that `!strip` and `debug` are set in
the `OPTIONS` line.  The default is the inverse, `strip` is enabled and 
`debug` is not.


Build and the package.  Note that you may need to debug this by installing
missing build dependencies or other tools required to build the package.
```
makepkg-mingw
pacman -U $PACKAGE_NAME.zst
cd ~/src/stargate/src
make mingw_deps
```

# From the Visual Studio Developer Command Prompt
```
cd c:\msys64\home\starg\src\stargate\src\engine
.\cv2pdb\cv2pdb.exe .\$PACKAGE_NAME.dll
```
