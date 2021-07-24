# Theming
This document describes how to create custom color themes.

This document may become out of date.  For the latest, see:
```
src/sglib/models/theme.py
src/files/themes/default/
```

# Performance Considerations
Avoid the use of transparency and gradients to the greatest extent possible.
Transparent hex colors are prepended by an extra 2 digits, ie:
```
white: #ffffff
transparent-white: #60ffffff
```
Transparency requires much more hardware power to render, and will not work
well on low power systems like Raspberry Pi. You can fake transparency by
blending colors together using `/scripts/color-hex-interpolate.py`.

Gradients are specified in QSS themes.

However, you can make an alternate version of the same theme that uses
transparency and gradients.  Every theme in the main repo should offer a
default version that works on 10 year old laptops and ARM single board
computers.   Add `fancy` to the name of any theme that uses transparency.

# Structure
A theme is a folder containing the following structure:
```
theme/
  theme1.yaml
  theme2.yaml
  assets/
    image1.png
    image2.svg
    ...
  system/
    system1.yaml
    ...
  templates/
    template1.qss
  vars/
    vars1.yaml
    ...
```
## Theme files
A theme file references one each of template, variable and system colors files.
```
# Looks in the templates/ folder
template: default.qss
# Looks in the vars/ folder
variables:
  path: default.yaml
  # Optional variable key/values to override the contents of @path
  overrides: {}
# Looks in the system/ folder
system:
  path: default.yaml
  overrides:
    daw: {}
    widgets: {}
```

## Template files
These are Qt QSS styles (similar to CSS), as Jinja2 templates.  One template
can be rendered into multiple different styles (for example, a light theme, a
dark theme, and an inbetween theme) by use of Jinja template variables and
variable files.  Note that there is a special variable that gets passed in
automatically: `ASSETS_DIR` provides a path to the assets folder.

## Variables files
These are a yaml dictionary of values to pass to a template.  This can include
simple data like hex colors, or larger chunks of data such as gradients or
entire elements.

## System files
These are the system colors defined in `src/sgui/theme.py`.  These are
implemented in the code, and cannot be styled using QSS.  However, the
QSS Jinja templates can reference this object as `SYSTEM_COLORS`.

Note that this file is also a Jinja template that is rendered with the
contents of the variables file, thus allowing the colors to be defined
in a single place for both QSS and non-QSS themed components.

# Debugging
Upon loading the theme, a copy of the fully rendered theme is saved to
`~/stargate/rendered_theme/`.  This copy of the theme cannot be edited
directly to change the appearance of Stargate, it is only for debugging
purposes.
