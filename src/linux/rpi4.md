# Raspberry Pi4
Stargate UI runs adequately on an rpi4, with some necessary tweaks.
The engine is very optimized and runs adequately without tweaks, but the
UI will lag unless additional optimizations are made to the operating system.

## Operating System

It is strongly encouraged that you not use Raspbian/NOOBS.  For Raspberry Pi 4,
Manjaro KDE for aarch64 is a much better choice.  You can use the official
`Raspberry Pi Imager` utility to download and install to a micro-SD card.
Be sure to use `gparted` or similar to increase the size of the partition after
imaging to use the entire micro-SD card. 

### Installing Stargate DAW
[See the Arch Linux instructions](./arch_linux.md)

### Operating System Settings

Note that the GPU on an rpi4 is exceptionally weak, and the Linux driver is 
low quality.  The following settings apply to KDE, they may be different on
a different desktop environment.

System Settings -> Display and Monitor:

Display Configuration:
- Change screen resolution to the lowest value you can tolerate.  1920x1080 at
  most, 1280x720 (or similar) is better

Compositor:
- Tearing Prevention (vsync): Only when cheap
- (you may want to experiment with other settings)

## Increase GPU memory
By default, the amount of memory reserved for the GPU is only 64MB.  Increase
it to the maximum (512MB) by editing `/boot/config.txt`, adding this line:
```
gpu_mem=512
```

If you are using the 2GB model and need more RAM for applications, you could
try 256MB instead.

