# Overview
This document describes the design principles this project was founded with,
that are reflected in the current state of the code.  Any and all of it is
negotiable, but the project makes no promises to overturn any of these
principles without great justification.  If you intend to make a feature
request (FR) or pull request (PR), please consider how you can make it align
with the core project principles, rather than submitting a request to
implement feature X, just because you are used to working this way in DAWs
Y and Z.  It is far more likely that your FR/PR will be accepted and
implemented if it aligns with the core project principles.

# Principles
## 1. A unique and carefully curated experience
Stargate does not intend to be a DAW just like any other DAW.  As a one person
development team (with some short-term assistance on cosmetic aspects from
others along the way), Stargate must think differently, and provide a unique
experience.  I hope to attract more developers to the platform, but I have
to assume that I will be doing this alone for the foreseeable future, given
the specialized knowledge and high barrier to entry to contribute to DAWs
and plugins at a high level (and the fact that those who can contribute tend
to start their own projects).

For example: VST support.  I could implement it, but it would make impossible
most of the other design principles that make this project unique.  I would
then have to undertake the burden of supporting thousands of VST plugins, many
of which are poorly coded and unstable.  I would have to add an endless stream
of quirks to try to keep their software from crashing my software.  At which
point in time, what value would this project have?  Just another DAW supporting
VSTs, I have no delusion that I can do this better than companies like
Steinberg and Ableton with hundreds of employees.  Maybe the value could be "a
better free/libre VST hosting DAW than the other libre/free DAWs", but then it
would still be a poor-man's Ableton, Cubase or FL Studio with regard to VST
support.  If I implement VST support (like every other DAW), what motivation
will you have to commit to using my DAW that now gives you exactly the same
experience you could get anywhere else?

## How we achieve this
- Innovation.  We aim for unique workflows and concepts.  We are not
  completely averse to implementing a feature that another DAW has, but we
  will not erode our aspirations for the future of music production to
  provide a more familiar experience like the DAW you already use.
- Complete control over the entire stack.  Maybe we, or you have a great
  idea that involves a drastic change to the plugin API (our internal
  equivalent of the VST standard).  Without control over the entire ecosystem,
  the only thing that can be done is to release a new major version of the
  standard, and hope developers adopt it, while supporting the old standard
  indefinitely.  With the entire ecosystem in one repository, we are free
  to make drastic changes as needed, without the bureaucracy of managing
  public standards and abandoned (but still widely used) plugins.

## 2. Base hardware requirements: Raspberry Pi 4, 15 year old laptop
Stargate is a DAW for everybody, regardless of socio-economic status.

The development team regularly tests against these 2 targets to ensure that
the application can run adequately on these platforms.  When most DAWs
proclaim Raspberry Pi 4 support, they only refer to being able to sequence
audio and other tasks that would be lightweight on any CPU.  This project
also works well on low-end hardware using the built-in plugins, even using
heavy synthesizer patches with many unison voices.

### How we achieve this
- Engine and plugins written in C.  C++ is capable of similar performance, but
  only if you use the subset of it that looks exactly like C.  C is more
  easily portable, with stable language standards that can be universally
  compiled on any platform.
- A full suite of built-in plugins.  By retaining control over the plugin
  ecosystem for this project, we can ensure a quality experience across the
  full spectrum
- Regular testing against a Raspberry Pi 4B 4GB and 2012 AMD Trinity laptop.
  Using a lightweight rpi4 distro like NOOBs, a 2GB rpi4 would be adequate.
  There should be a gradient of usability all the way back to 20 year old
  hardware, but we do not have any such hardware to test.
- Stargate is regularly tested against the following display resolutions:
  1280x720 (720p), 1920x1080 (HD), 3840x2160 (4k), to ensure that users of new
  hardware and old hardware both have a great experience.

## 3. Cutting corners on sound quality is not the way to achieve #2
DSP code is expected to be highly optimized.  Outside developers submitting
PRs will receive as much assistance as needed to get the performance of their
code to optimal levels.  Writing optimal C code is a deep subject that
requires deep knowledge of how CPUs and memory works, writing a complete guide
to writing optimal DSP code in C is outside the scope of this project.
However, there are many great resources on the internet, and we will assist
as much as possible.

### How we achieve this
- Engine and plugins written in C.  See the above rationale.
- Creative optimizations, when an operation is simply heavy by nature

## 4. Projects should be completely portable from one computer to another
This facilitates great collaboration.  For example, 3 internet friends in
Africa, USA and China could pass a project to each other around the clock,
each one adding their own unique spin to the project each day.

Any user should be able to zip/tar/whatever a project folder up, send it
to another computer, even if it has a different operating system or different
CPU architecture, and have the same experience (obviously hardware speed will
have some effect on the experience, but the difference should be minimal).

### How we achieve this
- Cross platform libraries and standards.  Special thanks to the many
  projects we leverage, such as: C, Python, Qt, PyQt, libsndfile, numpy,
  scipy, paulstretch, rubberband, sbsms, mido, python-wavfile, msys2,
  pyinstaller and many others that make this project possible.  If I forgot
  to mention your project, please submit a PR to add it.
- First-class Linux support.  Linux is the first to support new CPU
  architectures, therefore we limit support for various technologies and
  standards to those that have first class Linux support.
- Copying audio files to the project folder.  Any new files added to the
  project are preserved, without the need for the same sample libraries in
  the same file location.
- A full suite of built-in plugins.  Any 3rd party plugin standard is going
  to be difficult to support across operating systems and CPU architectures,
  if the developers even support all of the platforms that Stargate supports.
  Even if well supported on all platforms, it is cumbersome to have all users
  install the exact same plugins.

## 5. Stability
You need your DAW to work reliably.  DAWs and plugins are notoriously buggy,
especially when combined.  It is simply not feasible to test a plugin against
every DAW ever made, or test a DAW against every plugin ever made.

Then there is stability over time.  You should not have to keep the same
computer around forever without ever updating it (while praying that the hard
drive does not die) just to ensure that you can load and edit your old
projects.

### How we achieve this
- Engine and plugins written in C.  See the above rationale.
- UI is a separate process from the engine, they cannot crash each other.
- Best in class testing and debugging capabilities. See the project
  documentation on Github for more information.
- Projects are completely portable between computers.  See the previous
  section about project portability.
- Minor releases will not break backwards compatility within that major
  release.  If we decide to implement a backwards-incompatible feature, it
  will happen in the next major release.
- Major releases are supported for as long as possible, until it is simply
  not feasible anymore.  Even after that, it should be possible to create
  a VM of an older Linux distro running Stargate for the purpose of loading
  old projects.  The project will consider providing pre-built images for VMs
  later.
- Major releases do not load projects from other major releases.  This avoids
  many bugs that come with trying to change the software over time while
  maintaining file compatibility.  Multiple major versions of Stargate can
  be installed on the same computer.

## 6. Capable of running on all CPU architectures, past, present and future
There should be close to zero effort on our part to make Stargate work on
new CPU architectures.  We want you to be able to run Stargate on x86, or
ARM, or RISC-V, or PowerPC, or the next big thing.  Keep in mind that we
may be limited by support from 3rd party libraries we use, such as Qt.

### How we achieve this
- Avoid Assembly language where possible, where not possible provide a
  cross-platform default using conditional compilation.
- First-class Linux support: The Linux kernel and GCC, Clang communities
  are quick to implement new CPU architectures, Linux distros follow soon
  thereafter.

## 7. Documentation, documentation, documentation
DAWs are complex software with steep learning curves.  Especially when a DAW
aims to throw out the existing rules and norms to do things differently.
We pledge to maintain high-quality, accurate, up-to-date documentation.
Please hold us accountable if you are unable to understand how to achieve
your desired goals using our workflow.  Conversely, be open to learning new
ways to do things, do not expect us to throw away our existing work to turn
Stargate into FL Studio because that is what you are used to.

### How we achieve this
- User manual.  We document the design of the various UI views and their
  workflows in
  [the Github docs folder](https://github.com/stargateaudio/stargate/docs)
- Youtube videos.  A picture is worth 1000 words, a video is about 30 pictures
  per second, so 30,000 words/second over a 10 minute Youtube video is
  18,000,000 words.  Clearly a lot easier than typing that many words in the
  user manual.

