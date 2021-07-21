import os

if True:  # PyQt
    try:
        import PyQt5
        # default to PyQt5
        _PYQT6_ONLY = False
    except ImportError:
        import PyQt6
        # default to PyQt6 if available, and PyQt5 is not
        _PYQT6_ONLY = True
    if (
        _PYQT6_ONLY
        or
        "_USE_PYQT6" in os.environ
    ):
        def qt_event_pos(x):
            if hasattr(x, 'pos'):
                return x.pos()
            else:
                return x.position().toPoint()
        from PyQt6 import QtGui, QtWidgets, QtCore
        from PyQt6.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt6.QtGui import *
        from PyQt6.QtWidgets import *
    else:
        qt_event_pos = lambda x: x.pos()
        from PyQt5 import QtGui, QtWidgets, QtCore
        from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt5.QtGui import *
        from PyQt5.QtWidgets import *
else:  # PySide
    # Does not work yet, needs some porting and debugging
    from PySide6 import QtGui, QtWidgets, QtCore
    from PySide6.QtCore import Signal, Slot
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *

