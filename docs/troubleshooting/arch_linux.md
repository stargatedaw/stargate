# Arch Linux
This document describes how to build Stargate DAW for Arch Linux
and it's derivatives like Manjaro and others.

Note that Stargate DAW is available in [AUR](
  https://aur.archlinux.org/packages/stargate/
)

Also, if you are using an `x86_64` CPU, you may wish to use the AppImage
executable, [see this](./appimage.md)

# Build Procedure
```
git clone --recurse-submodules https://github.com/stargatedaw/stargate.git
cd stargate
# First time only
# Depending on which variant of Arch you are using, you may need to install
# additional packages not included here
./scripts/arch_deps.sh
```

## Building Manually
```
cd src

make
# Or for rpi4/ARM:
PLAT_FLAGS='-march=native' make

sudo make install
# Or just run without installing
./scripts/stargate
```

## PKGBUILD
```
./pkgbuild.py --install
# Package is a .zst file in the root of the repo along with PKGBUILD
```

Will it work now?  Probably not, you'll probably need to do additional things
such as update the system (`sudo pacman -Syu`), manually delete conflicting
files, etc...  Standard Arch Linux operating procedure.
