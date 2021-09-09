from sglib.log import LOG
import os


if True:  # PyQt
    try:
        import PyQt6
        # default to PyQt5
        _PYQT5_ONLY = False
    except ImportError:
        import PyQt5
        # default to PyQt6 if available, and PyQt5 is not
        _PYQT5_ONLY = True
    if (
        _PYQT5_ONLY
        or
        "_USE_PYQT5" in os.environ
    ):
        LOG.info("Using PyQt5")
        qt_event_pos = lambda x: x.pos()
        from PyQt5 import QtGui, QtWidgets, QtCore
        from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt5.QtGui import *
        from PyQt5.QtWidgets import *
        from PyQt5.QtSvg import QSvgRenderer
        # Not needed on Qt6, is the default behavior
        try:
            QGuiApplication.setAttribute(
                QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling,
            )
        except Exception as ex:
            LOG.warning(
                f"The platform you are using does not support Qt HiDpi: {ex}",
            )
    else:
        LOG.info("Using PyQt5")
        def qt_event_pos(x):
            if hasattr(x, 'pos'):
                return x.pos()
            else:
                return x.position().toPoint()
        from PyQt6 import QtGui, QtWidgets, QtCore
        from PyQt6.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt6.QtGui import *
        from PyQt6.QtWidgets import *
        from PyQt6.QtSvg import QSvgRenderer

    # Work around QMenu not taking the QApplication font, even if the QMenu
    # has a parent widget
    class _QMenu(QMenu):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Avoid circular dependency
            from sgui.util import get_font
            font = get_font()
            self.setFont(font.font)

        def addMenu(self, *args, **kwargs):
            menu = super().addMenu(*args, **kwargs)
            # Avoid circular dependency
            from sgui.util import get_font
            font = get_font()
            menu.setFont(font.font)
            return menu

    QMenu = _QMenu


else:  # PySide
    # Does not work yet, needs some porting and debugging
    from PySide6 import QtGui, QtWidgets, QtCore
    from PySide6.QtCore import Signal, Slot
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *
    from PySide6.QtSvg import QSvgRenderer

class _QSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class _QDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

QSpinBox = _QSpinBox
QDoubleSpinBox = _QDoubleSpinBox

