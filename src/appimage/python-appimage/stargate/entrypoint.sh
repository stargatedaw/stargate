#! /bin/bash -i

PYVER=3.11

if [ -z "$LD_LIBRARY_PATH" ]; then
    export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib/x86_64-linux-gnu"
fi

export QT_QPA_PLATFORM_PLUGIN_PATH="${APPDIR}/opt/python${PYVER}/lib/python${PYVER}/site-packages/PyQt5/Qt5/plugins/platforms"

_USE_PYQT5=1 {{ python-executable }} \
	-u "${APPDIR}/opt/stargate/scripts/stargate" "$@"
