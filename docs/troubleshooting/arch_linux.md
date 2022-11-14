# Arch Linux
This document describes how to build Stargate DAW for Arch Linux
and it's derivatives like Manjaro and others.

Note that Stargate DAW is available in [AUR](
  https://aur.archlinux.org/packages/stargate/), please:
- `Flag package out of date` to request an update to the latest version
  of Stargate DAW
- Vote to add to the main repos

Also, if you are using an `x86_64` CPU, you may wish to use the AppImage
executable, [see this](./appimage.md)

# Build Procedure
```
git clone https://github.com/stargatedaw/stargate.git
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
