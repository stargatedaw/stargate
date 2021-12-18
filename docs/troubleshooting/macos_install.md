# MacOS Installation Troubleshooting
This document describes how to deal with various MacOS issues regarding
the installation of Stargate DAW.

# "Unverified Developer"
If your Mac will not open apps from unverified developers, go to
`Apple Logo->System Preferences->Security & Privacy->General->Stargate...Open anyway`.
This happens because we do not pay an Apple "partner" a lot of money for a code
signing certificate.  Literally every application that does not have this
problem has paid the fee.

# Unable to record the built-in microphone
If you wish to record using the built-in MacBook microphone,
[see this](https://support.apple.com/en-us/HT209175)

# Porable install mode
If you would like to install Stargate DAW for MacOS to a flash drive, or you
just want to store your projects and configurations next to the app bundle,
simply place the app bundle in the desired folder, and create a file called
`_stargate_home` next to it.  Note that the MacOS app bundles can be installed
alongside a Windows portable install (at the time of this writing, there is
no universal portable Linux install yet).
