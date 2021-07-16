import os

if True:
    if "_USE_PYQT6" in os.environ:
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
else:
    # Does not work yet, needs some porting and debugging
    from PySide6 import QtGui, QtWidgets, QtCore
    from PySide6.QtCore import Signal, Slot
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *

