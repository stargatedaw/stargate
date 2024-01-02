from . import _shared
from sglib.math import (
    clip_min,
    clip_value,
    linear_interpolate,
)
from sgui.daw import shared
from sglib import constants
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.models import stargate as sg_project, theme
from sglib.lib import util
from sglib.lib.util import *
from sglib.lib.translate import _
from sglib.math import color_interpolate
from sgui.sgqt import *
from sgui import shared as glbl_shared
from sgui.util import get_font


PREVIEW_NOTES = set()

class NotePreviewer:
    def __init__(self):
        self.active = get_file_setting('preview-note', int, 1)
        self.last_note = None
        self.channel = shared.ITEM_EDITOR.get_midi_channel()
        self.rack = shared.CURRENT_ITEM_TRACK

    def update(self, note):
        if (
            len(PREVIEW_NOTES) > 6
            or
            glbl_shared.IS_PLAYING
            or
            glbl_shared.IS_RECORDING
        ):
            if self.last_note is not None:
                constants.DAW_IPC.note_off(
                    self.rack,
                    self.last_note,
                    self.channel,
                )
            return

        if not self.active or note == self.last_note:
            return

        assert note >= 0 and note <= 120, note
        constants.DAW_IPC.note_off(self.rack, self.last_note, self.channel)
        self.last_note = note
        constants.DAW_IPC.note_on(self.rack, note, self.channel)

    def __del__(self):
        constants.DAW_IPC.note_off(self.rack, self.last_note, self.channel)

class PianoRollNoteItem(QGraphicsRectItem):
    """ An individual note in the PianoRollEditor """
    def __init__(
        self,
        a_length,
        a_note_height,
        a_note,
        a_note_item,
        a_enabled=True,
    ):
        QGraphicsRectItem.__init__(self, 0, 0, a_length, a_note_height)
        if a_enabled:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges,
            )
            self.setZValue(1002.0)
        else:
            self.setZValue(1001.0)
            self.setEnabled(False)
            self.setOpacity(0.3)
        self.note_height = a_note_height
        self.current_note_text = None
        self.note_item = a_note_item
        self.setAcceptHoverEvents(True)
        self.resize_start_pos = self.note_item.start
        self.is_copying = False
        self.is_velocity_dragging = False
        self.is_velocity_curving = False
        self.new_note = False
        if (
            _shared.SELECTED_PIANO_NOTE is not None
            and
            a_note_item == _shared.SELECTED_PIANO_NOTE
        ):
            self.is_resizing = True
            shared.PIANO_ROLL_EDITOR.click_enabled = True
        else:
            self.is_resizing = False
        self.showing_resize_cursor = False
        self.resize_rect = self.rect()
        self.mouse_y_pos = QCursor.pos().y()
        self.note_text = get_font().QGraphicsSimpleTextItem(self)
        self.note_text.setPen(QPen(QtCore.Qt.GlobalColor.black))
        self.update_note_text()
        self.vel_line = QGraphicsLineItem(self)
        self.set_vel_line()
        self.set_brush()
        self.setToolTip(
            'A MIDI note to be sent to an instrument in the plugin rack. '
            'Select and move with the mouse, click near the end and drag '
            f'to change note length. {util.KEY_ALT}+click to multi-select. '
            'SHIFT+drag: position freely'
        )
        self.previewer = None
        self.selection_toggle = False

    def set_vel_line(self):
        if _shared.PARAMETER == 0:
            f_vel = self.note_item.velocity
            f_rect = self.rect()
            f_y = (1.0 - (f_vel * 0.007874016)) * f_rect.height()
            f_width = f_rect.width()
            self.vel_line.setLine(0.0, f_y, f_width, f_y)
        elif _shared.PARAMETER >= 1:
            value = self.note_item.get_pmn_param(_shared.PARAMETER)
            f_rect = self.rect()
            f_y = (1.0 - ((value + 1.0) * 0.5)) * f_rect.height()
            f_width = f_rect.width()
            self.vel_line.setLine(0.0, f_y, f_width, f_y)

    def set_brush(self):
        if _shared.PARAMETER == 0:  # velocity
            pos = (1.0 - (self.note_item.velocity / 127.0))
        elif _shared.PARAMETER >= 1:
            value = self.note_item.get_pmn_param(_shared.PARAMETER)
            pos = (1.0 - ((value + 1.0) * 0.5))

        pos = clip_value(pos, 0.0, 1.0)
        color = color_interpolate(
            theme.SYSTEM_COLORS.daw.note_vel_min_color,
            theme.SYSTEM_COLORS.daw.note_vel_max_color,
            pos,
        )
        brush = QColor(color)
        self.setBrush(brush)

    def update_note_text(self, a_note_num=None):
        f_note_num = a_note_num if a_note_num is not None \
            else self.note_item.note_num
        f_octave = (f_note_num // 12) - 2
        f_note = _shared.PIANO_ROLL_NOTE_LABELS[f_note_num % 12]
        f_text = "{}{}".format(f_note, f_octave)
        if f_text != self.current_note_text:
            self.current_note_text = f_text
            self.note_text.setText(f_text)

    def mouse_is_at_end(self, a_pos):
        f_width = self.rect().width()
        if f_width >= 30.0:
            return a_pos.x() > (f_width - 15.0)
        else:
            return a_pos.x() > (f_width * 0.72)

    def delete_later(self):
        if self.isEnabled() and self not in _shared.PIANO_ROLL_DELETED_NOTES:
            _shared.PIANO_ROLL_DELETED_NOTES.append(self)
            self.hide()

    def delete(self):
        shared.CURRENT_ITEM.remove_note(self.note_item)

    def show_resize_cursor(self, a_event):
        f_is_at_end = self.mouse_is_at_end(qt_event_pos(a_event))
        if f_is_at_end and not self.showing_resize_cursor:
            QApplication.setOverrideCursor(
                QtCore.Qt.CursorShape.SizeHorCursor,
            )
            self.showing_resize_cursor = True
        elif not f_is_at_end and self.showing_resize_cursor:
            QApplication.restoreOverrideCursor()
            self.showing_resize_cursor = False

    def get_selected_string(self):
        return self.note_item.selection_str()

    def hoverEnterEvent(self, a_event):
        shared.set_move_cursor()
        shared.PIANO_ROLL_EDITOR.click_enabled = False
        super().hoverEnterEvent(a_event)

    def hoverMoveEvent(self, a_event):
        #QGraphicsRectItem.hoverMoveEvent(self, a_event)
        if not self.is_resizing and shared._is_move_cursor():
            shared.PIANO_ROLL_EDITOR.click_enabled = False
            self.show_resize_cursor(a_event)

    def hoverLeaveEvent(self, a_event):
        shared.restore_move_cursor()
        shared.PIANO_ROLL_EDITOR.click_enabled = True
        if self.showing_resize_cursor:
            QApplication.restoreOverrideCursor()
            self.showing_resize_cursor = False
        super().hoverLeaveEvent(a_event)

    def mouseDoubleClickEvent(self, a_event):
        QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def _mp_vel_drag(self, event):
        if not self.isSelected():
            shared.PIANO_ROLL_EDITOR.scene.clearSelection()
            self.setSelected(True)
        self.is_velocity_dragging = True
        self._mp_vel_finish(event)

    def _mp_vel_curve(self, event):
        if not self.isSelected():
            shared.PIANO_ROLL_EDITOR.scene.clearSelection()
            self.setSelected(True)
        f_list = [
            x.note_item.start
            for x in shared.PIANO_ROLL_EDITOR.get_selected_items()
        ]
        if len(f_list) > 1:
            f_list.sort()
            self.is_velocity_curving = True
            self.vc_start = f_list[0]
            self.vc_mid = self.note_item.start
            self.vc_end = f_list[-1]
        elif len(f_list) <= 1:
            self.is_velocity_dragging = True
        self._mp_vel_finish(event)

    def _mp_vel_finish(self, event):
        event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self, event)
        self.orig_y = qt_event_pos(event).y()
        QApplication.setOverrideCursor(QtCore.Qt.CursorShape.BlankCursor)
        for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
            if _shared.PARAMETER == 0:
                f_item.orig_value = f_item.note_item.velocity
            elif _shared.PARAMETER >= 1:
                f_item.orig_value = f_item.note_item.get_pmn_param(
                    _shared.PARAMETER,
                )
            f_item.set_brush()
        for f_item in shared.PIANO_ROLL_EDITOR.note_items:
            if _shared.PARAMETER == 0:
                f_item.note_text.setText(str(f_item.note_item.velocity))
            if _shared.PARAMETER >= 1:
                f_item.note_text.setText(
                    str(f_item.note_item.get_pmn_param(_shared.PARAMETER)),
                )

    def _mp_resize(self, event):
        self.is_resizing = True
        self.mouse_y_pos = QCursor.pos().y()
        self.resize_last_mouse_pos = qt_event_pos(event).x()
        for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
            f_item.resize_start_pos = f_item.note_item.start
            f_item.resize_pos = f_item.pos()
            f_item.resize_rect = f_item.rect()

    def _mp_copy(self, event):
        self.is_copying = True
        for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
            shared.PIANO_ROLL_EDITOR.draw_note(f_item.note_item)

    def mousePressEvent(self, a_event):
        if a_event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        if not self.new_note and a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.AltModifier
        ):
            self.selection_toggle = True
            self.setSelected(not self.isSelected())
            return
        if shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
            _shared.piano_roll_set_delete_mode(True)
            self.delete_later()
            return
        elif a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.ControlModifier
            |
            QtCore.Qt.KeyboardModifier.AltModifier
        ):
            self._mp_vel_drag(a_event)
        elif a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.ControlModifier
            |
            QtCore.Qt.KeyboardModifier.ShiftModifier
        ):
            self._mp_vel_curve(a_event)
        else:
            a_event.setAccepted(True)
            QGraphicsRectItem.mousePressEvent(self, a_event)
            s_brush = QColor(
                theme.SYSTEM_COLORS.daw.note_selected_color,
            )
            self.setBrush(s_brush)
            self.o_pos = self.pos()
            if self.mouse_is_at_end(qt_event_pos(a_event)):
                self._mp_resize(a_event)
            elif a_event.modifiers() == (
                QtCore.Qt.KeyboardModifier.ControlModifier
            ):
                self._mp_copy(a_event)
        shared.PIANO_ROLL_EDITOR.click_enabled = True

    def _mm_vel_drag(self, f_item, f_val):
        if _shared.PARAMETER == 0:
            f_new_vel = clip_value(
                f_val + f_item.orig_value,
                1,
                127,
            )
            f_new_vel = int(f_new_vel)
            f_item.note_item.velocity = f_new_vel
            f_item.note_text.setText(str(f_new_vel))
        elif _shared.PARAMETER >= 1:
            new_value = clip_value(
                (f_val * 0.01) + f_item.orig_value,
                -1.0,
                1.0,
            )
            new_value = round(new_value, 2)
            f_item.note_item.set_pmn_param(
                _shared.PARAMETER,
                new_value,
            )
            f_item.note_text.setText(str(new_value))
        f_item.set_brush()
        f_item.set_vel_line()

    def _mm_vel_curve(self, f_item, f_val):
        if _shared.PARAMETER == 0:
            f_start = f_item.note_item.start
            if f_start == self.vc_mid:
                f_new_vel = f_val + f_item.orig_value
            else:
                if f_start > self.vc_mid:
                    f_frac = (f_start -
                        self.vc_mid) / (self.vc_end - self.vc_mid)
                    f_new_vel = linear_interpolate(
                        f_val, 0.3 * f_val, f_frac)
                else:
                    f_frac = (f_start -
                        self.vc_start) / (self.vc_mid - self.vc_start)
                    f_new_vel = linear_interpolate(
                        0.3 * f_val, f_val, f_frac)
                f_new_vel += f_item.orig_value
            f_new_vel = clip_value(f_new_vel, 1, 127)
            f_new_vel = int(f_new_vel)
            f_item.note_item.velocity = f_new_vel
            f_item.note_text.setText(str(f_new_vel))
            f_item.set_brush()
            f_item.set_vel_line()
        elif _shared.PARAMETER >= 1:
            f_start = f_item.note_item.start
            if f_start == self.vc_mid:
                new_value = (f_val * 0.01) + f_item.orig_value
            else:
                if f_start > self.vc_mid:
                    f_frac = (f_start -
                        self.vc_mid) / (self.vc_end - self.vc_mid)
                    new_value = linear_interpolate(
                        f_val * 0.01,
                        0.003 * f_val,
                        f_frac,
                    )
                else:
                    f_frac = (f_start -
                        self.vc_start) / (self.vc_mid - self.vc_start)
                    new_value = linear_interpolate(
                        0.003 * f_val,
                        f_val * 0.01,
                        f_frac,
                    )
                new_value += f_item.orig_value
            new_value = clip_value(new_value, -1.0, 1.0)
            new_value = round(new_value, 2)
            f_item.note_item.set_pmn_param(
                _shared.PARAMETER,
                new_value,
            )
            f_item.note_text.setText(str(new_value))
            f_item.set_brush()
            f_item.set_vel_line()

    def _mm_resize(self, f_item, f_pos_x):
        if shared.PIANO_ROLL_SNAP:
            f_adjusted_width = round(
                f_pos_x / shared.PIANO_ROLL_SNAP_VALUE) * \
                shared.PIANO_ROLL_SNAP_VALUE
            if f_adjusted_width == 0.0:
                f_adjusted_width = shared.PIANO_ROLL_SNAP_VALUE
        else:
            f_adjusted_width = clip_min(
                f_pos_x,
                shared.PIANO_ROLL_MIN_NOTE_LENGTH,
            )
        f_item.resize_rect.setWidth(int(f_adjusted_width))
        f_item.setRect(f_item.resize_rect)
        f_item.setPos(f_item.resize_pos.x(), f_item.resize_pos.y())
        # Does not work on Wayland
        #QCursor.setPos(QCursor.pos().x(), self.mouse_y_pos)

    def _mm_move(self, a_event, f_item, preview):
        is_shift = bool(
            a_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        f_pos_x = f_item.pos().x()
        f_pos_y = f_item.pos().y()
        if f_pos_x < shared.PIANO_KEYS_WIDTH:
            f_pos_x = shared.PIANO_KEYS_WIDTH
        elif f_pos_x > shared.PIANO_ROLL_GRID_MAX_START_TIME:
            f_pos_x = shared.PIANO_ROLL_GRID_MAX_START_TIME
        if f_pos_y < _shared.PIANO_ROLL_HEADER_HEIGHT:
            f_pos_y = _shared.PIANO_ROLL_HEADER_HEIGHT
        elif f_pos_y > shared.PIANO_ROLL_TOTAL_HEIGHT:
            f_pos_y = shared.PIANO_ROLL_TOTAL_HEIGHT
        f_pos_y = \
            (int((f_pos_y - _shared.PIANO_ROLL_HEADER_HEIGHT) /
            self.note_height) * self.note_height) + \
            _shared.PIANO_ROLL_HEADER_HEIGHT
        if not is_shift and shared.PIANO_ROLL_SNAP:
            f_pos_x = (int((f_pos_x - shared.PIANO_KEYS_WIDTH) /
            shared.PIANO_ROLL_SNAP_VALUE) *
            shared.PIANO_ROLL_SNAP_VALUE) + shared.PIANO_KEYS_WIDTH
        f_item.setPos(f_pos_x, f_pos_y)
        f_new_note = self.y_pos_to_note(f_pos_y)
        f_item.update_note_text(f_new_note)
        if preview:
            orig_note = f_item.note_item.note_num
            if orig_note not in PREVIEW_NOTES and not f_item.previewer:
                PREVIEW_NOTES.add(orig_note)
                f_item.previewer = NotePreviewer()
            if f_item.previewer:
                f_item.previewer.update(f_new_note)

    def mouseMoveEvent(self, a_event):
        if a_event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        if self.selection_toggle:
            return
        if shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
            self.delete_later()
            return
        if self.is_velocity_dragging or self.is_velocity_curving:
            f_pos = qt_event_pos(a_event)
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.5)
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)

        if self.is_resizing:
            f_pos_x = qt_event_pos(a_event).x()
            self.resize_last_mouse_pos = qt_event_pos(a_event).x()
        selected_items = list(shared.PIANO_ROLL_EDITOR.get_selected_items())
        unique_notes = {x.note_item.note_num for x in selected_items}
        for f_item in selected_items:
            if self.is_resizing:
                self._mm_resize(f_item, f_pos_x)
            elif self.is_velocity_dragging:
                self._mm_vel_drag(f_item, f_val)
            elif self.is_velocity_curving:
                self._mm_vel_curve(f_item, f_val)
            else:
                self._mm_move(a_event, f_item, len(unique_notes) <= 6)

    def y_pos_to_note(self, a_y):
        return int(
            shared.PIANO_ROLL_NOTE_COUNT - (
                (
                    a_y - _shared.PIANO_ROLL_HEADER_HEIGHT
                ) / shared.PIANO_ROLL_NOTE_HEIGHT
            )
        )

    def _mr_resize(self, f_item, f_pos_x, f_recip):
        f_new_note_length = (
            (f_pos_x + f_item.rect().width() - shared.PIANO_KEYS_WIDTH)
            * f_recip * shared.CURRENT_ITEM_LEN
        ) - f_item.resize_start_pos
        if (
            shared.PIANO_ROLL_SNAP
            and
            f_new_note_length < shared.PIANO_ROLL_SNAP_BEATS
        ):
            f_new_note_length = shared.PIANO_ROLL_SNAP_BEATS
        elif f_new_note_length < min_note_length:
            f_new_note_length = min_note_length
        f_item.note_item.set_length(f_new_note_length)

    def _mr_copy(self, f_item, f_pos_x, f_recip, f_new_selection):
        f_pos_y = f_item.pos().y()
        f_new_note_start = (
            f_pos_x - shared.PIANO_KEYS_WIDTH
        ) * shared.CURRENT_ITEM_LEN * f_recip
        f_new_note_num = self.y_pos_to_note(f_pos_y)
        f_new_note = sg_project.MIDINote(
            f_new_note_start,
            f_item.note_item.length,
            f_new_note_num,
            f_item.note_item.velocity,
            f_item.note_item.pan,
            f_item.note_item.attack,
            f_item.note_item.decay,
            f_item.note_item.sustain,
            f_item.note_item.release,
            f_item.note_item.channel,
        )
        shared.CURRENT_ITEM.add_note(f_new_note, False)
        # pass a ref instead of a str in case
        # fix_overlaps() modifies it.
        f_item.note_item = f_new_note
        f_new_selection.append(f_item)

    def _mr_move(self, f_item, f_pos_x, f_recip):
        f_pos_y = f_item.pos().y()
        f_new_note_start = (
            f_pos_x - shared.PIANO_KEYS_WIDTH
        ) * shared.CURRENT_ITEM_LEN * f_recip
        f_new_note_num = self.y_pos_to_note(f_pos_y)
        shared.CURRENT_ITEM.notes.remove(f_item.note_item)
        f_item.note_item.set_start(f_new_note_start)
        f_item.note_item.note_num = f_new_note_num
        shared.CURRENT_ITEM.notes.append(f_item.note_item)
        shared.CURRENT_ITEM.notes.sort()

    def mouseReleaseEvent(self, a_event):
        if a_event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        if self.selection_toggle:
            shared.PIANO_ROLL_EDITOR.selected_note_strings.clear()
            for item in shared.PIANO_ROLL_EDITOR.get_selected_items():
                shared.PIANO_ROLL_EDITOR.selected_note_strings.append(
                    item.get_selected_string(),
                )
            self.selection_toggle = False
            return
        PREVIEW_NOTES.clear()
        if _shared.PIANO_ROLL_DELETE_MODE:
            _shared.piano_roll_set_delete_mode(False)
            return
        a_event.setAccepted(True)
        f_recip = 1.0 / shared.PIANO_ROLL_GRID_WIDTH
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        if self.is_copying:
            f_new_selection = []
        for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
            f_item.previewer = None
            f_pos_x = f_item.pos().x()
            if self.is_resizing:
                self._mr_resize(f_item, f_pos_x, f_recip)
            elif self.is_velocity_dragging or self.is_velocity_curving:
                pass
            elif self.is_copying:
                self._mr_copy(
                    f_item,
                    f_pos_x,
                    f_recip,
                    f_new_selection,
                )
            else:
                self._mr_move(f_item, f_pos_x, f_recip)
        if self.is_resizing:
            shared.LAST_NOTE_RESIZE = self.note_item.length
        shared.CURRENT_ITEM.fix_overlaps()
        _shared.SELECTED_PIANO_NOTE = None
        shared.PIANO_ROLL_EDITOR.selected_note_strings.clear()
        if self.is_copying:
            for f_new_item in f_new_selection:
                shared.PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_new_item.get_selected_string(),
                )
        else:
            for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
                shared.PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_item.get_selected_string(),
                )
        for f_item in shared.PIANO_ROLL_EDITOR.note_items:
            f_item.is_resizing = False
            f_item.is_copying = False
            f_item.is_velocity_dragging = False
            f_item.is_velocity_curving = False
            f_item.selection_toggle = False
            f_item.new_note = False
        global_save_and_reload_items()
        self.showing_resize_cursor = False
        QApplication.restoreOverrideCursor()
        shared.PIANO_ROLL_EDITOR.click_enabled = True

