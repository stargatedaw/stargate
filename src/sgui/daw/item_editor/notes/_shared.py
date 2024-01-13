from sgui.daw import shared
from sgui.daw.shared import *
from sgui.sgqt import *


PARAMETER = 0  # 0: velocity, 1: pan, 2:A, 3:D, 4:S, 5:R, 6:pitch_fine

PIANO_ROLL_DELETE_MODE = False
PIANO_ROLL_DELETED_NOTES = []
PIANO_ROLL_NOTE_LABELS = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
]
SELECTED_PIANO_NOTE = None   #Used for mouse click hackery
PIANO_ROLL_HEADER_HEIGHT = 45


def piano_roll_set_delete_mode(a_enabled):
    global PIANO_ROLL_DELETE_MODE
    if a_enabled:
        shared.PIANO_ROLL_EDITOR.setDragMode(QGraphicsView.DragMode.NoDrag)
        PIANO_ROLL_DELETED_NOTES.clear()
        PIANO_ROLL_DELETE_MODE = True
    else:
        shared.PIANO_ROLL_EDITOR.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag,
        )
        PIANO_ROLL_DELETE_MODE = False
        for f_item in PIANO_ROLL_DELETED_NOTES:
            f_item.delete()
        shared.PIANO_ROLL_EDITOR.selected_note_strings = []
        global_save_and_reload_items()

