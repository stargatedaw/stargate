from . import _shared
from ..abstract import AbstractItemEditor, ItemEditorHeader
from .key import PianoKeyItem
from .note import PianoRollNoteItem
from sglib.math import clip_value, pitch_to_hz
from sgui import widgets
from sgui.daw import shared
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.models import stargate as sg_project
from sglib.lib import strings as sg_strings
from sglib.lib import util
from sglib.lib import scales
from sglib.lib.util import *
from sglib.lib.translate import _
from sglib.models import theme
from sglib.log import LOG
from sgui.sgqt import *
from sgui.util import get_font


class PianoRollEditor(AbstractItemEditor):
    """ This is the QGraphicsView and QGraphicsScene where notes are drawn
    """
    def __init__(self):
        self.viewer_width = 1000
        self.grid_div = 16

        self.end_octave = 8
        self.start_octave = -2
        self.notes_in_octave = 12
        self.piano_width = 32
        self.padding = 2

        self.update_note_height()

        AbstractItemEditor.__init__(self, shared.PIANO_KEYS_WIDTH)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.default_scene_background,
            ),
        )
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setScene(self.scene)
        self.first_open = True

        self.has_selected = False

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.note_items = []

        self.right_click = False
        self.left_click = False
        self.click_enabled = True
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        self.scene.selectionChanged.connect(self.highlight_selected)
        self.selected_note_strings = []
        self.piano_keys = None
        self.vel_rand = 0
        self.vel_emphasis = 0
        self.clipboard = []
        self.setToolTip(sg_strings.PianoRollEditor)

    def update_note_height(self):
        self.note_height = shared.PIANO_ROLL_NOTE_HEIGHT
        self.octave_height = self.notes_in_octave * self.note_height

        self.piano_height = self.note_height * shared.PIANO_ROLL_NOTE_COUNT

        self.piano_height = self.note_height * shared.PIANO_ROLL_NOTE_COUNT
        shared.PIANO_ROLL_TOTAL_HEIGHT = self.piano_height + _shared.PIANO_ROLL_HEADER_HEIGHT

    def get_selected_items(self):
        return (x for x in self.note_items if x.isSelected())


    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def highlight_keys(self, a_state, a_note):
        f_note = int(a_note)
        f_state = int(a_state)
        if self.piano_keys is not None and f_note in self.piano_keys:
            if f_state == 0:
                if self.piano_keys[f_note].is_black:
                    self.piano_keys[f_note].setBrush(QColor(0, 0, 0))
                else:
                    self.piano_keys[f_note].setBrush(
                        QColor(255, 255, 255))
            elif f_state == 1:
                self.piano_keys[f_note].setBrush(QColor(237, 150, 150))
            else:
                assert False, "Invalid state"

    def set_grid_div(self, a_div):
        self.grid_div = int(a_div)

    def scrollContentsBy(self, x, y):
        QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_and_keys()

    def set_header_and_keys(self):
        f_point = self.get_scene_pos()
        self.piano.setPos(f_point.x(), _shared.PIANO_ROLL_HEADER_HEIGHT)
        self.header.setPos(self.piano_width + self.padding, f_point.y())

    def get_scene_pos(self):
        return QtCore.QPointF(
            float(self.horizontalScrollBar().value()),
            float(self.verticalScrollBar().value()),
        )

    def highlight_selected(self):
        self.has_selected = False
        s_brush = QColor(
            theme.SYSTEM_COLORS.daw.note_selected_color,
        )
        for f_item in self.note_items:
            if f_item.isSelected():
                f_item.setBrush(s_brush)
                f_item.note_item.is_selected = True
                self.has_selected = True
            else:
                f_item.note_item.is_selected = False
                f_item.set_brush()

    def set_selected_strings(self):
        self.selected_note_strings = [
            x.get_selected_string()
            for x in self.note_items
            if x.isSelected()
        ]

    def keyPressEvent(self, a_event):
        QGraphicsView.keyPressEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def half_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        self.selected_note_strings = []

        min_split_size = 4.0 / 64.0

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        for f_note in f_selected:
            if f_note.note_item.length < min_split_size:
                continue
            f_half = f_note.note_item.length * 0.5
            f_note.note_item.set_length(f_half)
            f_new_start = f_note.note_item.start + f_half
            f_note_num = f_note.note_item.note_num
            f_velocity = f_note.note_item.velocity
            pan = f_note.note_item.pan
            self.selected_note_strings.append(str(f_note.note_item))
            f_new_note_item = sg_project.MIDINote(
                f_new_start,
                f_half,
                f_note_num,
                f_velocity,
                pan,
                f_note.note_item.attack,
                f_note.note_item.decay,
                f_note.note_item.sustain,
                f_note.note_item.release,
                f_note.note_item.channel,
            )
            shared.CURRENT_ITEM.add_note(f_new_note_item, False)
            self.selected_note_strings.append(str(f_new_note_item))

        global_save_and_reload_items()

    def glue_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        channel = shared.ITEM_EDITOR.get_midi_channel()

        f_dict = {}
        for f_note in f_selected:
            f_note_num = f_note.note_item.note_num
            if not f_note_num in f_dict:
                f_dict[f_note_num] = []
            f_dict[f_note_num].append(f_note)

        f_result = []

        for k in sorted(f_dict.keys()):
            v = f_dict[k]
            if len(v) == 1:
                v[0].setSelected(False)
                f_dict.pop(k)
            else:
                f_max = -1.0
                f_min = 99999999.9
                for f_note in f_dict[k]:
                    f_start = f_note.note_item.start
                    if f_start < f_min:
                        f_min = f_start
                    f_end = f_note.note_item.length + f_start
                    if f_end > f_max:
                        f_max = f_end
                f_vels = [x.note_item.velocity for x in f_dict[k]]
                f_vel = int(sum(f_vels) // len(f_vels))
                pans = [x.note_item.pan for x in f_dict[k]]
                pan = round(sum(pans) / len(pans), 2)

                attacks = [x.note_item.attack for x in f_dict[k]]
                attack = round(sum(attacks) / len(attacks), 2)

                decays = [x.note_item.decay for x in f_dict[k]]
                decay = round(sum(decays) / len(decays), 2)

                sustains = [x.note_item.sustain for x in f_dict[k]]
                sustain = round(sum(sustains) / len(sustains), 2)

                releases = [x.note_item.release for x in f_dict[k]]
                release = round(sum(releases) / len(releases), 2)

                LOG.info(str(f_max))
                LOG.info(str(f_min))
                f_length = f_max - f_min
                LOG.info(str(f_length))
                f_start = f_min
                LOG.info(str(f_start))
                f_new_note = sg_project.MIDINote(
                    f_start,
                    f_length,
                    k,
                    f_vel,
                    pan,
                    attack,
                    decay,
                    sustain,
                    release,
                    channel,
                )
                LOG.info(str(f_new_note))
                f_result.append(f_new_note)

        self.delete_selected(False)
        for f_new_note in f_result:
            shared.CURRENT_ITEM.add_note(f_new_note, False)
        global_save_and_reload_items()


    def copy_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return 0
        self.clipboard = [
            str(x.note_item) for x in self.note_items if x.isSelected()]
        return len(self.clipboard)

    def paste(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        if not self.clipboard:
            QMessageBox.warning(
                self,
                _("Error"),
                _("Nothing copied to the clipboard"),
            )
            return
        for f_item in self.clipboard:
            shared.CURRENT_ITEM.add_note(sg_project.MIDINote.from_str(f_item))
        global_save_and_reload_items()
        self.scene.clearSelection()
        for f_item in self.note_items:
            f_tuple = str(f_item.note_item)
            if f_tuple in self.clipboard:
                f_item.setSelected(True)

    def delete_selected(self, a_save_and_reload=True):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        self.selected_note_strings = []
        for f_item in self.get_selected_items():
            shared.CURRENT_ITEM.remove_note(f_item.note_item)
        if a_save_and_reload:
            global_save_and_reload_items()

    def transpose_selected(self, a_amt):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        f_list = [x for x in self.note_items if x.isSelected()]
        if not f_list:
            QMessageBox.warning(self, _("Error"), _("No notes selected"))
            return
        self.selected_note_strings = []
        for f_item in f_list:
            f_item.note_item.note_num = clip_value(
                f_item.note_item.note_num + a_amt, 0, 120)
            self.selected_note_strings.append(f_item.get_selected_string())
        global_save_and_reload_items()

    def focusOutEvent(self, a_event):
        QGraphicsView.focusOutEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def sceneMouseReleaseEvent(self, a_event):
        if _shared.PIANO_ROLL_DELETE_MODE:
            _shared.piano_roll_set_delete_mode(False)
        else:
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
            self.set_selected_strings()
        self.click_enabled = True

    def sceneMousePressEvent(self, a_event):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
        elif a_event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        elif shared.EDITOR_MODE == shared.EDITOR_MODE_SELECT:
            if self.click_enabled:
                self.scene.clearSelection()
            self.hover_restore_cursor_event()
        elif shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
            _shared.piano_roll_set_delete_mode(True)
            return
        elif (
            a_event.modifiers() == (
                QtCore.Qt.KeyboardModifier.ControlModifier
                |
                QtCore.Qt.KeyboardModifier.AltModifier
            )
            or
            a_event.modifiers() == (
                QtCore.Qt.KeyboardModifier.ControlModifier
                |
                QtCore.Qt.KeyboardModifier.ShiftModifier
            )
        ):
            pass
        elif (
            self.click_enabled
            and
            shared.ITEM_EDITOR.enabled
            and
            shared.EDITOR_MODE == shared.EDITOR_MODE_DRAW
        ):
            self.scene.clearSelection()
            f_pos = a_event.scenePos()
            if self.get_item_at_pos(f_pos, ItemEditorHeader):
                a_event.setAccepted(True)
                QGraphicsScene.mousePressEvent(self.scene, a_event)
                return
            f_pos_x = a_event.scenePos().x()
            f_pos_y = a_event.scenePos().y()
            if (
                f_pos_x > shared.PIANO_KEYS_WIDTH
                and
                f_pos_x < shared.PIANO_ROLL_GRID_MAX_START_TIME
                and
                f_pos_y > _shared.PIANO_ROLL_HEADER_HEIGHT
                and
                f_pos_y < shared.PIANO_ROLL_TOTAL_HEIGHT
            ):
                f_recip = 1.0 / shared.PIANO_ROLL_GRID_WIDTH
                if self.vel_rand == 1:
                    pass
                elif self.vel_rand == 2:
                    pass
                f_note = int(
                    shared.PIANO_ROLL_NOTE_COUNT - ((f_pos_y -
                    _shared.PIANO_ROLL_HEADER_HEIGHT) / self.note_height)) + 1
                channel = shared.ITEM_EDITOR.get_midi_channel()
                if shared.PIANO_ROLL_SNAP:
                    f_beat = (
                        int(
                            (f_pos_x - shared.PIANO_KEYS_WIDTH) /
                            shared.PIANO_ROLL_SNAP_VALUE
                        ) * shared.PIANO_ROLL_SNAP_VALUE
                    ) * f_recip * shared.CURRENT_ITEM_LEN
                    f_note_item = sg_project.MIDINote(
                        f_beat,
                        shared.LAST_NOTE_RESIZE,
                        f_note,
                        self.get_vel(f_beat),
                        channel=channel,
                    )
                else:
                    f_beat = (
                        f_pos_x - shared.PIANO_KEYS_WIDTH
                    ) * f_recip * shared.CURRENT_ITEM_LEN
                    f_note_item = sg_project.MIDINote(
                        f_beat,
                        0.25,
                        f_note,
                        self.get_vel(f_beat),
                        channel=channel,
                    )
                shared.ITEM_EDITOR.add_note(f_note_item)
                _shared.SELECTED_PIANO_NOTE = f_note_item
                f_drawn_note = self.draw_note(f_note_item)
                f_drawn_note.setSelected(True)
                f_drawn_note.resize_start_pos = f_drawn_note.note_item.start
                f_drawn_note.resize_pos = f_drawn_note.pos()
                f_drawn_note.resize_rect = f_drawn_note.rect()
                f_drawn_note.is_resizing = True
                f_cursor_pos = QCursor.pos()
                f_drawn_note.mouse_y_pos = f_cursor_pos.y()
                f_drawn_note.resize_last_mouse_pos = \
                    f_pos_x - f_drawn_note.pos().x()

        a_event.setAccepted(True)
        QGraphicsScene.mousePressEvent(self.scene, a_event)
        QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, a_event):
        QGraphicsView.mouseMoveEvent(self, a_event)
        if _shared.PIANO_ROLL_DELETE_MODE:
            for f_item in self.items(qt_event_pos(a_event)):
                if isinstance(f_item, PianoRollNoteItem):
                    f_item.delete_later()

    def hover_restore_cursor_event(self, a_event=None):
        QApplication.restoreOverrideCursor()

    def draw_header(self):
        self.px_per_beat = self.viewer_width / shared.CURRENT_ITEM_LEN
        AbstractItemEditor.draw_header(
            self,
            self.viewer_width,
            _shared.PIANO_ROLL_HEADER_HEIGHT,
        )
        self.header.hoverEnterEvent = self.hover_restore_cursor_event
        self.scene.addItem(self.header)
        #self.header.mapToScene(self.piano_width + self.padding, 0.0)
        self.value_width = self.px_per_beat / self.grid_div
        self.header.setZValue(1003.0)
        if shared.ITEM_REF_POS:
            f_start, f_end = shared.ITEM_REF_POS
            f_start_x = f_start * self.px_per_beat
            f_end_x = f_end * self.px_per_beat
            f_start_line = QGraphicsLineItem(
                f_start_x,
                0.0,
                f_start_x,
                _shared.PIANO_ROLL_HEADER_HEIGHT,
                self.header,
            )
            start_pen = QPen(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_header_region,
                ),
                6.0,
            )
            f_start_line.setPen(start_pen)
            f_end_line = QGraphicsLineItem(
                f_end_x,
                0.0,
                f_end_x,
                _shared.PIANO_ROLL_HEADER_HEIGHT,
                self.header,
            )
            end_pen = QPen(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_header_region,
                ),
                6.0,
            )
            f_end_line.setPen(end_pen)

    def draw_piano(self):
        self.piano_keys = {}
        f_black_notes = [2, 4, 6, 9, 11]
        f_piano_label = QFont()
        f_piano_label.setPointSize(8)
        self.piano = QGraphicsRectItem(
            0.,
            0.,
            float(self.piano_width),
            float(self.piano_height),
        )
        self.scene.addItem(self.piano)
        self.piano.mapToScene(
            0.0,
            _shared.PIANO_ROLL_HEADER_HEIGHT,
        )
        f_key = PianoKeyItem(self.piano_width, self.note_height, self.piano)
        f_label = get_font().QGraphicsSimpleTextItem("C8", f_key)
        f_label.setPen(QtCore.Qt.GlobalColor.black)
        f_label.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )
        f_label.setPos(4, 0)
        f_label.setFont(f_piano_label)
        f_key.setBrush(QColor(255, 255, 255))
        f_note_index = 0
        f_note_num = 0

        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_key = PianoKeyItem(
                    self.piano_width, self.note_height, self.piano)
                self.piano_keys[f_note_index] = f_key
                f_note_index += 1
                f_key.setPos(
                    0, (self.note_height * j) + (self.octave_height * (i - 1)))

                tooltip = "{} - {}hz - MIDI note #{}".format(
                    util.note_num_to_string(f_note_num),
                    round(pitch_to_hz(f_note_num)),
                    f_note_num,
                )
                f_key.setToolTip(tooltip)
                f_note_num += 1
                if j == 12:
                    f_label = get_font().QGraphicsSimpleTextItem("C{}".format(
                        self.end_octave - i), f_key)
                    f_label.setFlag(
                        QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
                    )
                    f_label.setPos(4, 0)
                    f_label.setFont(f_piano_label)
                    f_label.setPen(QtCore.Qt.GlobalColor.black)
                if j in f_black_notes:
                    f_key.setBrush(QColor(0, 0, 0))
                    f_key.is_black = True
                else:
                    f_key.setBrush(QColor(255, 255, 255))
                    f_key.is_black = False
        self.piano.setZValue(1000.0)

    def draw_grid(self):
        f_black_key_brush = QBrush(
            QColor(
                theme.SYSTEM_COLORS.daw.note_black_background,
            ),
        )
        f_white_key_brush = QBrush(
            QColor(
                theme.SYSTEM_COLORS.daw.note_white_background,
            ),
        )
        f_base_brush = QBrush(
            QColor(
                theme.SYSTEM_COLORS.daw.note_root_background,
            ),
        )
        try:
            f_index = \
                shared.PIANO_ROLL_EDITOR_WIDGET.scale_combobox.currentIndex()
        except NameError:
            f_index = 0
        if self.first_open:
            f_index = 0

        f_octave_brushes = scales.scale_to_value_list(
            f_index,
            [f_base_brush, f_white_key_brush, f_black_key_brush],
        )

        f_current_key = 0
        key_index = \
            shared.PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.currentIndex()
        if not self.first_open:
            f_index = 12 - key_index
            f_octave_brushes = \
                f_octave_brushes[f_index:] + f_octave_brushes[:f_index]
        self.first_open = False
        f_note_bar = QGraphicsRectItem(
            0.,
            0.,
            float(self.viewer_width),
            float(self.note_height),
        )
        f_note_bar.hoverMoveEvent = self.hover_restore_cursor_event
        f_note_bar.setBrush(f_base_brush)
        self.scene.addItem(f_note_bar)
        f_note_bar.setPos(
            self.piano_width + self.padding,
            _shared.PIANO_ROLL_HEADER_HEIGHT,
        )
        for i in range(
            self.end_octave - self.start_octave,
            self.start_octave - self.start_octave, -1,
        ):
            for j in range(self.notes_in_octave, 0, -1):
                f_note_bar = QGraphicsRectItem(
                    0.,
                    0.,
                    float(self.viewer_width),
                    float(self.note_height),
                )
                f_note_bar.setZValue(60.0)
                self.scene.addItem(f_note_bar)
                f_note_bar.setBrush(f_octave_brushes[f_current_key])
                f_current_key += 1
                if f_current_key >= len(f_octave_brushes):
                    f_current_key = 0
                f_note_bar_y = (
                    (self.note_height * j)
                    +
                    (self.octave_height * (i - 1))
                    +
                    _shared.PIANO_ROLL_HEADER_HEIGHT
                )
                f_note_bar.setPos(
                    self.piano_width + self.padding, f_note_bar_y,
                )
        f_beat_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.daw.note_beat_line,
            ),
            2.,
        )
        f_line_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.daw.note_snap_line,
            ),
            1.
        )
        self.total_height = (
            self.piano_height
            +
            _shared.PIANO_ROLL_HEADER_HEIGHT
            +
            self.note_height
        )
        for i in range(0, int(shared.CURRENT_ITEM_LEN) + 1):
            f_beat_x = (self.px_per_beat * i) + self.piano_width
            f_beat = self.scene.addLine(
                f_beat_x,
                0,
                f_beat_x,
                self.total_height,
            )

            f_beat.setZValue(1001.0)
            f_beat_number = i
            f_beat.setPen(f_beat_pen)
            if i < shared.CURRENT_ITEM_LEN:
                f_number = get_font().QGraphicsSimpleTextItem(
                    str(f_beat_number + 1), self.header)
                f_number.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
                f_number.setPos((self.px_per_beat * i), 24)
                f_number.setBrush(QtCore.Qt.GlobalColor.white)
                for j in range(0, self.grid_div):
                    f_x = (self.px_per_beat * i) + (self.value_width *
                        j) + self.piano_width
                    f_line = self.scene.addLine(
                        f_x,
                        _shared.PIANO_ROLL_HEADER_HEIGHT,
                        f_x,
                        self.total_height,
                        f_line_pen,
                    )
                    f_line.setZValue(1001.0)
                    if float(j) != self.grid_div * 0.5:
                        f_line.setPen(f_line_pen)

    def default_vposition(self):
        scrollbar = self.verticalScrollBar()
        new_val = int(self.piano_height * 0.5)
        scrollbar.setSliderPosition(new_val)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        shared.ITEM_EDITOR.tab_changed()

    def clear_drawn_items(self):
        self.note_items = []
        self.scene.clear()
        self.update_note_height()
        self.draw_header()
        self.draw_piano()
        self.set_header_and_keys()
        self.draw_grid()

    def draw_item(self):
        self.has_selected = False #Reset the selected-ness state...
        self.viewer_width = shared.PIANO_ROLL_GRID_WIDTH
        self.setSceneRect(
            0.0,
            0.0,
            float(self.viewer_width + 200.0),
            float(self.piano_height + _shared.PIANO_ROLL_HEADER_HEIGHT + 24.0),
        )
        shared.PIANO_ROLL_GRID_MAX_START_TIME = (shared.PIANO_ROLL_GRID_WIDTH -
            1.0) + shared.PIANO_KEYS_WIDTH
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        channel = shared.ITEM_EDITOR.get_midi_channel()
        if shared.CURRENT_ITEM:
            for f_note in shared.CURRENT_ITEM.notes:
                if f_note.channel != channel:
                    continue
                f_note_item = self.draw_note(f_note)
                f_note_item.resize_last_mouse_pos = \
                    f_note_item.scenePos().x()
                f_note_item.resize_pos = f_note_item.scenePos()
                if (
                    f_note_item.get_selected_string()
                    in
                    self.selected_note_strings
                ):
                    f_note_item.setSelected(True)
            if shared.DRAW_LAST_ITEMS and shared.LAST_ITEM:
                f_offset = (
                    shared.LAST_ITEM_REF.start_offset
                    -
                    shared.ITEM_REF_POS[0]
                )
                for f_note in shared.LAST_ITEM.notes:
                    if f_note.channel != channel:
                        continue
                    f_note_item = self.draw_note(
                        f_note,
                        False,
                        a_offset=f_offset,
                    )
            self.scrollContentsBy(0, 0)
#            f_text = get_font().QGraphicsSimpleTextItem(f_name, self.header)
#            f_text.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
#            f_text.setBrush(QtCore.Qt.GlobalColor.yellow)
#            f_text.setPos((f_i * shared.PIANO_ROLL_GRID_WIDTH), 2.0)
        self.setUpdatesEnabled(True)
        self.update()

    def draw_note(self, a_note, a_enabled=True, a_offset=0.0):
        """ a_note is an instance of the sg_project.MIDINote class"""
        f_start = (self.piano_width + self.padding +
            self.px_per_beat * (a_note.start - a_offset))
        f_length = self.px_per_beat * a_note.length
        f_note = (
            _shared.PIANO_ROLL_HEADER_HEIGHT
            +
            self.note_height
            *
            (shared.PIANO_ROLL_NOTE_COUNT - a_note.note_num)
        )
        f_note_item = PianoRollNoteItem(
            f_length,
            self.note_height,
            a_note.note_num,
            a_note,
            a_enabled,
        )
        f_note_item.setPos(f_start, f_note)
        self.scene.addItem(f_note_item)
        if a_enabled:
            self.note_items.append(f_note_item)
            return f_note_item

    def set_vel_rand(self, a_rand, a_emphasis):
        self.vel_rand = int(a_rand)
        self.vel_emphasis = int(a_emphasis)

    def get_vel(self, a_beat):
        if self.vel_rand == 0:
            return 100
        f_emph = self.get_beat_emphasis(a_beat)
        if self.vel_rand == 1:
            return random.randint(75 - f_emph, 100 - f_emph)
        elif self.vel_rand == 2:
            return random.randint(75 - f_emph, 100 - f_emph)
        else:
            assert False, "Invalid velocity randomization value"

    def get_beat_emphasis(self, a_beat, a_amt=25.0):
        if self.vel_emphasis == 0:
            return 0
        f_beat = a_beat
        if self.vel_emphasis == 2:
            f_beat += 0.5
        f_beat = f_beat % 1.0
        if f_beat > 0.5:
            f_beat = 0.5 - (f_beat - 0.5)
            f_beat = 0.5 - f_beat
        return int(f_beat * 2.0 * a_amt)


