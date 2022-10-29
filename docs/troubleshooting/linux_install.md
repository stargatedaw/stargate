# Linux Installation Troubleshooting
This document describes all of the ways that Linux distros and package managers
make themselves user-unfriendly, and what you can do about it.  If you discover
additional steps required for your distro of choice, please submit a pull
request to update this document.

# Important Notes
## Pipewire
Pipewire is a new technology with many bugs.  Note that DAWs do not directly
interface with Pipepwire, and by extension have no way to directly influence
the behavior or Pipewire.  Issues with Pipewire must be reported to the
Pipewire developers.

If you experience issues, try testing on a distro that does not use Pipewire.
If it works in the non-Pipewire distro, file bugs with Pipewire and your
distro (and if your priority is to actually make music, keep using the
non-Pipewire distro until Pipewire actually works for you).

## "bleeding edge" distros
Recent major releases of compilers, kernels, libc, lib\*, and other core system
software have bugs when they are new, just like any other software.  It's only
logical to expect problems when building on a shaky foundation that can add
bugs to the software that relies on it.  If you are using a bleeding edge
distro like Arch, Fedora and many others, and experience problems, try
something more stable like the latest Ubuntu LTS.  If older distros are not
an option because you are using newer hardware, then report issues you are
having to the appropriate upstream project.

# All distros: AppImage
The new AppImage is a portable executable that is meant to be used on almost
any Linux distro, without the need to install.  Simply download, run:
```
chmod +x /path/to/download/folder/StargateDAW*.AppImage
```
, then either run the AppImage from the command line, or double click from
a file browser.

## Portable install mode
If you would like to install Stargate DAW for Linux to a flash drive, or you
just want to store your projects and configurations next to the AppImage,
simply place the AppImage in the desired folder, and create a file called
`_stargate_home` next to it.  Note that the Linux AppImage can be installed
alongside a Windows portable install and a MacOS app bundle at the same time
 to create a (nearly) universal DAW flash drive.

## Fedora/CentOS/RHEL/Rocky/Alma/etc... issues
### 'Could not display...' 'There is no application installed for appimage...'
If the file is on a file system that does not support POSIX file
permissions, such as a FAT32 flash drive, this will not work until you copy
the file to an ext4, xfs, etc... file system.

#### GUI File Browser
- right-click on the StargateDAW AppImage
- properties
- permissions
- allow executing file as program

#### Terminal
```
chmod +x StargateDAW*.AppImage
```

### EL8 variants: Unable to find shared libraries, window does not start
This has been seen as a result of selinux in RHEL8 and it's clones.  The
`LD_LIBRARY_PATH` environment variable is being stripped away by SELinux.
Given that AppImage relies on `LD_LIBRARY_PATH` to find it's libraries, it is
unlikely that any AppImage would work.  Either disable SELinux or update your
policy to not do that.  Or upgrade to EL9+, where they realized the err of
their ways and stopped doing that (yet, decided to keep EL8 this way for
"stability").

## Adding the AppImage to the start menu
If you wish to add the Stargate DAW AppImage to the start menu, there is
a special command that is only available in the AppImage:
```
/path/to/Stargate*.AppImage appimage-start-menu
```

This command will extract `stargate.png` next to the AppImage, and create
a `~/.local/share/applications/stargate.desktop` file to add Stargate DAW
to your start menu.

Note that this must be done everytime you download a new version, otherwise
it will be pointing to the old version (which may be deleted).

# deb distros
Debian, and it's derivatives like Ubuntu, MX Linux, Linux Mint, and many
others.

Note that `dpkg` is not a viable way to install any packages, because it has
no concept of dependency management.  Use `sudo apt install ./package-name.deb`
instead, which will install dependencies.  `dpkg` is a low level tool meant to
be used by other tools such as `apt`

## Ubuntu
You must enable the universe and multiverse repositories to get all of the
dependency packages.

```
sudo add-apt-repository universe
sudo add-apt-repository multiverse
```

# RPM distros
Fedora, and it's derivatives like CentOS, RHEL, Rocky, also OpenSUSE.

You will need to install the [RPM Fusion repos](https://rpmfusion.org/)
to get all of the recommended dependency packages.

## CentOS 8, including Stream
You will need to install `epel-release` and enable the `Power Tools` repo.
```
sudo dnf install epel-release
sudo dnf config-manager --set-enabled powertools
sudo dnf update
```

## CentOS Stream 9
As of December 2021, it seems they have not packaged many of the required
dependencies.  Maybe in the coming months it will be possible without adding
non-official repositories

## OpenSUSE
OpenSUSE expects all packages to be signed with a code signing cert that they
recognize, which we do not have.  So when `zypper` warns you about unsigned
code and asks you what to do, enter `i` for "ignore"

# Arch / PKGBUILD
Arch, Manjaro, EndeavourOS and many others.

Stargate DAW is available in [AUR](
  https://aur.archlinux.org/packages/stargate/)
To build it yourself, [see this document](../src/linux/arch_linux.md)

# Building from source code

- Is there already a pre-compiled package for your distro?  Does it work?
  If not, did you report that it does not work?
- There are instructions for how to do this, did you look for them?  Note that
  a DAW is a massively complex piece of software, and building it on
  every mainstream desktop platform (read: not just Linux) and CPU
  architecture requires an elaborate custom build system that will not be as
  simple as `./configure && make && make install`
- Are you using an officially supported distro like Fedora or Ubuntu?  If it
  works on the officially supported distro but not your distro, did you file
  a bug with your distro?
- Did you or or your distro modify any of the default, carefully selected
  and well tested compiler flags?  Are you aware that not all code can compile
  with all compiler flags (and this behavior is not a bug), and that
  compilers are loaded with bugs when using obscure optimization flags?  Are
  you aware that there are good reasons why most distros do not use -O3 by
  default, that it adds bugs and usually is not significantly faster, and could
  even be slower?
- Does your distro use a recent version of your compiler?  Are you aware that
  major releases of compilers tend to be buggy for at least the first 6-12
  months?  Can you compile it on something older, like GCC in the current
  (or better yet, previous) stable version of Debian?

