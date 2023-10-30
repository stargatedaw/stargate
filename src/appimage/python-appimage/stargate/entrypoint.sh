#! /bin/bash -i

if [ -z "$LD_LIBRARY_PATH" ]; then
    export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib/x86_64-linux-gnu"
fi

export QT_QPA_PLATFORM_PLUGIN_PATH="${APPDIR}/opt/python3.10/lib/python3.10/site-packages/PyQt5/Qt5/plugins/platforms"

{{ python-executable }} \
	-u "${APPDIR}/opt/stargate/scripts/stargate" "$@"
