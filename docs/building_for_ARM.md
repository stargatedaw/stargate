# Compiling for ARM
Including popular boards such as the Raspberry Pi 4 (rpi4).

# Raspberry Pi 4 (rpi4)
[See the Raspberry Pi 4 documentation](./rpi4.md)

# Choosing an ARM SBC (single board computer)
rpi4 is very popular and has become the dominant SBC platform.  However, if you
are buying a SBC explicitly to run Stargate, it is recommended to shop around
and try to find a SBC that has a faster GPU, better GPU drivers, and if
possible, better CPU performance is always helpful.

# Steps
## Install all required dependencies for Debian or Ubuntu
```
scripts/debian_deps.sh
# or
scripts/fedora_deps.sh
```
## Creating packages
Note that you may be able to create packages using the package building
scripts:
```
scripts/deb.py --plat-flags='-march=native'
# or
scripts/rpm.py --plat-flags='-march=native'
```

## Compiling and installing manually
```
cd src/

# Preferred for performance
PLAT_FLAGS="-march=native" make
# or, if native has bugs or other issues
PLAT_FLAGS="" make

#install
sudo PREFIX=/usr/local make install
# or, Stargate is fully relocatable, you can do a root-less install
# to any folder you'd like, and you can even move the folder later.
PREFIX=$(your prefix) DESTDIR=$(where you want to install it) make install
```

