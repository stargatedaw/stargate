# MacOS Installation Troubleshooting
This document describes how to deal with various MacOS issues regarding
the installation of Stargate DAW.

# Basic installation
Double-click the .pkg file to open the install wizard.

# Issues
## Spectrum analyzer does not work, various issues when trying to use it
Stargate DAW uses the UDP protocal for communicating between the engine and
the UI.  UDP has a limit of 64kb for packet sizes, which Stargate DAW stays
within.  However, by default, MacOS limits it to 9216 bytes (which sometimes
Stargate exceeds), `<sarcasm>` because apparently Apple knows better than the
Internet Engineering Taskforce what the UDP protocol limits should be, and
anybody that is sending more than the nice round number of 9216 bytes in one go
is `doing it wrong`.`</sarcasm>`

You can fix it by running this command:
```
sudo sysctl -w net.inet.udp.maxdgram=65535
```

## "Unverified Developer"
Note that you may get a warning about unidentified/unverified developer.  This
is because presently we are not paying a yearly fee to be part of the Apple
Developer program.  To get around this, you can use Google to find instructions
[such as this](https://customercare.primera.com/portal/en/kb/articles/how-to-open-a-primera-app-that-hasn-t-been-notarized-or-is-from-an-unidentified-developer)

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
