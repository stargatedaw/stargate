"""
    Preflight checks
"""
import subprocess

from sgui.sgqt import QMessageBox
from sglib.hardware import rpi
from sglib.lib.translate import _
from sglib.lib.util import IS_MAC_OSX
from sglib.log import LOG

__all__ = ['preflight']

RPI4_WARNING = """\
Detected a Raspberry Pi with suboptimal settings.  "
Please see https://github.com/stargatedaw/stargate/src/linux/rpi4.md
"""

MACOS_UDP_WARNING = """\
Detected that your UDP packet size limit is too low.  This will prevent some
features such as the spectrum analyzer from working.  Please run this command
from the terminal to set the UDP packet size to it's maximum limit:

    sudo sysctl -w net.inet.udp.maxdgram=65535
"""

def _preflight_rpi():
    try:
        if rpi.is_rpi():
            if not rpi.gpu_mem():
                QMessageBox.warning(
                    None,
                    "Warning",
                    _(RPI4_WARNING),
                )
    except Exception as ex:
        LOG.exception(ex)

def _log_system_info():
    try:
        import distro
        LOG.info(distro.info())
    except Exception as ex:
        LOG.warning(ex)
    try:
        import platform
        LOG.info(f"Python version: {platform.python_version()}")
        LOG.info(f"Platform: {platform.platform()}")
    except Exception as ex:
        LOG.warning(ex)

def preflight_macos_udp():
    if not IS_MAC_OSX:
        return
    try:
        output = subprocess.check_output(['sysctl', 'net.inet.udp.maxdgram'])
        output = output.decode('utf-8')
        size = int(output.split()[1])
        if size != 65535:
            QMessageBox.warning(
                None,
                "Warning",
                MACOS_UDP_WARNING,
            )
    except:
        LOG.exception('Failed to read MacOS net.inet.udp.maxdgram')

def preflight():
    preflight_macos_udp()
    _preflight_rpi()
    _log_system_info()
