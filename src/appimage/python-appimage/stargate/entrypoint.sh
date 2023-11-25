#! /bin/bash -i

PYVER=3.11

if [ -z "$LD_LIBRARY_PATH" ]; then
    export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib/x86_64-linux-gnu"
fi

export QT_QPA_PLATFORM_PLUGIN_PATH="${APPDIR}/opt/python${PYVER}/lib/python${PYVER}/site-packages/PyQt5/Qt5/plugins/platforms"

export QT_DEBUG_PLUGINS=1

# exporting the DISPLAY fixes Qt errors regarding the xcb platform plugin
if [ -e "$(which xrandr)" ]; then
        export DISPLAY=":$(xrandr --current | grep -Eo 'Screen [0-9]+:' | grep -Eo '[0-9]+')"
elif [ -e /tmp/.X11-unix ]; then
        export DISPLAY=$(ls /tmp/.X11-unix | tr 'X' ':' | head -n 1)
fi


{{ python-executable }} -s \
	-u "${APPDIR}/opt/stargate/scripts/stargate" "$@"
