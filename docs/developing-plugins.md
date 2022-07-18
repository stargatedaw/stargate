# Work in Progress
This document, and the plugin API, are a work in progress.  They are completely
usable now, but future efforts are planned to standardize and streamline
the plugin development process.

# Developing Plugins
This document provides a basic overview of how to develop instrument and
effects plugins.  It is not comprehensive API documentation.

# BEFORE YOU START
The project wants to curate the selection of plugins available on the platform.
The project is eager to accept 3rd party plugin contributions, and willing to
work with developers as much as needed.  However, it is important to ensure
quality and long term project vision that prospective plugins are designed
and discussed thoroughly before implementing.  Especially because plugins
are expected to maintain backwards compatibility forever, and the project
does not want to maintain 10 different versions of the same plugin with only
minor differences.

Before coding any plugin, please create an issue in the Github issue tracker
and tag it with `new_plugin_proposal`.

Use this format:
```
# Description
Describe the new plugin, the problem it is solving, and why it cannot be
adequately solved by existing plugins.

# Use Case
Describe how this will be used to make music, and the intended audience.

# UI
Discuss the UI in detail, a mock-up of the proposed UI would be excellent.

# Engine
Discuss how the DSP code will be implemented.  Will it require libraries that
stargate-engine does not already depend on?

# Resource Consumption
Will the UI involve complex 2d or 3d rendering?  Would CPU usage be considered
low, medium, or high?  Can we expect this plugin to function on low end
hardware like rpi4 or a 10 year old laptop?
```

Expect lively discussion and many questions.  After the plugin has been
approved, you can begin coding it.

# Language
Python3/PyQt are the only choice for UI programming.  However, if you can
make a good case for something else that can be perfectly integrated with
PyQt, feel free to discuss it.

GNU89 C is the only choice for engine programming.  Why not C++?  Because well
written and optimized C is a much more performant and stable choice.  Why not
C11?  Because libc and compiler support still are not ready for serious use.

# Coding Basics
Use the existing libraries in `src/sgui/widgets/` and
`src/engine/{src,include}/audiodsp/`, these libraries make it easy to create
new plugins by re-using existing, well-tested widgets and DSP routines.  If you
need to create new widgets or DSP routines, create them in the libraries for
re-use in other plugins.  For DSP routines, write unit tests that touch every
line to ensure that there are not memory errors.  You can modify existing
widgets and DSP routines only if the changes to not break backwards
compatibility.

## Backwards Compatibility
Backwards compatibility must be maintained within the same MAJOR release
(stargate, stargate2, stargate3).  Major releases may break compatibility
as needed, as stargate3 is not expected to open stargate2 projects, etc...

- You must not break compatibility with existing project file formats.  In
  some cases you may be able to add things to the format without breaking
  compatibility.  Any hacks you add to the code to check for the optional
  thing should include a code comment of `TODO: Remove at next major version`.
- Existing projects must not sound different after your code change, unless
  the change is universally an improvement, for example, removing pops and
  clicks caused by a bug.

# UI
- The plugin UIs are defined in `src/sgui/plugins/`.  See existing plugins for
  examples.
- To the greatest extent possible, the plugins should make use of
  the widget library in `src/sgui/widgets/`.  If a new widget is created that
  can potentially be re-used in other plugins, it should be created in the
  widget library and imported into the plugin.  The component should be made
  generic and reusable to the greatest extent possible.
- UIs should use the UI theme capabilities in `src/sglib/models/theme.py`
  to choose colors, either by QSS (Calling setObjectName() on the appropriate
  widgets), or using `SYSTEM_COLORS` if manually drawing 2d or 3d components.
- Optional functionalities (currently only getting the wav\_pool uids of a
  plugin such as a sampler) may require creating a plugin model in
  `src/sglib/models/plugins/`.
- Plugins must go into the plugin rack, and must not generate pop up windows.
  Exceptions may be granted to this rule with proper justification.

# Engine
- Plugins should not generate their own worker threads.  The current desire is
  to keep the existing setup and require a plugin to run on a single CPU core.
  If somebody can justify a plugin that requires multiple concurrent threads,
  there will need to be big changes to the threading model to make this work
  efficiently.
- It is very important that you use the `src/engine/{include,src}/audiodsp`
  library to the greatest extent possible, and add new DSP routines to the
  library.
- Your plugin must pass unit tests and have zero memory errors in Valgrind.
  This will ensure that Stargate is stable, reliable software.
