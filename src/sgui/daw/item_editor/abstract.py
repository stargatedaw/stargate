from sglib.math import clip_value
from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui.daw.shared import *
from sglib.lib import util
from sglib.lib.util import *
from sglib.models import theme
from sgui.sgqt import *


class ItemEditorHeader(QGraphicsRectItem):
    """ The horizontal header at the top of an item editor.
        Inherits from QGraphicsRectItem so that
        AbstractItemEditor.get_item_at_pos() can find it
    """
    def __init__(self, *args, **kwargs):
        QGraphicsRectItem.__init__(self, *args, **kwargs)
        self.setBrush(
            QColor(
                theme.SYSTEM_COLORS.daw.seq_header,
            )
        )


class AbstractItemEditor(QGraphicsView, shared.HoverCursorChange):
    """ Base class for things on the "Items" tab.  Over time, more
        functionality should be absorbed into here and standardized
        across the different editors.
    """
    def __init__(self, a_cursor_offset=0.0):
        QGraphicsView.__init__(self)
        self.playback_cursor = None
        self.header = None
        self.cursor_offset = a_cursor_offset
        self.px_per_beat = None
        self.total_height = 2000

    def set_playback_pos(self, a_ignored=None):
        if not all((shared.CURRENT_ITEM_REF, self.playback_cursor)):
            return
        start = (
            shared.CURRENT_ITEM_REF.start_beat -
            shared.CURRENT_ITEM_REF.start_offset
        )
        length = (
            shared.CURRENT_ITEM_REF.length_beats +
            shared.CURRENT_ITEM_REF.start_offset
        )
        self.playback_pos = clip_value(
            shared.PLAYBACK_POS - start,
            0.0,
            length,
        )
        f_pos = (self.playback_pos * self.px_per_beat) + self.cursor_offset
        self.playback_cursor.setPos(f_pos, 0.0)

    def draw_header(self, a_header_width, a_header_height):
        self.header = ItemEditorHeader(
            0, 0, a_header_width, a_header_height)
        if not shared.CURRENT_ITEM_REF:
            return
        self.playback_cursor = self.scene.addLine(
            0.0,
            0.0,
            0.0,
            self.total_height,
            QPen(
                QColor(
                    theme.SYSTEM_COLORS.daw.playback_cursor,
                ),
                2.0,
            ),
        )
        self.playback_cursor.setZValue(1000.0)
        self.header.mousePressEvent = self.header_mousePressEvent
        self.set_playback_pos()

    def get_item_at_pos(self, a_pos, a_type):
        """
            @a_pos:  QPointF to enumerate items from in the QGraphicsScene
            @a_type: The type to look for
            @return: The item found, or None if not found
        """
        for f_item in self.scene.items(a_pos):
            if isinstance(f_item, a_type):
                return f_item
        return None

    def header_mousePressEvent(self, a_event):
        if not shared.CURRENT_ITEM_REF:
            return
        if (
            not glbl_shared.IS_PLAYING
            and
            a_event.button() != QtCore.Qt.MouseButton.RightButton
        ):
            f_beat = int((a_event.scenePos().x() - self.cursor_offset)
                / self.px_per_beat) + shared.CURRENT_ITEM_REF.start_beat - \
                shared.CURRENT_ITEM_REF.start_offset
            shared.global_set_playback_pos(f_beat if f_beat >= 0 else 0)

    def scroll_to_pos(self, pos, up=True):
        scene_pos = self.mapToScene(int(pos.x()), int(pos.y()))
        if up:
            x_pos = scene_pos.x() - (pos.x() * 0.5)
        else:
            x_pos = scene_pos.x() - (pos.x() * 1.5)
        self.horizontalScrollBar().setValue(int(x_pos))

    def wheelEvent(self, event):
        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            up = event.pixelDelta().y() > 0
            shared.ITEM_EDITOR.increment_hzoom(up)
            pos = event.position()
            self.scroll_to_pos(pos, up)
        else:
            QGraphicsView.wheelEvent(self, event)

