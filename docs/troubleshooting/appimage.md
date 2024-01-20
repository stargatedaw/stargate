# Usage
Download the AppImage, then:
#### GUI File Browser
- right-click on the StargateDAW AppImage
- properties
- permissions
- allow executing file as program

or...
#### Terminal
```
chmod +x StargateDAW*.AppImage
```

# AppImage
The new AppImage is a portable executable that is meant to be used on almost
any Linux distro, without the need to install.  Simply download, extract the
`.tar.gz` file, then either run the AppImage from the command line, or double
click from a file browser.  Some distro security features may cause issues,
you can also run the AppImage from the command line with:
```
# Only do this once per release
./StargateDAW*.AppImage --appimage-extract
mv squashfs-root/ stargatedaw/
# Each time you want to run
./stargatedaw/AppRun
```

# Adding the AppImage to the start menu
If you wish to add the Stargate DAW AppImage to the start menu, when running
the AppImage there is an action in the main menu (the "hamburger" icon in the
upper left corner of the window after opening a project) to install (or
uninstall) a start menu shortcut.

This command will extract `stargate.png` next to the AppImage, and create
a `~/.local/share/applications/stargate.desktop` file to add Stargate DAW
to your start menu.

Note that this must be done everytime you download a new version, otherwise
the start menu entry will be pointing to the old version (which may be
deleted).

# Portable install mode
NOTE:
- It is recommended to use an exFAT formatted flash drive, as other formats
  such as FAT32 do not support  UNIX permissions to set the executable bit,
  and others are not compatible across all 3 major desktop platforms.
- Having said that, this is very unlikely to work for you, because distro
  security engineers don't like this kind of thing.  If the engine crashes
  during start up, try copying the AppImage from your flash drive to your
  hard drive and running it.  If it now works, then it is security settings
  (which probably cannot be changed easily, if at all).

If you would like to install Stargate DAW for Linux to a flash drive, or you
just want to store your projects and configurations next to the AppImage,
simply place the AppImage in the desired folder, and create an empty text file
called `_stargate_home` next to it.  Note that the Linux AppImage can be
installed alongside a Windows portable install and a MacOS app bundle at the
same time to create a (nearly) universal DAW flash drive.
# General problems
## Engine crashes
If the engine is crashing, it probably means that the version of portaudio
and portmidi that are packaged are not compatible with your distro.  You
can try installing those packages from your distro.

# Linux distro-specific issues
## Any
### Qt could not initialize any platform plugins
Usually the simplest way to solve this is to install `python3-pyqt5`, or
whatever the package may be called on your distro

## Ubuntu 22.04 and later AppImage issues
### AppImage will not launch
Ubuntu does not come with `libfuse2` already installed, which is a requirement
of the AppImage runtime to run ANY appimage.  You will need to run the
following commands:
```
sudo apt update && sudo apt install libfuse2 python3-pyqt5

# Or alternately, extract the AppImage and run
./StargateDaw-*.AppImage --appimage-extract
mv squashfs-root StargateDAW
./StargateDAW/AppRun
```

However, double-clicking still will not open it.  You will need to right-click
and choose `Run as program` to launch Stargate DAW.  Or install to the start
menu using the `Adding the AppImage to the start menu` instructions below.

## Fedora/CentOS/RHEL/Rocky/Alma/etc... AppImage issues
### 'Could not display...' 'There is no application installed for appimage...'
If the file is on a file system that does not support POSIX file
permissions, such as a FAT32 flash drive, this will not work until you copy
the file to an exFAT, ext4, xfs, etc... file system.

### EL8 variants: AppImage Unable to find shared libraries, window does not start
This has been seen as a result of selinux in RHEL8 and it's clones.  The
`LD_LIBRARY_PATH` environment variable is being stripped away by SELinux.
Given that AppImage relies on `LD_LIBRARY_PATH` to find it's libraries, it is
unlikely that any AppImage would work.  Either disable SELinux or update your
policy to not do that.  Or upgrade to EL9+, where they realized the err of
their ways and stopped doing that (yet, decided to keep EL8 this way for
"stability").

