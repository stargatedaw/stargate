# MacOS Installation Troubleshooting
This document describes how to deal with various MacOS issues regarding
the installation of Stargate DAW.

# Basic installation
Double-click the .pkg file to open the install wizard.

# Issues
## "Unverified Developer"
Note that you may get a warning about unidentified/unverified developer.  This
is because presently we are not paying a yearly fee to be part of the Apple
Developer program.  To get around this, you can use Google to find instructions
[such as this](https://customercare.primera.com/portal/en/kb/articles/how-to-open-a-primera-app-that-hasn-t-been-notarized-or-is-from-an-unidentified-developer)

## Unable to record the built-in microphone
At the moment, it will not be possible to request microphone access from 
Stargate DAW, however, there is a workaround.  You can open a Terminal and
run Stargate DAW from the terminal, and grant the terminal access to the 
microphone when prompted.  This is the command to run Stargate DAW from the
terminal:
```
/Applications/Stargate\ DAW.app/Contents/MacOS/stargate
```

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
