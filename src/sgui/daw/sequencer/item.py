from .  import _shared
from sglib.math import (
    clip_max,
    clip_min,
    clip_value,
)
from sglib import constants
from sgui import shared as glbl_shared
from sgui.daw import painter_path, shared
from sglib.log import LOG
from sglib.models.daw import *
from sglib.models import theme
from sgui.daw.shared import *
from sgui.daw import strings as daw_strings
from sglib.lib import util
from sglib.lib.util import *
from sglib.lib.translate import _
from sgui.sgqt import *
from sgui.util import get_font


class SequencerItemHandle(QGraphicsPolygonItem):
    def __init__(self, _polygon, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setZValue(2200.0)
        self.setAcceptHoverEvents(True)
        self.setPolygon(_polygon)

    def hoverEnterEvent(self, event):
        if not glbl_shared.IS_PLAYING and shared._is_move_cursor():
            QApplication.setOverrideCursor(
                QtCore.Qt.CursorShape.SizeHorCursor,
            )
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not glbl_shared.IS_PLAYING and shared._is_move_cursor():
            QApplication.restoreOverrideCursor()
        super().hoverLeaveEvent(event)


class SequencerItem(QGraphicsRectItem):
    """ This is an individual sequencer item within the ItemSequencer
    """
    def __init__(self, a_name, a_audio_item, draw_handle):
        QGraphicsRectItem.__init__(self)
        self.name = str(a_name)
        self.is_deleted = False
        self.draw_handle = draw_handle

        if _shared.SEQUENCE_EDITOR_MODE == 0:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges,
            )
            #self.setFlag(QGraphicsItem.ItemDoesntPropagateOpacityToChildren)
        else:
            self.setEnabled(False)
            #self.setOpacity(0.2)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)

        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_audio_item.track_num

        self.pixmap_items = []
        self.should_draw = (
            _shared.DRAW_SEQUENCER_GRAPHS
            or
            a_audio_item.length_beats > _shared.CACHED_SEQ_LEN * 0.02
        )

        if self.should_draw:
            f_pixmaps = painter_path.get_item_path(
                a_audio_item.item_uid,
                _shared.SEQUENCER_PX_PER_BEAT,
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT - 20,
                shared.CURRENT_SEQUENCE.get_tempo_at_pos(
                    a_audio_item.start_beat,
                ),
            )
            for f_pixmap in f_pixmaps:
                f_pixmap_item = QGraphicsPixmapItem(f_pixmap, self)
                f_pixmap_item.setCacheMode(
                    QGraphicsItem.CacheMode.ItemCoordinateCache,
                )
                f_pixmap_item.setZValue(1900.0)
                self.pixmap_items.append(f_pixmap_item)

        self.label_bg = QGraphicsRectItem(parent=self)
        self.label_bg.setPen(shared.NO_PEN)
        self.label_bg.setPos(1.0, 1.0)
        self.label_bg.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )
        self.label_bg.setZValue(2050.00)

        self.label = get_font().QGraphicsSimpleTextItem(
            str(a_name),
            parent=self,
        )
        self.label.setPen(shared.NO_PEN)
        self.label.setBrush(
            QColor(
                theme.SYSTEM_COLORS.daw.seq_item_text,
            ),
        )

        self.label.setPos(1.0, 1.0)
        self.label.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )
        self.label.setZValue(2100.00)

        self.start_handle = SequencerItemHandle(
            _polygon=shared.BOTTOM_LEFT_TRI,
            parent=self,
        )
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            0.0,
            (
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle,
        )

        self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

        self.length_handle = SequencerItemHandle(
            _polygon=shared.BOTTOM_RIGHT_TRI,
            parent=self,
        )
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle,
        )

        self.stretch_handle = SequencerItemHandle(
            _polygon=shared.BOTTOM_RIGHT_TRI,
            parent=self,
        )
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5
            ) - (shared.SEQUENCE_EDITOR_TRACK_HEIGHT * 0.5),
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT * 0.5
            ) + (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle,
        )
        self.stretch_handle.hide()
        if not self.draw_handle:
            self.start_handle.hide()
            self.length_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT,
            self,
        )
        self.split_line.hide()
        self.split_line.mapFromParent(0.0, 0.0)
        self.split_line.setZValue(3000)
        self.split_line_is_shown = False

        self.setAcceptHoverEvents(True)

        self.is_start_resizing = False
        self.is_resizing = False
        self.is_copying = False
        self.is_fading_in = False
        self.is_fading_out = False
        self.is_stretching = False
        self.set_brush()
        self.waveforms_scaled = False
        self.event_pos_orig = None
        self.width_orig = None
        self.quantize_offset = 0.0
        self.draw()
        self.set_tooltips()

    def itemChange(self, a_change, a_value):
        if a_change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.set_brush()
        return QGraphicsItem.itemChange(self, a_change, a_value)

    def get_selected_string(self):
        return str(self.audio_item)

    def mouseDoubleClickEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        global_open_items(
            self.name,
            a_reset_scrollbar=True,
            a_new_ref=self.audio_item,
            item_track=self.track_num,
        )
        editors = (
            shared.CURRENT_ITEM.items,
            shared.CURRENT_ITEM.notes,
            shared.CURRENT_ITEM.ccs,
            shared.CURRENT_ITEM.pitchbends,
        )
        current_index = shared.ITEM_EDITOR.tab_widget.currentIndex()
        if current_index < len(editors) and not editors[current_index]:
            for i in range(len(editors)):
                if editors[i]:
                    current_index = i
                    shared.ITEM_EDITOR.tab_widget.setCurrentIndex(
                        current_index,
                    )
                    break
        shared.MAIN_WINDOW.setCurrentIndex(shared.TAB_ITEM_EDITOR)
        #Ensure that notes are visible
        if (
            current_index == 1
            and
            shared.PIANO_ROLL_EDITOR.note_items
        ):
            height = shared.PIANO_ROLL_EDITOR.geometry().height()
            average = sum(
                x.pos().y()
                for x in shared.PIANO_ROLL_EDITOR.note_items
            ) / len(shared.PIANO_ROLL_EDITOR.note_items)
            val = int(average - (height * 0.5))
            shared.PIANO_ROLL_EDITOR.verticalScrollBar().setValue(val)

    def draw(self):
        f_start = self.audio_item.start_beat * _shared.SEQUENCER_PX_PER_BEAT
        f_length = (
            self.audio_item.length_beats * _shared.SEQUENCER_PX_PER_BEAT
        )

        self.length_orig = f_length
        self.length_px_start = (
            self.audio_item.start_offset * _shared.SEQUENCER_PX_PER_BEAT
        )
        self.length_px_minus_start = f_length - self.length_px_start

        self.rect_orig = QtCore.QRectF(
            0.0,
            0.0,
            float(f_length),
            float(shared.SEQUENCE_EDITOR_TRACK_HEIGHT),
        )
        self.setRect(self.rect_orig)

        label_rect = QtCore.QRectF(0.0, 0.0, float(f_length), 20.)
        self.label_bg.setRect(label_rect)
        if f_length < 20:
            self.label.hide()

        f_track_num = _shared.SEQUENCE_EDITOR_HEADER_HEIGHT + (
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT * self.audio_item.track_num
        )

        self.setPos(f_start, f_track_num)
        self.is_moving = False
#        if self.audio_item.time_stretch_mode >= 3 or \
#        (self.audio_item.time_stretch_mode == 2 and \
#        (self.audio_item.timestretch_amt_end ==
#        self.audio_item.timestretch_amt)):
#            self.stretch_width_default = \
#                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = -self.length_px_start

        if self.should_draw:
            f_offset = 0
            for f_pixmap_item in self.pixmap_items:
                f_pixmap_item.setPos(
                    f_offset + self.sample_start_offset_px,
                    20.0,
                )
                f_offset += f_pixmap_item.pixmap().width()

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = self.start_handle_scene_min + f_length

        self.length_handle.setPos(
            f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT
                -
                shared.AUDIO_ITEM_HANDLE_HEIGHT
            ),
        )
        self.start_handle.setPos(
            0.0,
            (
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT
                -
                shared.AUDIO_ITEM_HANDLE_HEIGHT
            )
        )
#        if self.audio_item.time_stretch_mode >= 2 and \
#        (((self.audio_item.time_stretch_mode != 5) and \
#        (self.audio_item.time_stretch_mode != 2)) \
#        or (self.audio_item.timestretch_amt_end ==
#        self.audio_item.timestretch_amt)):
#            self.stretch_handle.show()
#            self.stretch_handle.setPos(
#                f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
#                (shared.SEQUENCE_EDITOR_TRACK_HEIGHT * 0.5) - \
#                (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5))

    def set_tooltips(self):
        self.setToolTip(daw_strings.sequencer_item)
        self.start_handle.setToolTip(
            "Use this handle to resize the item by changing the start point.  "
            "You cannot make an item longer by dragging the start handle, "
            "only move the start to the middle of the item."
        )
        self.length_handle.setToolTip(
            "Use this handle to resize the item by changing the end point.  "
            'To edit an item after increasing the length, double click to '
            'open in the item editor again'
        )
        self.stretch_handle.setToolTip(
            "Use this handle to resize the item by time-stretching it."
        )

    def clip_at_sequence_end(self):
        f_current_sequence_length = get_current_sequence_length()
        f_max_x = f_current_sequence_length * _shared.SEQUENCER_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(
                0.0,
                0.0,
                float(f_end_px),
                float(shared.SEQUENCE_EDITOR_TRACK_HEIGHT),
            )
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_orig) * 1000.0
            self.audio_item.sample_end = clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None, override=False):
        if theme.SYSTEM_COLORS.daw.seq_item_background_use_track_color:
            if self.isSelected() or override:
                brush = theme.SYSTEM_COLORS.daw.seq_selected_item
            else:
                brush = shared.TRACK_COLORS.get_color(
                    self.audio_item.track_num,
                )
        else:
            brush = theme.SYSTEM_COLORS.daw.seq_item_background
        self.setBrush(
            QColor(brush),
        )
        if self.isSelected() or override:
            item_color = QColor(
                theme.SYSTEM_COLORS.daw.seq_selected_item,
            )
            self.setBrush(item_color)
            self.label_bg.setBrush(item_color)
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(shared.SPLIT_LINE_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_item_text_selected,
                ),
            )
            handle_brush = QColor(
                theme.SYSTEM_COLORS.daw.seq_item_handle_selected,
            )
            self.start_handle.setBrush(handle_brush)
            self.length_handle.setBrush(handle_brush)
            self.stretch_handle.setBrush(handle_brush)
        else:
            if _shared.SEQUENCE_EDITOR_MODE == 1:
                self.setOpacity(0.3)
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(shared.SPLIT_LINE_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_item_text,
                ),
            )
            handle_brush = QColor(
                theme.SYSTEM_COLORS.daw.seq_item_handle,
            )
            self.start_handle.setBrush(handle_brush)
            self.length_handle.setBrush(handle_brush)
            self.stretch_handle.setBrush(handle_brush)
            brush = QColor(
                shared.TRACK_COLORS.get_color(self.audio_item.track_num),
            )
            self.label_bg.setBrush(brush)

    def pos_to_musical_time(self, a_pos):
        return a_pos / _shared.SEQUENCER_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsPolygonItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.isSelected():
                f_item.min_start = f_item.pos().x() * -1.0
                f_item.is_start_resizing = True
                f_item.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
                    False,
                )

    def length_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsPolygonItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
                    False,
                )

    def stretch_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_sequence_pos = (_shared.SEQUENCER_PX_PER_BEAT *
            get_current_sequence_length())
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.isSelected() and \
            f_item.audio_item.time_stretch_mode >= 2:
                f_item.is_stretching = True
                f_item.max_stretch = f_max_sequence_pos - f_item.pos().x()
                f_item.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
                    False,
                )
                #for f_path in f_item.path_items:
                #    f_path.hide()

    def check_selected_status(self):
        """ If a handle is clicked and not selected, clear the selection
            and select only this item
        """
        if not self.isSelected():
            shared.SEQUENCER.scene.clearSelection()
            self.setSelected(True)

    def select_file_instance(self):
        shared.SEQUENCER.scene.clearSelection()
        f_uid = self.audio_item.uid
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.audio_item.uid == f_uid:
                f_item.setSelected(True)

    def reset_end(self):
        f_list = shared.SEQUENCER.get_selected()
        for f_item in f_list:
            f_old = f_item.audio_item.start_offset
            f_item.audio_item.start_offset = 0.0
            f_item.audio_item.length_beats += f_old
            self.draw()
            self.clip_at_sequence_end()
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(_("Reset sample ends for item(s)"))
        global_open_audio_items()

    def mousePressEvent(self, a_event):
        if (
            glbl_shared.IS_PLAYING
            or
            a_event.button() == QtCore.Qt.MouseButton.RightButton
        ):
            return

        if a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.AltModifier
        ):
            self.setSelected(not self.isSelected())
            shared.SEQUENCER.set_selected_strings()
            return

        if not self.isSelected():
            shared.SEQUENCER.scene.clearSelection()
            self.setSelected(True)

        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            f_item = self.audio_item
            f_item_old = f_item.clone()
            shared.CURRENT_SEQUENCE.add_item(f_item_old)
            f_scene_pos = self.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(
                f_scene_pos) - f_item_old.start_beat
            f_item.start_beat = f_item.start_beat + f_musical_pos
            f_item.length_beats = f_item_old.length_beats - f_musical_pos
            f_item.start_offset = f_musical_pos + f_item_old.start_offset
            f_item_old.length_beats = f_musical_pos
            constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
            constants.DAW_PROJECT.commit(_("Split sequencer item"))
            shared.SEQ_WIDGET.open_sequence()
        else:
            if a_event.modifiers() == (
                QtCore.Qt.KeyboardModifier.ControlModifier
            ):
                a_event.accept()
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.event_pos_orig = qt_event_pos(a_event).x()
            for f_item in shared.SEQUENCER.get_selected():
                f_item_pos = f_item.pos().x()
                f_item.setZValue(2400.0)
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == (
                    QtCore.Qt.KeyboardModifier.ControlModifier
                ):
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    shared.SEQUENCER.draw_item(f_item.name, f_item.audio_item)
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()

    def hoverEnterEvent(self, a_event):
        shared.set_move_cursor()
        f_item_pos = self.pos().x()
        self.quantize_offset = f_item_pos - self.quantize_all(f_item_pos)
        super().hoverEnterEvent(a_event)

    def hoverMoveEvent(self, a_event):
        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            if not self.split_line_is_shown:
                self.split_line_is_shown = True
                self.split_line.show()
            f_x = qt_event_pos(a_event).x()
            f_x = self.quantize_all(f_x)
            f_x -= self.quantize_offset
            self.split_line.setPos(f_x, 0.0)
        else:
            if self.split_line_is_shown:
                self.split_line_is_shown = False
                self.split_line.hide()

    def hoverLeaveEvent(self, a_event):
        shared.restore_move_cursor()
        if self.split_line_is_shown:
            self.split_line_is_shown = False
            self.split_line.hide()
        super().hoverLeaveEvent(a_event)

    def y_pos_to_lane_number(self, a_y_pos):
        f_lane_num = int(
            (a_y_pos - _shared.SEQUENCE_EDITOR_HEADER_HEIGHT)
            /
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        )
        f_lane_num = clip_value(
            f_lane_num,
            0,
            TRACK_COUNT_ALL - 1,
        )
        f_y_pos = (
            f_lane_num * shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        ) + _shared.SEQUENCE_EDITOR_HEADER_HEIGHT
        return f_lane_num, f_y_pos

    def lane_number_to_y_pos(self, a_lane_num):
        a_lane_num = clip_value(
            a_lane_num, 0, TRACK_COUNT_ALL)
        return (
            a_lane_num * shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        ) + _shared.SEQUENCE_EDITOR_HEADER_HEIGHT

    def quantize_all(self, a_x):
        f_x = a_x
        if _shared.SEQ_QUANTIZE:
            f_x = round(
                f_x / _shared.SEQUENCER_QUANTIZE_PX
            ) * _shared.SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if (
            _shared.SEQ_QUANTIZE
            and
            f_x < _shared.SEQUENCER_QUANTIZE_PX
        ):
            f_x = _shared.SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= _shared.SEQUENCER_QUANTIZE_PX
        return f_x

    def mouseMoveEvent(self, a_event):
        if glbl_shared.IS_PLAYING or self.event_pos_orig is None:
            return

        f_event_pos = qt_event_pos(a_event).x()
        f_event_diff = f_event_pos - self.event_pos_orig

        if self.is_resizing:
            for f_item in shared.SEQUENCER.get_selected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = clip_min(f_x, shared.AUDIO_ITEM_HANDLE_SIZE)
                f_x = f_item.quantize(f_x)
                f_x -= f_item.quantize_offset
                f_item.length_handle.setPos(
                    f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                    shared.SEQUENCE_EDITOR_TRACK_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_start_resizing:
            for f_item in shared.SEQUENCER.get_selected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = clip_value(
                    f_x, f_item.sample_start_offset_px,
                    f_item.length_handle.pos().x())
                f_x = clip_min(f_x, f_item.min_start)
                if f_x > f_item.min_start:
                    f_x = f_item.quantize_start(f_x)
                    f_x -= f_item.quantize_offset
                f_item.start_handle.setPos(
                    f_x, shared.SEQUENCE_EDITOR_TRACK_HEIGHT -
                        shared.AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_stretching:
            for f_item in shared.SEQUENCER.audio_items:
                if f_item.isSelected() and \
                f_item.audio_item.time_stretch_mode >= 2:
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = clip_value(
                        f_x, f_item.stretch_width_default * 0.1,
                        f_item.stretch_width_default * 200.0)
                    f_x = clip_max(f_x, f_item.max_stretch)
                    f_x = f_item.quantize(f_x)
                    f_x -= f_item.quantize_offset
                    f_item.stretch_handle.setPos(
                        f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                        (shared.SEQUENCE_EDITOR_TRACK_HEIGHT * 0.5) -
                        (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5))
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)
            if _shared.SEQ_QUANTIZE:
                f_max_x = (
                    get_current_sequence_length()
                    *
                    _shared.SEQUENCER_PX_PER_BEAT
                ) - _shared.SEQUENCER_QUANTIZE_PX
            else:
                f_max_x = (get_current_sequence_length() *
                    _shared.SEQUENCER_PX_PER_BEAT) - shared.AUDIO_ITEM_HANDLE_SIZE
            f_new_lane, f_ignored = self.y_pos_to_lane_number(
                a_event.scenePos().y(),
            )
            f_lane_offset = f_new_lane - self.audio_item.track_num
            for f_item in shared.SEQUENCER.get_selected():
                f_pos_x = f_item.pos().x()
                f_pos_x = clip_value(f_pos_x, 0.0, f_max_x)
                f_pos_y = self.lane_number_to_y_pos(
                    f_lane_offset + f_item.audio_item.track_num)
                f_pos_x = f_item.quantize_all(f_pos_x)
                f_item.setPos(f_pos_x, f_pos_y)
                if not f_item.is_moving:
                    f_item.is_moving = True
                    # Triggers a bug in Qt5 where the pixmaps in a long
                    # tiled item disappear
                    #f_item.setGraphicsEffect(QGraphicsOpacityEffect())

    def mouseReleaseEvent(self, a_event):
        if glbl_shared.IS_PLAYING or self.event_pos_orig is None:
            return
        f_was_resizing = self.is_resizing
        QApplication.restoreOverrideCursor()
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_stretched_items = []
        f_event_pos = qt_event_pos(a_event).x()
        f_event_diff = f_event_pos - self.event_pos_orig
        f_was_copying = self.is_copying
        if f_was_copying:
            a_event.accept()
        for f_audio_item in shared.SEQUENCER.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = clip_min(f_audio_item.pos().x(), 0.0)
            if f_audio_item.is_resizing:
                f_x = (f_audio_item.width_orig + f_event_diff +
                    f_audio_item.quantize_offset)
                f_x = clip_min(f_x, shared.AUDIO_ITEM_HANDLE_SIZE)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(
                    0.0,
                    0.0,
                    float(f_x),
                    float(shared.SEQUENCE_EDITOR_TRACK_HEIGHT),
                )
                f_item.length_beats = f_x /_shared.SEQUENCER_PX_PER_BEAT
                LOG.info(f_item.length_beats)
                f_did_change = True
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_old_start = f_item.start_beat
                f_item.start_beat = self.pos_to_musical_time(f_x)
                f_item.start_offset = ((f_x -
                    f_audio_item.start_handle_scene_min) /
                    (f_audio_item.start_handle_scene_max -
                    f_audio_item.start_handle_scene_min)) * \
                    f_item.length_beats
                f_item.start_offset = clip_min(
                    f_item.start_offset, 0.0)
                f_item.length_beats -= f_item.start_beat - f_old_start
            elif (
                f_audio_item.is_stretching
                and
                f_item.time_stretch_mode >= 2
            ):
                f_reset_selection = True
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = clip_value(
                    f_x, f_audio_item.stretch_width_default * 0.1,
                    f_audio_item.stretch_width_default * 200.0)
                f_x = clip_max(f_x, f_audio_item.max_stretch)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_item.timestretch_amt = \
                    f_x / f_audio_item.stretch_width_default
                f_item.timestretch_amt_end = f_item.timestretch_amt
                if (
                    f_item.time_stretch_mode >= 3
                    and
                    f_audio_item.orig_string != str(f_item)
                ):
                    f_was_stretching = True
                    f_ts_result = constants.PROJECT.timestretch_audio_item(
                        f_item,
                    )
                    if f_ts_result is not None:
                        f_stretched_items.append(f_ts_result)
                f_audio_item.setRect(
                    0.0,
                    0.0,
                    float(f_x),
                    float(shared.SEQUENCE_EDITOR_TRACK_HEIGHT),
                )
            else:
                f_item.modified = True
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    shared.CURRENT_SEQUENCE.add_item(f_item_old)
                else:
                    f_audio_item.set_brush(f_item.track_num)
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.track_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
                f_item.start_beat = f_audio_item.pos_to_musical_time(f_pos_x)
                f_did_change = True
            f_audio_item.clip_at_sequence_end()
            f_item_str = str(f_item)
            if f_item_str != f_audio_item.orig_string:
                f_audio_item.orig_string = f_item_str
                f_did_change = True
                if not f_reset_selection:
                    f_audio_item.draw()
            f_audio_item.is_moving = False
            f_audio_item.is_resizing = False
            f_audio_item.is_start_resizing = False
            f_audio_item.is_copying = False
            f_audio_item.is_fading_in = False
            f_audio_item.is_fading_out = False
            f_audio_item.is_stretching = False
            f_audio_item.setGraphicsEffect(None)
            f_audio_item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
            )
        if f_was_resizing:
            _shared.LAST_ITEM_LENGTH = self.audio_item.length_beats

        if f_did_change:
            #f_audio_items.deduplicate_items()
            if f_was_stretching:
                pass
            constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
            constants.DAW_PROJECT.commit(_("Update sequencer items"))
        shared.SEQUENCER.set_selected_strings()
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        shared.SEQ_WIDGET.open_sequence()

