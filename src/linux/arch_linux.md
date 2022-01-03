# Arch Linux
This document describes how to build Stargate DAW for Arch Linux
and it's derivatives like Manjaro.

Note that Stargate DAW is available in [AUR](
  https://aur.archlinux.org/packages/stargate/)

# Procedure
```
git clone https://github.com/stargateaudio/stargate.git
cd stargate/scripts
# First time only
# Depending on which variant of Arch you are using, you may need to install
# additional packages not included here
./arch_deps.sh
# Every time
git pull
./pkgbuild.py --install
# Package is a .zst file in the root of the repo along with PKGBUILD
```

Will it work now?  Probably not, you'll probably need to do additional things
such as update the system (`sudo pacman -Syu`), manually delete conflicting
files, etc...  Standard Arch Linux operating procedure.
