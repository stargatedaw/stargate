# Description
This document describes how to use Stargate DAW as a benchmark for highly
optimized, multithreaded audio DSP code written in C.  Specifically, this
procedure is for Linux, it would be possible on Windows, but not trivially
easy to do from the installed artifacts in the Windows installer.

# Overview
The Stargate UI is a PyQt5/6 application that controls the engine subprocess
that is written in C, by invoking the engine CLI and communicating over UDP
sockets on localhost.

When the user renders their project to a `.wav` file, the UI invokes the engine
CLI again, but with a different set of arguments that tells it to play a
specific part of the song, write the output to a file instead of an audio
device, and not to listen for communications over sockets.  We can use this
mechanism to benchmark the code.

## Considerations
The track routing in the project affects multicore scaling, 2 different
projects will not have identical scaling.  For example, if every track routes
directly to the `Main` track, the project will scale very well to many cores,
as many as cores as there are tracks are playing at the same time.  This is the
ideal case for scaling.

Conversely, if every track routes to a different track, this is the worst case,
effectively the project is single threaded.  This is not a realistic use case,
the normal, average use case is somewhere between, but much closer to the ideal
use case.

# Benchmark setup
## Download or build Stargate DAW
See [the build instructions](./building.md) or the
[releases page](https://github.com/stargateaudio/stargate/releases).

## Run the benchmark
### Acquiring projects to benchmark
[Download the CPU-heavy stress-testing project here](./benchmark-project.zip)

Or clone the demo projects for real world benchmarking
```
git clone https://github.com/stargateaudio/stargate-v1-demo-projects.git
# Projects are in stargate-v1-demo-projects/src/*/
```

### Generate the engine command from the UI
This is needed to generate the start and end parameters for the command, to
know which beat number the render should start and stop at.  Using arbitrary
numbers is also an option, but it is best to render the entire song and not
include empty space at either end, as it may skew the results.

* Opening the project in Stargate DAW
* Make sure that the region start/end are set to the portion of the song
  you want to render by right-clicking on the sequencer header and setting
  the region start/end
* Go to `Menu (top left of the screen)->File->Render`
* Click the `Copy cmd args` button, and close the dialog
* Close Stargate DAW
* Open a terminal
* Type in the `stargate-engine` binary you want to use, ie: ./stargate-engine,
  /usr/bin/stargate-engine, etc...
* Paste the command arguments you copied from the render dialog

You should have with something like this in your terminal window:
```
./stargate-engine daw '/home/me/stargate/projects/myproject' test.wav 8 340 44100 512 3 0 0 0
```

### Parameterizing a benchmarking shell command

```shell
# Sample rate.  Normally this is 44100 or 48000, but users sometimes choose
# 96000 or 192000 for higher quality, at a much higher CPU cost.  Stargate DAW
# has been tested at rates over 1,000,000, although such rates adversely affect
# the audio by drastically changing the mix characteristics
SR=44100
# Buffer size.  In real time audio, this affects latency, lower sizes have
# less latency, but make less efficient use of the CPU. At 44100 sample rate,
# 64 is a very low value, 512 is more normal, typical users may use 128
# to 1024.  Doubling the sample rate effectively halves the latency of this
# value, keep that in mind when changing one or the other.  Latenchy is
# calculated as (BUF_SIZE / SR) * 1000 == latency in milliseconds
BUF_SIZE=512
# The number of worker threads to spawn.  The limit is 16, setting to zero
# causes Stargate DAW to automatically select a very conservative value
# of 1-4 depending on the CPU that was detected
THREADS=8
# The project folder to render.  Specifically, this is the folder that contains
# the `stargate.project` file.
PROJECT=~/stargate/projects/myproject
# The file to output.  If you want to keep all of the artifacts from this run,
# change the filename between runs
OUTFILE=test.wav
# This is the musical "beat" number within the project to begin rendering at.
# 0 being the first beat of the song.  It is best to get this by opening
# the project in Stargate DAW as described above, but you could also use
# arbitrary numbers.  This should be a low number, like 0 or 8
START=8
# This is the musical "beat" number within the project to stop rendering at
# This should always be a (much) larger number than ${START}
END=340

./stargate-engine daw ${PROJECT?} ${OUTFILE?} ${START?} ${END?} ${SR?} ${BUF_SIZE?} ${THREADS?} 0 0 0
```

The `OUTFILE` parameter will exist as a file after the render.  Note that the
file may be deterministic within the same version of Stargate DAW, but floating
point rounding error may cause it to be non-deterministic.  You can listen to
the file to check for correctness, but checksums may (or may not) work as
intended.

Using this to parameterize your benchmark with scaling values, you can now
grep the output for these lines:

Affirmation of how many threads were actually spawned.
```
Spawning 16 worker threads
```

Total time to render the file.  This does not include time to load the
project directory, which is not threaded, nor does it make sense to thread.
If you measured total run time of the process, it would include the load
time and skew the results.
```
Completed v_daw_offline_render in 28.158311 seconds
```

Length of the `.wav` file that was rendered.  If you open it in a music player,
this is how long it would play.
```
Song length: 155.643356 seconds
```

This is the rate that Stargate DAW can render.  For example 1:1 means that it
can keep up with real time, no faster or slower.  For example, a 120 second
song rendered in 120 seconds.  3: 1 means that Stargate DAW can output 3
seconds of the song in 1 second (on average, for the entire song).  Less than
1:1 means the system is too slow to play the project back in real time.
```
Ratio, render time to real time (higher is better):  5.527439 : 1
```

# Examples
This is a benchmark of my current system, a Ryzen 5950x with 16 cores, using
a development build shortly after the Stargate DAW 21.10.8 release.

The project is an unrealistically heavy project designed to scale well that you
can [download here](./benchmark-project.zip).  It consists of 31 instances of
the FM1 synthesizer running the unison-heavy `Festivus` patch, playing a chord
heavy MIDI item.  Nobody would realistically run such a heavy project, as such
you should not try to open the project and play it back in Stargate DAW unless
you have a CPU with many cores AND you have configured Stargate DAW to use at
least 8 cores in the `Hardware Settings` dialog on the welcome screen.
However, you can offline render it on any hadrware, even a Raspberry Pi 4 or an
ancient laptop.

16 threads, 44100 sample rate, 512 buffer size:
```
Completed v_daw_offline_render in 28.158311 seconds
Song length: 155.643356 seconds
Ratio, render time to real time (higher is better):  5.527439 : 1
```

8 threads, 44100 sample rate, 512 buffer size:
```
Completed v_daw_offline_render in 47.669643 seconds
Song length: 155.643356 seconds
Ratio, render time to real time (higher is better):  3.265041 : 1
```

4 threads, 44100 sample rate, 512 buffer size:
```
Completed v_daw_offline_render in 93.022316 seconds
Song length: 157.512562 seconds
Ratio, render time to real time (higher is better):  1.693277 : 1
```

2 threads, 44100 sample rate, 512 buffer size:
```
Completed v_daw_offline_render in 182.148489 seconds
Song length: 157.512562 seconds
Ratio, render time to real time (higher is better):  0.864748 : 1
```

Note that with 2 threads, we entered the point where the ratio fell below 1:1,
therefore there is no way this project could be played in real time in Stargate
DAW on 2 CPU cores.  However, given that this project is completely,
unrealistically CPU heavy (many times more so than a normal song), this is a
testament to how CPU efficient the code is that such a heavy project can almost
run on 2 cores.

