from sglib.log import LOG
import os
import sys
import textwrap
import time
from typing import Optional


if True:  # PyQt
    try:
        import PyQt6
        # default to PyQt5
        _PYQT5_ONLY = False
    except ImportError:
        try:
            import PyQt5
        except ImportError:
            LOG.error(f"Unable to Find PyQt5 or PyQt6 in {sys.path}")
            sys.exit(1)
        # default to PyQt6 if available, and PyQt5 is not
        _PYQT5_ONLY = True
    if (
        _PYQT5_ONLY
        or
        "_USE_PYQT5" in os.environ
    ):
        LOG.info("Using PyQt5")
        try:
            from PyQt5 import __path__ as mod_path
            LOG.info(mod_path)
        except:
            pass
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
        LOG.info("Using PyQt6")
        if getattr(PyQt6, '__path__', None):
            LOG.info(PyQt6.__path__)
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

HINT_CACHE = {}
HINT_BOX_STACK = []
HINT_BOX = None

def create_hintbox():
    global HINT_BOX
    HINT_BOX = QLabel()
    HINT_BOX.setAlignment(
        QtCore.Qt.AlignmentFlag.AlignTop
        |
        QtCore.Qt.AlignmentFlag.AlignLeft
    )
    HINT_BOX.setObjectName('hintbox')
    HINT_BOX.setToolTip(
        'The hint box, provides information about almost anything '
        'you hover the mouse over.  To hide the hint box, click the '
        '"Hide Hint Box" action in the main menu on the upper left'
    )


class _HintBox:
    """ Converts tooltips to hint box hints using the standard Qt
        setToolTip() method
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tooltip = None

    def setToolTip(
        self,
        text: Optional[str],
        reformat: bool=True,
    ):
        if text is None:
            self._tooltip = None
            return
        if reformat:
            cached = HINT_CACHE.get(text, None)
            if cached is not None:
                self._tooltip = cached
                return
            lines = textwrap.wrap(text)
            if len(lines) > 3:
                lines[2] = lines[2][:-3] + '...'
                LOG.error(f'Truncating hint {lines[0]}')
            self._tooltip = "\n".join(lines[:3])
            HINT_CACHE[text] = self._tooltip
        else:
            self._tooltip = text

    def _clear_hint_box(self, _all=False):
        # Maintain a stack of messages, only clear the text if there are none
        if _all:
            HINT_BOX_STACK.clear()
            HINT_BOX.setText('')
        else:
            if HINT_BOX_STACK:
                HINT_BOX_STACK.pop()
            if HINT_BOX_STACK:  # still
                msg = HINT_BOX_STACK[-1]
                HINT_BOX.setText(msg)
            else:
                HINT_BOX.setText('')

    def _set_hint_box(self, msg: str, clear=False):
        if HINT_BOX:
            HINT_BOX.setText(msg)
            if clear:
                HINT_BOX_STACK.clear()
            elif msg in HINT_BOX_STACK:
                HINT_BOX_STACK.remove(msg)
            HINT_BOX_STACK.append(msg)

class _HintWidget(_HintBox):
    def event(self, event):
        if self._tooltip:
            if event.type() in (
                QtCore.QEvent.Type.StatusTip,
            ):
                self._set_hint_box(self._tooltip, clear=True)
            elif event.type() in (
                QtCore.QEvent.Type.HoverEnter,
                QtCore.QEvent.Type.Enter,
            ):
                self._set_hint_box(self._tooltip)
            elif event.type() in (
                QtCore.QEvent.Type.HoverLeave,
                QtCore.QEvent.Type.Leave,
            ):
                self._clear_hint_box()
        return super().event(event)

class _HintItem(_HintBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        if self._tooltip:
            self._set_hint_box(self._tooltip)
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self._tooltip:
            self._clear_hint_box()
        return super().hoverLeaveEvent(event)

orig_QLineEdit = QLineEdit

class _QLineEdit(_HintWidget, QLineEdit):
    def event(self, ev):
        if ev.type() == QtCore.QEvent.Type.KeyPress:
            if ev.key() in(
                QtCore.Qt.Key.Key_Enter,
                QtCore.Qt.Key.Key_Return,
            ):
                self.focusNextChild()
                return True
        return super().event(ev)

origQComboBox = QComboBox

class _QComboBox(_HintWidget, QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def wheelEvent(self, event):
        event.ignore()

class SgSpinBox(_QLineEdit):
    """
    Tries to mimic behavior from Maya's internal slider that's found in the channel box.
    """
    TYPE_INT = 0
    TYPE_DOUBLE = 1

    def __init__(self, spinbox_type, *args, **kwargs):
        self.spinbox_type = spinbox_type
        super(SgSpinBox, self).__init__(*args, **kwargs)

        if spinbox_type == SgSpinBox.TYPE_INT:
            self.setValidator(QtGui.QIntValidator(parent=self))
        elif spinbox_type == SgSpinBox.TYPE_DOUBLE:
            self.setValidator(QtGui.QDoubleValidator(parent=self))
        else:
            assert False, spinbox_type
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum,
        )
        self.setFixedSize(36, 24)

        self.min = None
        self.max = None
        self.step_size = 1
        self.decimals = 0
        self.value_at_press = None
        self.pos_at_press = None
        self.setValue(0)

    def _str_to_value(self, _str):
        if self.spinbox_type == self.TYPE_DOUBLE:
            value = float(_str)
        elif self.spinbox_type == self.TYPE_INT:
            value = int(_str)
        if self.max is not None and value > self.max:
            value = self.max
            self.setValue(self.max)
        elif self.min is not None and value < self.min:
            value = self.min
            self.setValue(self.min)
        assert not isinstance(value, str), value
        return value

    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.value_at_press = self.value()
            self.pos_at_press = event.pos()
            self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.SizeVerCursor))
        else:
            super(SgSpinBox, self).mousePressEvent(event)
            self.selectAll()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.value_at_press = None
            self.pos_at_press = None
            self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.IBeamCursor))
            return
        super(SgSpinBox, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() != QtCore.Qt.MouseButton.LeftButton:
            return

        if self.pos_at_press is None:
            return

        steps_mult = self.getStepsMultiplier(event)

        delta = self.pos_at_press.y() - event.pos().y()
        # Make movement less sensitive.
        if event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
            delta /= 6
        else:
            delta /= 3

        delta *= self.step_size * steps_mult
        value = self.value_at_press + delta

        if self.spinbox_type == SgSpinBox.TYPE_DOUBLE:
            value = round(value, self.decimals)
        self.setValue(value)

        super(SgSpinBox, self).mouseMoveEvent(event)

    def getStepsMultiplier(self, event):
        steps_mult = 1

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            steps_mult = 10
        elif event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
            steps_mult = 0.1

        return steps_mult

    def setMinimum(self, value):
        self.min = value

    def setMaximum(self, value):
        self.max = value

    def minimum(self):
        return self.min

    def maximum(self):
        return self.max

    def setRange(self, _min, _max):
        self.min = _min
        self.max = _max
        self.setValue(self.value())

    def setSingleStep(self, step_size):
        if self.spinbox_type == SgSpinBox.TYPE_INT:
            self.step_size = step_size
        else:
            self.step_size = step_size

    def value(self):
        text = self.text()
        if text == '':
            text = str(self.min)
            self.setText(text)
        if self.spinbox_type == SgSpinBox.TYPE_INT:
            return int(text)
        else:
            return float(text)

    def setValue(self, value):
        if self.min is not None:
            value = max(value, self.min)

        if self.max is not None:
            value = min(value, self.max)

        if self.spinbox_type == SgSpinBox.TYPE_INT:
            self.setText(str(int(value)))
        else:
            self.setText(str(float(value)))

    def event(self, ev):
        if ev.type() == QtCore.QEvent.Type.KeyPress:
            if ev.key() in(
                QtCore.Qt.Key.Key_Enter,
                QtCore.Qt.Key.Key_Return,
            ):
                self.focusNextChild()
                return True
            elif ev.key() == QtCore.Qt.Key.Key_Up:
                value = self.value() + self.step_size
                if hasattr(self, 'decimals'):
                    value = round(value, self.decimals)
                self.setValue(value)
                return True
            elif ev.key() == QtCore.Qt.Key.Key_Down:
                value = self.value() - self.step_size
                if hasattr(self, 'decimals'):
                    value = round(value, self.decimals)
                self.setValue(value)
                return True
        return super().event(ev)

class _QDoubleSpinBox(SgSpinBox):
    valueChanged = Signal(float)

    def __init__(self, *args, **kwargs):
        SgSpinBox.__init__(
            self,
            SgSpinBox.TYPE_DOUBLE,
            *args,
            **kwargs
        )
        self.editingFinished.connect(self._editingFinished)

    def _editingFinished(self):
        value = str(self.text())
        if value == '':
            value = str(self.min)
            self.setText(value)
        value = self._str_to_value(value)
        self.valueChanged.emit(value)

    def setDecimals(self, decimals):
        self.decimals = decimals


class _QSpinBox(SgSpinBox):
    valueChanged = Signal(int)

    def __init__(self, *args, **kwargs):
        SgSpinBox.__init__(
            self,
            SgSpinBox.TYPE_INT,
            *args,
            **kwargs
        )
        self.editingFinished.connect(self._editingFinished)

    def _editingFinished(self):
        value = self._str_to_value(str(self.text()))
        self.valueChanged.emit(value)

DIALOG_SHOWING = None

class QDialog(QDialog):
    def _center(self):
        parent = self.parentWidget()
        geometry = parent.geometry()
        self.move(
            int(geometry.center().x() - (self.width() / 2) - geometry.left()),
            int(geometry.center().y() - (self.height() / 2) - geometry.top()),
        )

    def closeEvent(self, event):
        global DIALOG_SHOWING
        DIALOG_SHOWING = None
        widget = self.parentWidget().currentWidget()
        widget.setEnabled(True)
        self._waiting = False
        super().closeEvent(event)

    def _end_wait(self):
        self._waiting = False

    def exec(self, block=True, center=True):
        global DIALOG_SHOWING
        DIALOG_SHOWING = self
        # Avoid circular dependency
        from sgui import shared
        parent = shared.MAIN_STACKED_WIDGET
        self.setParent(parent)
        #self.setModal(True)
        current_widget = parent.currentWidget()
        current_widget.setDisabled(True)
        self.setMinimumHeight(
            int(current_widget.height() * 0.2),
        )
        self.setMinimumWidth(
            int(current_widget.width() * 0.2),
        )
        self.adjustSize()
        if center:
            self._center()

        self.show()

        if block:
            self._waiting = True
            self.destroyed.connect(self._end_wait)
            wait = 1. / 60.
            while self._waiting:
                time.sleep(wait)
                QApplication.processEvents()

orig_QMessageBox = QMessageBox

class _QMessageBox:
    StandardButton = orig_QMessageBox.StandardButton

    @staticmethod
    def question(
        parent,
        title,
        message,
        buttons,
        default=None,
        callbacks=None,
    ):
        answer = []
        def close(_answer):
            if callbacks:
                if _answer in callbacks:
                    callbacks[_answer]()
            else:
               answer.append(_answer)
            dialog.close()
        def add_button(_enum):
            # Needs to be a separate function so that the value of
            # _enum is in the stack frame
            button = QPushButton(_enum.name)
            button.pressed.connect(lambda: close(_enum))
            buttons_layout.addWidget(button)
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        #layout.addWidget(QLabel(title))
        layout.addWidget(QLabel(message))
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        for _enum in QMessageBox.StandardButton:
            if _enum not in (
                QMessageBox.StandardButton.ButtonMask,
                QMessageBox.StandardButton.FlagMask,
            ) and buttons & _enum.value:
                add_button(_enum)
        dialog.exec(block=not callbacks)
        if not callbacks:
            answer = answer.pop()
            return answer

    @staticmethod
    def warning(parent, title, message):
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(title))
        layout.addWidget(QLabel(message))
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        button = QPushButton("OK")
        button.pressed.connect(dialog.close)
        buttons_layout.addWidget(button)
        dialog.exec()

QComboBox = _QComboBox
QDoubleSpinBox = _QDoubleSpinBox
QLineEdit = _QLineEdit
QSpinBox = _QSpinBox
QMessageBox = _QMessageBox

class QPushButton(_HintWidget, QPushButton):
    pass

class QGraphicsView(_HintWidget, QGraphicsView):
    pass

class QDial(_HintWidget, QDial):
    pass

class QSlider(_HintWidget, QSlider):
    pass

class QCheckBox(_HintWidget, QCheckBox):
    pass

class QRadioButton(_HintWidget, QRadioButton):
    pass

class QListWidget(_HintWidget, QListWidget):
    pass

class QTextEdit(_HintWidget, QTextEdit):
    pass

class QTreeWidget(_HintWidget, QTreeWidget):
    pass

class QLabel(_HintWidget, QLabel):
    pass

class QAction(_HintBox, QAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tooltip = None
        self.activate(QAction.ActionEvent.Trigger)
        self.activate(QAction.ActionEvent.Hover)
        self.hovered.connect(
            lambda: self._set_hint_box(self._tooltip, clear=True)
        )
        self.triggered.connect(
            lambda x: self._clear_hint_box(_all=True)
        )
class QLCDNumber(_HintWidget, QLCDNumber):
    pass

# These caused unknown theming problems.
# TODO: Try QGroupBox, it may have only been QWidget
#class QGroupBox(_HintWidget, QGroupBox):
#    pass

#class QWidget(_HintWidget, QWidget):
#    pass

class QGraphicsRectItem(_HintItem, QGraphicsRectItem):
    def paint(
        self,
        painter,
        option,
        arg4=None,
    ):
        """ Override to avoid the dotted line around selected items
        """
        option.state &= ~QStyle.StateFlag.State_Selected
        QtWidgets.QGraphicsRectItem.paint(self, painter, option)

class QGraphicsEllipseItem(_HintItem, QGraphicsEllipseItem):
    pass

