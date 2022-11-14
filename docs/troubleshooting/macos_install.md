# MacOS Installation Troubleshooting
This document describes how to deal with various MacOS issues regarding
the installation of Stargate DAW.

# Basic installation
Double-click on the .dmg file, drag and drop it into the Applications folder.
If you see a pop-up warning that there is already a Stargate DAW app bundle
installed, answer `Replace` to the dialog.

# Issues
## "Unverified Developer"
If your Mac will not open apps from unverified developers:
```
In the Finder on your Mac, locate the app you want to open.  (NOTE: This will
be /Applications for Stargate DAW)

Don’t use Launchpad to do this. Launchpad doesn’t allow you to access the
shortcut menu.

Control-click (or 2-finger/right-click) the app icon, then choose Open
from the context menu.

Click Open.

The app is saved as an exception to your security settings, and you can open it
in the future by double-clicking it just as you can any registered app.
```
from [HERE](
  https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unidentified-developer-mh40616/mac
)

Note that the app is unverified because we are refusing to pay the fee or have
our legal name(s) publicly listed for all to see.  You can verify that the
downloads have not been modified by comparing the sha256 sums we provide, or
else build the source code yourself using the instructions provided.

## Unable to record the built-in microphone
If you wish to record using the built-in MacBook microphone,
[see this](https://support.apple.com/en-us/HT209175)

## Portable install mode
NOTE: It is recommended to use an exFAT formatted flash drive, as other formats
such as FAT32 do not support  UNIX permissions to set the executable bit,
and others are not compatible across all 3 major desktop platforms.

If you would like to install Stargate DAW for MacOS to a flash drive, or you
just want to store your projects and configurations next to the app bundle,
simply place the app bundle in the desired folder, and create a file called
`_stargate_home` next to it.  Note that the MacOS app bundle can be installed
alongside a Windows portable install and a Linux AppImage to create a
(nearly) universal DAW flash drive.
