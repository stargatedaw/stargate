from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.plugins import *
from sgui.sgqt import *

from . import _shared
from sglib.math import clip_min, clip_value
from sglib.lib import util
from sglib.lib.translate import _
from sglib.models import theme
from sgui.daw import shared

class SeqAtmItem(QGraphicsEllipseItem):
    """ This is an automation point within the ItemSequencer, these are only
        drawn when "Automation" mode is selected in SequencerWidget
    """
    def __init__(self, a_item, a_save_callback, a_min_y, a_max_y):
        QGraphicsEllipseItem.__init__(
            self,
            0,
            0,
            _shared.ATM_POINT_DIAMETER,
            _shared.ATM_POINT_DIAMETER,
        )
        self.setPen(shared.NO_PEN)
        self.save_callback = a_save_callback
        self.item = a_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(1100.0)
        self.set_brush()
        self.min_y = a_min_y
        self.max_y = a_max_y
        self.is_deleted = False

    def itemChange(self, a_change, a_value):
        if a_change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.set_brush()
        return QGraphicsItem.itemChange(self, a_change, a_value)

    def set_brush(self):
        if self.isSelected():
            self.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_atm_item_selected,
                ),
            )
        else:
            self.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_atm_item,
                ),
            )

    def _quantize(self, pos):
        pos = pos
        x = pos.x()
        if _shared.SEQ_QUANTIZE:
            x = round(
                x / _shared.SEQUENCER_QUANTIZE_PX
            ) * _shared.SEQUENCER_QUANTIZE_PX
        else:
            x = round(
                x / _shared.SEQUENCER_QUANTIZE_64TH
            ) * _shared.SEQUENCER_QUANTIZE_64TH
        x = clip_min(x, 0.0)
        y = clip_value(pos.y(), self.min_y, self.max_y)
        return x, y

    def quantize(self, pos):
        x, y = self._quantize(pos)
        if(
            self.pos().x() == x
            and
            self.pos().y() == y
        ):
            return
        shared.SEQUENCER.setUpdatesEnabled(False)
        self.setPos(x, y)
        delta_x = x - self.orig_x
        delta_y = y - self.orig_y
        for point in self._selected_points:
            new_x = clip_min(point.orig_x + delta_x, 0.0)
            new_y = clip_value(
                point.orig_y + delta_y,
                point.min_y,
                point.max_y,
            )
            point.setPos(new_x, new_y)
        shared.SEQUENCER.setUpdatesEnabled(True)
        shared.SEQUENCER.update()

    def mousePressEvent(self, a_event):
        if shared.EDITOR_MODE in (
            shared.EDITOR_MODE_SELECT,
            shared.EDITOR_MODE_DRAW,
        ):
            self.is_moving = True
            self._selected_points = [
                x for x in shared.SEQUENCER.get_selected_points()
                if x != self
            ]
            shared.SEQUENCER.remove_atm_path(self.item.index)
            #a_event.setAccepted(True)
            #QGraphicsEllipseItem.mousePressEvent(self, a_event)
            self.orig_x = self.pos().x()
            self.orig_y = self.pos().y()
            for point in self._selected_points:
                point.orig_x = point.pos().x()
                point.orig_y = point.pos().y()
            self.quantize(a_event.scenePos())
        elif shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            self.item.break_after = int(not self.item.break_after)
            self.set_point_value()
            self.save_callback()

    def mouseMoveEvent(self, a_event):
        if self.is_moving:
            #QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
            self.quantize(a_event.scenePos())

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        if self.is_moving:
            self.is_moving = False
            self.quantize(a_event.scenePos())
            self.set_point_value()
            for point in self._selected_points:
                point.set_point_value()
            self.save_callback()

    def set_point_value(self):
        f_pos = self.pos()
        f_point = self.item
        (track, beat, cc_val) = shared.SEQUENCER.get_item_coord(f_pos, a_clip=True)
        beat = clip_min(beat, 0.0)
        cc_val = clip_value(cc_val, 0.0, 127.0, True)
        f_point.beat, f_point.cc_val = (beat, cc_val)

    def __lt__(self, other):
        return self.pos().x() < other.pos().x()

