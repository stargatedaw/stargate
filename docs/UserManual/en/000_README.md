# Introduction
Stargate is a holistic audio production that focuses on deeply integrated
components and workflows.  This provides users with a powerful, stable and
efficient suite of audio tools.

# Plugins
Plugins are organized into virtual plugin racks.  The plugins are all an
internal plugin format.  For stability and performance across all supported
platforms, 3rd party plugin formats are not supported.  3rd parties can
contribute plugins to Stargate, but they must be integrated into the main
source code repository and thoroughly tested for quality.

# Hardware Support
Stargate supports any audio and MIDI devices supported by Portaudio and
Portmidi, respectively.

# Platform Support
Stargate targets any platform that can run Python, PyQt, and has drivers for
production-grade audio and MIDI hardware.  The main supported platforms are
Linux on x86 and ARM(including rpi4), Mac OSX, and Windows.  It may be
possible to compile and run on other platforms, but you must support it
yourself.  Pull requests are accepted to add support for other platforms.
