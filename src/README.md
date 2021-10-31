# Source Code
# Building
[See the building instructions](../docs/building.md "Building")

# Architecture
The UI is written in Python and PyQt.  PyQt5 and PyQt6 are both supported,
presently the default is PyQt6 because it fixes some issues with Wayland, but
most package managers do not have PyQt6 at the time of this writing.  You can
specify PyQt5 by passing in the environment variable `_USE_PYQT5=1`.  If PyQt5
is available, and PyQt6 is not, then PyQt5 will be used without any additional
configuration.  Once PyQt6 is available in Debian stable, Fedora, MinGW and
Homebrew, PyQt5 will be deprecated and removed.

The audio/dsp engine is written in C and runs as a separate process,
communicating over UDP sockets.

Using a separate process has the following advantages:
- The UI can be written in a very high-level language, and the engine in a
  very low-level language, the best of both worlds
- Able to run as a different user than the UI
- More resilient to crashes, does not crash the UI if it crashes
- Can be restarted freely
- Many interesting options for debugging using GDB, LLDB, Valgrind and other
  tools.

# Source Code Layout
Note that there is some very old legacy code not following these standards.
All new code should try to refactor anything it touches to comply with these
standards.

## engine/
The engine that interacts with audio and MIDI hardware,
generates/records/processes/plays audio.  Written in GNU89 C for portable,
stable, real-time performance.

## files/
Various non-source-code files that are distributed with Stargate, including
plugin presets, themes, desktop files.

## meta.json
Information such as major and minor release names and numbers.

## scripts/
Executables to be installed to /usr/bin or elsewhere in `$PATH`.

## sglib/
The back-end library for the Stargate UI.  All business logic, models
and related code should go in this library.  There should be no presentation
or Qt dependencies in this library.

Divided into main areas:
- `api`: `sgui` should interact with the engine and file formats using
  API functions in this submodule
- `files`: Defines the project file structure
- models: Define data models here using `pymarshal`

## sgui/
The UI for `stargate`.  The UI should contain as little logic as possible,
it should make calls into `sglib.api` to interact with the rest of the stack.

## test/
Python unit tests using `pytest`.  `sglib` is expected to have 100% coverage.
Presently, `sgui` is tested manually.  `engine` has it's own unit tests in
`engine/tests`, and is expected to have close to 100% coverage.

## vendor/
External libraries and applications (developed by Stargate or 3rd parties) used
by Stargate that are not readily available on all target platforms.

