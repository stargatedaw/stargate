from sglib import constants
from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui.sgqt import QGraphicsRectItem, QApplication, QColor


class PianoKeyItem(QGraphicsRectItem):
    """ This is a piano key on the PianoRollEditor
    """
    def __init__(
        self,
        a_piano_width,
        a_note_height,
        a_parent,
        note,
    ):
        QGraphicsRectItem.__init__(
            self,
            0,
            0,
            a_piano_width,
            a_note_height,
            a_parent,
        )
        self.setAcceptHoverEvents(True)
        self.hover_brush = QColor(120, 120, 120)
        self.note = note

    def hoverEnterEvent(self, a_event):
        super().hoverEnterEvent(a_event)
        self.o_brush = self.brush()
        self.setBrush(self.hover_brush)
        QApplication.restoreOverrideCursor()

    def hoverLeaveEvent(self, a_event):
        super().hoverLeaveEvent(a_event)
        self.setBrush(self.o_brush)

    def mousePressEvent(self, ev):
        if (
            shared.CURRENT_ITEM_TRACK is None
            or
            glbl_shared.IS_PLAYING
            or
            glbl_shared.IS_RECORDING
        ):
            return
        self.channel = shared.ITEM_EDITOR.get_midi_channel()
        self.rack = shared.CURRENT_ITEM_TRACK
        constants.DAW_IPC.note_on(self.rack, self.note, self.channel)

    def mouseReleaseEvent(self, ev):
        if (
            shared.CURRENT_ITEM_TRACK is None
            or
            glbl_shared.IS_PLAYING
            or
            glbl_shared.IS_RECORDING
        ):
            return
        constants.DAW_IPC.note_off(self.rack, self.note, self.channel)

