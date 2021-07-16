from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sglib.lib.translate import _
from sgui.sgqt import *


class PianoKeyItem(QGraphicsRectItem):
    """ This is a piano key on the PianoRollEditor
    """
    def __init__(
        self,
        a_piano_width,
        a_note_height,
        a_parent,
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
        self.hover_brush = QColor(200, 200, 200)

    def hoverEnterEvent(self, a_event):
        QGraphicsRectItem.hoverEnterEvent(self, a_event)
        self.o_brush = self.brush()
        self.setBrush(self.hover_brush)
        QApplication.restoreOverrideCursor()

    def hoverLeaveEvent(self, a_event):
        QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        self.setBrush(self.o_brush)
