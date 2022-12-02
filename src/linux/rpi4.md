# Raspberry Pi4
Stargate UI runs adequately on an rpi4, with some necessary tweaks.
The engine is very optimized and runs adequately without tweaks, but the
UI will lag unless additional optimizations are made to the operating system.

## Operating System

We strongly recommend Manjaro (we use KDE, other desktops may work), aarch64
for Raspberry Pi 4.  You can use the official `Raspberry Pi Imager` utility to
download and install to a micro-SD card.  Be sure to use `gparted` or similar
to increase the size of the partition after imaging to use the entire micro-SD
card.

We strongly discourage Raspbian/NOOBS, despite being the official Raspberry Pi
Linux distro.  Version 10/Buster is ancient and performs poorly, version
11/Bullseye is very buggy at the time of this writing, and offers no
significant advantages over 10.

Despite Manjaro being less user friendly than other distros, we recommend it
for rpi4 because:

- Much smoother graphics, even when running a desktop like KDE.  Not sure why
  that is, probably newer, better GPU drivers and saner graphic effects config
- PyQt6 is available, which is much better than PyQt5 for running Stargate DAW.
  Qt6 also has much better support for various alternative platforms like ARM.
- It seems to be the most stable, polished and reliable distro for the rpi4,
  much better in our experience than Raspbian/NOOBS, Ubuntu and Fedora.

### Installing Stargate DAW

[See the Arch Linux instructions](../../docs/troubleshooting//arch_linux.md)

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

## Use the 'performance' CPU governor

This will greatly reduce audio dropouts and improve performance, but you will
need a proper heavy heatsink on your rpi4.  We recommend getting a heavy-duty
case that acts as a passive heatsink, something that weighs hundreds of grams.

### Permanently
```
sudo -i

pacman -Syu cpupower
vim /etc/default/cpupower
# Change the 'governor' field to 'performance'
systemctl start cpupower
systemctl enable cpupower

# Check that the changes applied
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Manually (you will need to do this every time before running Stargate)
```
# Become root
sudo -i

# Check the existing governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set to performance
for path in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  echo performance > $path
done

# Check that the changes applied
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```
