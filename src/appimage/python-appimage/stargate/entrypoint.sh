#! /bin/bash -i
{{ python-executable }} \
	-u "${APPDIR}/opt/stargate/scripts/stargate" "$@"
