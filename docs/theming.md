# Theming
This document describes how to create custom color themes.

For documentation and examples of every parameter, see:
```
src/files/themes/default/
src/sglib/models/theme.py
```

# Opening, Copying Themes
Themes are controlled in the `Appearance` menu in the main menu (button on the
upper left).  There are actions to open a theme, revert to the default theme,
or copy the current theme to a new theme.

# Performance Considerations
Avoid the use of transparency and gradients to the greatest extent possible.
Transparent hex colors are prepended by an extra 2 digits, ie:
```
white: "#ffffff"
transparent_white: "#60ffffff"
```
Transparency requires more hardware power to render, and will not work well on
low power systems like Raspberry Pi. You can fake transparency by blending
colors together using `/scripts/color-hex-interpolate.py`.

Gradients are specified in QSS stylesheets, for example `qlineargradient(...)`,
`qradialgradient(...)`, `qconicalgradient(...)`.  See the
[Qt styleseet documentation](
	https://doc.qt.io/qt-5/stylesheet-reference.html
) and the existing [fancy theme](
	../src/files/themes/default/fancy.sgtheme
).

However, you can make an alternate version of the same theme that uses
transparency and gradients.  Every theme in the main repo should offer a
default version that works on 10 year old laptops and ARM single board
computers.   Add `fancy` to the name of any theme that uses transparency.
See the existing [fancy theme](
	../src/files/themes/default/fancy.sgtheme
).

# Font Considerations
Font scaling between different displays is very tricky.  As such, the strategy
of the project is to use the font size the user configured the operating system
to use.  Theme designers can change the font-family, but the font size should
not be changed directly by the theme.  Note that the user can override your
font choice in the application. If you want to change the size of a widget's
font relative to the system font size, you can do this:

```
{% if FONT_UNIT == 'pt' %}
font-size: {{ FONT_SIZE + 2 }}{{ FONT_UNIT }};
{% elif FONT_UNIT == 'px %}
font-size: {{ FONT_SIZE + 4 }}{{ FONT_UNIT }};
{% endif %}
```

# Structure
A theme is a folder containing the following structure:
```
theme/
  theme1.sgtheme
  theme2.sgtheme
  assets/
    image1.png
    image2.svg
    subdirectory/
      image456.svg
    ...
  system/
    system1.yaml
    ...
  templates/
    template1.qss
    ...
  vars/
    vars1.yaml
    ...
```
## Theme files
An `*.sgtheme` file references one each of template, variable and system colors
files.
```
# Looks in the templates/ folder
template: default.qss
variables:
  # Looks in the vars/ folder
  path: default.yaml
  # Optional variable key/values to override the contents of @path
  overrides:
    some_color: |-
      qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop: 0 #ffffff, stop: 1: #000000
      )
    some_other_color: "#012345"
system:
  # Looks in the system/ folder
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
