#! /bin/bash -i

if [ -z "$LD_LIBRARY_PATH" ]; then
    export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib/x86_64-linux-gnu"
fi

{{ python-executable }} \
	-u "${APPDIR}/opt/stargate/scripts/stargate" "$@"
