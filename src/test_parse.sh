#!/bin/sh -xe

# Test that various files can be parsed

for fname in $(find files/ -name '*.yaml' -or -name '*.sgtheme'); do
	yq . $fname 1>/dev/null
done

python -c 'from sgui import main'
python -c 'from sgui.widgets import *'
# sglib has unit tests, no need to check that it parses
