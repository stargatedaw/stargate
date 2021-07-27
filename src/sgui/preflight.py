"""
    Preflight checks
"""
from sgui.sgqt import QMessageBox
from sglib.hardware import rpi
from sglib.lib.translate import _

__all__ = ['preflight']

RPI4_WARNING = """\
Detected a Raspberry Pi with suboptimal settings.  "
Please see <a href="https://github.com/stargateaudio/stargate/docs/rpi.md">
the rpi4 documentation</a>
"""

def _preflight_rpi():
    if rpi.is_rpi():
        if not (
            rpi.gpu_mem()
            and
            rpi.desktop()
        ):
            QMessageBox.warning(
                None,
                "Warning",
                _(RPI4_WARNING),
            )

def preflight():
    _preflight_rpi()
