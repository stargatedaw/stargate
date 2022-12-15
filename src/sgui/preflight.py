"""
    Preflight checks
"""
import subprocess

from sgui.sgqt import QMessageBox
from sglib.hardware import rpi
from sglib.lib.translate import _
from sglib.lib.util import IS_MACOS
from sglib.log import LOG

__all__ = ['preflight']

RPI4_WARNING = """\
Detected a Raspberry Pi with suboptimal settings.  "
Please see https://github.com/stargatedaw/stargate/src/linux/rpi4.md
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
        LOG.info(f"Machine Arch: {platform.machine()}")
    except Exception as ex:
        LOG.warning(ex)

def preflight():
    _log_system_info()
    _preflight_rpi()
