"""
    Preflight checks
"""
from . import shared
from sglib.hardware import rpi
from sglib.lib.translate import _

__all__ = ['preflight']

def _preflight_rpi():
    if rpi.is_rpi():
        if not (
            rpi.gpu_mem()
            and
            rpi.desktop()
        ):
            QMessageBox.warning(
                shared.MAIN_WINDOW.widget,
                "Warning",
                _(
                    "Detected a Raspberry Pi with suboptimal settings.  "
                    "Please see: "
                    "https://github.com/stargateaudio/stargate/docs/"
                    "rpi.md"
                ),
            )

def preflight():
    _preflight_rpi()
