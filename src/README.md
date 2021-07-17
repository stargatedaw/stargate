# Source Code
# Building
[See the building instructions](../docs/building.md "Building")

# Architecture
The UI is written in Python and PyQt.  The audio/dsp engine is written in C
and can be run one of 2 ways:
- A separate process, communicating OSC over TCP sockets (default on Linux)
- A shared library (.so, .dll, .dylib) (default on Windows and Mac)

The separate process has the following advantages:
- Able to run as a different user than the UI
- More resilient to crashes, does not crash the UI if it crashes
- Can be restarted freely
- Many interesting options for debugging using GDB, LLDB, Valgrind and other
  tools.

The shared library has the following advantages:
- Does not require IPC (inter-process communication)
- Deeper integration with the UI than the subprocess (but presently this
  is not being done)

Likely the socket mode will become the dominant mode, and the library will be
kept around just in case there is a use for it on some platform where sockets
are too much trouble.

# Source Code Layout
Note that there is some very old legacy code not following these standards.
All new code should try to refactor anything it touches to comply with these
standards.

## engine/
The audio/dsp engine that interacts with audio and MIDI hardware,
generates/records/processes/plays audio.  Written in GNU89 C for
portable, stable, real-time performance.

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
or Qt dependenies in this library.

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

