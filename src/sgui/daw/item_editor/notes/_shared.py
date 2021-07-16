from sgui.daw import shared
from sgui.daw.shared import *
from sgui.sgqt import *


PIANO_ROLL_DELETE_MODE = False
PIANO_ROLL_DELETED_NOTES = []
PIANO_ROLL_NOTE_LABELS = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
]
SELECTED_PIANO_NOTE = None   #Used for mouse click hackery
SELECTED_NOTE_GRADIENT = QLinearGradient(
    QtCore.QPointF(0, 0),
    QtCore.QPointF(0, 12),
)
SELECTED_NOTE_GRADIENT.setColorAt(0, QColor(180, 172, 100))
SELECTED_NOTE_GRADIENT.setColorAt(1, QColor(240, 240, 240))
PIANO_ROLL_HEADER_HEIGHT = 45


def piano_roll_set_delete_mode(a_enabled):
    if a_enabled:
        shared.PIANO_ROLL_EDITOR.setDragMode(QGraphicsView.DragMode.NoDrag)
        PIANO_ROLL_DELETED_NOTES = []
        PIANO_ROLL_DELETE_MODE = True
        QApplication.setOverrideCursor(
            QtCore.Qt.CursorShape.ForbiddenCursor,
        )
    else:
        shared.PIANO_ROLL_EDITOR.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag,
        )
        PIANO_ROLL_DELETE_MODE = False
        for f_item in PIANO_ROLL_DELETED_NOTES:
            f_item.delete()
        shared.PIANO_ROLL_EDITOR.selected_note_strings = []
        global_save_and_reload_items()
        QApplication.restoreOverrideCursor()

