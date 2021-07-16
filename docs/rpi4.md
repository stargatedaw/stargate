# Raspberry Pi4
Stargate UI runs adequately on an rpi4, with some necessary tweaks.
The engine is very optimized and runs adequately without tweaks, but the
UI will lag unless additional optimizations are made to the operating system.

## Increase GPU memory
By default, the amount of memory reserved for the GPU is only 64MB.  Increase
it to the maximum (512MB) by editing `/boot/config.txt`, adding this line:
```
gpu_mem=512
```

If you are using the 2GB model and need more RAM for applications, you could
try 256MB instead.

## Install Fluxbox
Fluxbox has been found to be the only desktop environment lightweight enough to
run adequately on an rpi4 (period, not just for Stargate).  Gnome and KDE are
very slow on rpi4 and consume a lot of CPU and RAM, LXDE and LXQT are a bit
better, but Fluxbox is even much lighter than those.  You can use a distro like
MX Linux that installs it by default, or you can install it into NOOBS or
Ubuntu using these commands:

If you know of an alternative to Fluxbox that performs adequately, please
create an issue in the issue tracker to add it to the allow list.

```
sudo apt install fluxbox
```

For Ubuntu, select Fluxbox at login.

For NOOBS, you will have to create `~/.xsession` and add this content:
```
#!/bin/bash

fluxbox
```
If the file already exists, you will have to replace the existing window
manager with `fluxbox`.

