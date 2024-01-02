from sglib.models.daw import *
from sgui.daw.shared import *
from sgui.daw.painter_path import clear_caches as daw_painter_clear_cache
from sglib.lib.util import *
from sgui.sgqt import *

from sglib.math import (
    clip_max,
    clip_min,
    clip_value,
    db_to_lin,
    linear_interpolate,
    pitch_to_ratio,
)
from sglib import constants
from sglib.lib import strings as sg_strings
from sglib.lib import util
from sglib.lib.translate import _
from sglib.models import theme
from sgui import shared as glbl_shared
from sgui.daw.lib import item as item_lib
from sgui.daw import painter_path as daw_painter_path, shared
from sgui.shared import AUDIO_ITEM_SCENE_RECT
from sgui.widgets.sample_graph import create_sample_graph
from . import (
    item_context_menu,
    _shared,
)
from sgui.util import get_font


class AudioSeqItemHandle(QGraphicsPolygonItem):
    def __init__(self, _polygon, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)
        self.setPolygon(_polygon)

    def hoverEnterEvent(self, a_event):
        if not glbl_shared.IS_PLAYING and shared._is_move_cursor():
            QApplication.setOverrideCursor(
                QtCore.Qt.CursorShape.SizeHorCursor,
            )
        super().hoverEnterEvent(a_event)

    def hoverLeaveEvent(self, a_event):
        if not glbl_shared.IS_PLAYING and shared._is_move_cursor():
            QApplication.restoreOverrideCursor()
        super().hoverLeaveEvent(a_event)


class AudioSeqItem(QGraphicsRectItem):
    """ This is an individual audio item within the AudioItemSeq """
    def __init__(
        self,
        a_track_num,
        a_audio_item,
        a_graph,
    ):
        QGraphicsRectItem.__init__(self)
        self.setAcceptDrops(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges,
        )
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)

        self.sample_length = a_graph.length_in_seconds
        self.graph_object = a_graph
        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_track_num

        f_uid = self.audio_item.uid
        if f_uid in _shared.PAINTER_PATH_CACHE:
            self.painter_paths = _shared.PAINTER_PATH_CACHE[f_uid]
        else:
            self.painter_paths = create_sample_graph(
                a_graph,
                True,
            )
            _shared.PAINTER_PATH_CACHE[f_uid] = self.painter_paths

        self.y_inc = _shared.AUDIO_ITEM_HEIGHT / len(self.painter_paths)
        f_y_pos = 0.0
        self.path_items = []
        for f_painter_path in self.painter_paths:
            f_path_item = QGraphicsPathItem(f_painter_path)
            f_path_item.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_audio_waveform,
                ),
            )
            f_path_item.setPen(shared.NO_PEN)
            f_path_item.setParentItem(self)
            f_path_item.mapToParent(0.0, 0.0)
            self.path_items.append(f_path_item)
            f_y_pos += self.y_inc
        f_file_name = constants.PROJECT.get_wav_name_by_uid(
            self.audio_item.uid)
        f_file_name = constants.PROJECT.timestretch_lookup_orig_path(
            f_file_name)
        f_name_arr = f_file_name.rsplit("/", 1)
        f_name = f_name_arr[-1]
        self.label = get_font().QGraphicsSimpleTextItem(f_name, parent=self)
        self.label.setPos(10, 0)
        self.label.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )

        self.start_handle = AudioSeqItemHandle(
            shared.BOTTOM_LEFT_TRI,
            parent=self,
        )
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            0.0,
            (
                _shared.AUDIO_ITEM_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle,
        )

        self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

        self.length_handle = AudioSeqItemHandle(
            shared.BOTTOM_RIGHT_TRI,
            parent=self,
        )
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE, shared.AUDIO_ITEM_HANDLE_HEIGHT,
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (_shared.AUDIO_ITEM_HEIGHT * -1.0) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.fade_in_handle = AudioSeqItemHandle(
            shared.TOP_LEFT_TRI,
            parent=self,
        )
        self.fade_in_handle.mousePressEvent = \
            self.fade_in_handle_mouseClickEvent
        self.fade_in_handle_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            0.0,
            self,
        )

        self.fade_out_handle = AudioSeqItemHandle(
            shared.TOP_RIGHT_TRI,
            parent=self,
        )
        self.fade_out_handle.mousePressEvent = \
            self.fade_out_handle_mouseClickEvent
        self.fade_out_handle_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            0.0,
            self,
        )

        self.stretch_handle = AudioSeqItemHandle(
            shared.RECT_ITEM_HANDLE,
            parent=self,
        )
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5
            ) - (_shared.AUDIO_ITEM_HEIGHT * 0.5),
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                _shared.AUDIO_ITEM_HEIGHT * 0.5
            ) + (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle,
        )
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            _shared.AUDIO_ITEM_HEIGHT,
            self,
        )
        self.split_line.hide()
        self.split_line.setPen(shared.SPLIT_LINE_PEN)
        self.split_line.setZValue(3000)
        self.split_line.mapFromParent(0.0, 0.0)
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
        self.is_amp_curving = False
        self.is_amp_dragging = False
        self.is_amp_dragging_audio_pool = False
        self.event_pos_orig = None
        self.width_orig = None
        audio_pool = constants.PROJECT.get_audio_pool()
        by_uid = audio_pool.by_uid()
        ap_entry = by_uid[self.audio_item.uid]
        self.vol_linear = db_to_lin(self.audio_item.vol + ap_entry.volume)
        self.quantize_offset = 0.0
        self.draw()
        self.set_tooltips()

    def handleDropEvent(self, path):
        menu = QMenu()

        f_replace_item_action = QAction("Replace This Audio Item Only", menu)
        menu.addAction(f_replace_item_action)
        f_replace_item_action.setToolTip(
            'Replace this audio item only with a new audio file.'
        )
        f_replace_item_action.triggered.connect(
            lambda: self.replace_file(path)
        )

        f_replace_seq_action = QAction(
            "Replace All Instances in this Sequencer Item",
            menu,
        )
        menu.addAction(f_replace_seq_action)
        f_replace_seq_action.setToolTip(
            'Replace all instances of this audio file in this sequencer '
            'item with the new audio file.  Other references to this '
            'sequencer item will also be updated'
        )
        f_replace_seq_action.triggered.connect(
            lambda: self.replace_seq_item(path)
        )

        f_replace_all_action = QAction(
            "Replace All Instances in the Entire Project",
            menu,
        )
        menu.addAction(f_replace_all_action)
        f_replace_all_action.setToolTip(
            'Replace all instances of this audio file in all sequencer '
            'items in the entire project with the new audio file'
        )
        f_replace_all_action.triggered.connect(
            lambda: self.replace_project(path)
        )

        # Restore the drag-drop highlighting to normal, avoid item appearing
        # to be selected when it is not
        menu.aboutToHide.connect(lambda: self.set_brush())
        menu.exec(QCursor.pos())

    def replace_file(self, path):
        self.audio_item.uid = constants.PROJECT.get_wav_uid_by_name(path)
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        constants.DAW_PROJECT.commit(_("Replace audio item"))
        global_open_audio_items(True)

    def replace_seq_item(self, path):
        new_uid = constants.PROJECT.get_wav_uid_by_name(path)
        old_uid = self.audio_item.uid
        shared.CURRENT_ITEM.replace_all_audio_file(old_uid, new_uid)
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        constants.DAW_PROJECT.commit(_("Replace audio item"))
        global_open_audio_items(True)

    def replace_project(self, path):
        new_uid = constants.PROJECT.get_wav_uid_by_name(path)
        old_uid = self.audio_item.uid
        constants.DAW_PROJECT.replace_all_audio_file(old_uid, new_uid)
        constants.DAW_PROJECT.commit(_("Replace audio item"))
        shared.CURRENT_ITEM = constants.DAW_PROJECT.get_item_by_uid(
            shared.CURRENT_ITEM.uid,
        )
        global_open_audio_items(True)
        daw_painter_clear_cache()
        global_open_items()

    def draw(self):
        f_temp_seconds = self.sample_length

        if (
            self.audio_item.time_stretch_mode == 1
            and
            self.audio_item.pitch_shift_end == self.audio_item.pitch_shift
        ):
            f_temp_seconds /= pitch_to_ratio(self.audio_item.pitch_shift)
        elif (
            self.audio_item.time_stretch_mode == 2
            and
            self.audio_item.timestretch_amt_end ==
                self.audio_item.timestretch_amt
        ):
            f_temp_seconds *= self.audio_item.timestretch_amt

        f_start = self.audio_item.start_beat
        f_start *= _shared.AUDIO_PX_PER_BEAT

        f_length_seconds = seconds_to_beats(
            f_temp_seconds) * _shared.AUDIO_PX_PER_BEAT
        self.length_seconds_orig_px = f_length_seconds
        self.rect_orig = QtCore.QRectF(
            0.0,
            0.0,
            float(f_length_seconds),
            float(_shared.AUDIO_ITEM_HEIGHT),
        )
        self.length_px_start = (self.audio_item.sample_start *
            0.001 * f_length_seconds)
        self.length_px_minus_start = f_length_seconds - self.length_px_start
        self.length_px_minus_end = (self.audio_item.sample_end *
            0.001 * f_length_seconds)
        f_length = self.length_px_minus_end - self.length_px_start

        f_track_num = (_shared.AUDIO_RULER_HEIGHT +
            _shared.AUDIO_ITEM_HEIGHT * self.audio_item.lane_num)

        f_fade_in = self.audio_item.fade_in * 0.001
        f_fade_out = self.audio_item.fade_out * 0.001
        self.setRect(
            0.0,
            0.0,
            float(f_length),
            float(_shared.AUDIO_ITEM_HEIGHT),
        )
        f_fade_in_handle_pos = (f_length * f_fade_in)
        f_fade_in_handle_pos = clip_value(
            f_fade_in_handle_pos, 0.0, (f_length - 6.0))
        f_fade_out_handle_pos = \
            (f_length * f_fade_out) - shared.AUDIO_ITEM_HANDLE_SIZE
        f_fade_out_handle_pos = clip_value(
            f_fade_out_handle_pos, (f_fade_in_handle_pos + 6.0), f_length)
        self.fade_in_handle.setPos(f_fade_in_handle_pos, 0.0)
        self.fade_out_handle.setPos(f_fade_out_handle_pos, 0.0)
        self.update_fade_in_line()
        self.update_fade_out_line()
        self.setPos(f_start, f_track_num)
        self.is_moving = False
        if (
            self.audio_item.time_stretch_mode >= 3
            or (
                self.audio_item.time_stretch_mode == 2
                and
                self.audio_item.timestretch_amt_end ==
                    self.audio_item.timestretch_amt
            )
        ):
            self.stretch_width_default = \
                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = (self.audio_item.sample_start *
            -0.001 * self.length_seconds_orig_px)

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = (self.start_handle_scene_min +
            self.length_seconds_orig_px)

        if not self.waveforms_scaled:
            f_channels = len(self.painter_paths)
            f_i_inc = 1.0 / f_channels
            f_i = f_i_inc
            f_y_inc = 0.0
            # Kludge to fix the problem, there must be a better way...
            if f_channels == 1:
                f_y_offset = \
                    (1.0 - self.vol_linear) * (_shared.AUDIO_ITEM_HEIGHT * 0.5)
            else:
                f_y_offset = (1.0 - self.vol_linear) * self.y_inc * f_i_inc
            for f_path_item in self.path_items:
                if self.audio_item.reversed:
                    f_path_item.setPos(
                        self.sample_start_offset_px +
                        self.length_seconds_orig_px,
                        self.y_inc + (f_y_offset * -1.0) + (f_y_inc * f_i))
                    f_path_item.setRotation(-180.0)
                else:
                    f_path_item.setPos(
                        self.sample_start_offset_px,
                        f_y_offset + (f_y_inc * f_i))
                f_x_scale, f_y_scale = util.scale_to_rect(
                    AUDIO_ITEM_SCENE_RECT,
                    self.rect_orig,
                )
                f_y_scale *= self.vol_linear
                f_scale_transform = QTransform()
                f_scale_transform.scale(f_x_scale, f_y_scale)
                f_path_item.setTransform(f_scale_transform)
                f_i += f_i_inc
                f_y_inc += self.y_inc
        self.waveforms_scaled = True

        self.length_handle.setPos(
            f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
            _shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0,
            _shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT,
        )
        if (
            self.audio_item.time_stretch_mode not in (0, 1)
            and not (
                self.audio_item.time_stretch_mode == 5  # SBSMS
                and
                self.audio_item.timestretch_amt_end
                !=
                self.audio_item.timestretch_amt
            )
        ):
            self.stretch_handle.show()
            self.stretch_handle.setPos(
                f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
                (
                    _shared.AUDIO_ITEM_HEIGHT * 0.5
                ) - (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            )

    def set_tooltips(self):
        self.start_handle.setToolTip(
            "Use this handle to resize the item by changing the start point."
            "SHIFT+drag to resize freely without quantize"
        )
        self.length_handle.setToolTip(
            "Use this handle to resize the item by changing the end point.  "
            "SHIFT+drag to resize freely without quantize"
        )
        self.fade_in_handle.setToolTip(
            "Use this handle to change the fade in.  See "
            'right-click->Properties->FadeVolume... to adjust the volume the '
            'fades start and end from'
        )
        self.fade_out_handle.setToolTip(
            "Use this handle to change the fade out.  See "
            'right-click->Properties->FadeVolume... to adjust the volume the '
            'fades start and end from'
        )
        self.stretch_handle.setToolTip(
            "Use this handle to resize the item by time-stretching it.  You "
            'can choose a time stretching algorithm by '
            'right-click->Properties->TimestretchMode.  Note that each '
            'algorithm has different properties, and some will be more '
            'time-accurate than others. '
            "SHIFT+drag to stretch without quantize"
        )
        self.setToolTip(sg_strings.AudioSeqItem)

    def clip_at_sequence_end(self):
        f_max_x = shared.CURRENT_ITEM_LEN * _shared.AUDIO_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(
                0.0,
                0.0,
                float(f_end_px),
                float(_shared.AUDIO_ITEM_HEIGHT),
            )
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_seconds_orig_px) * 1000.0
            self.audio_item.sample_end = clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None, override=False):
        if override or self.isSelected():
            self.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_selected_item,
                ),
            )
            self.label.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_audio_label_selected,
                ),
            )
            handle_brush = QColor(
                theme.SYSTEM_COLORS.daw.item_audio_handle_selected,
            )
            for item in (
                self.start_handle,
                self.length_handle,
                self.fade_in_handle,
                self.fade_out_handle,
                self.stretch_handle,
                self.start_handle_line,
                self.length_handle_line,
                self.fade_in_handle_line,
                self.fade_out_handle_line,
                self.stretch_handle_line,
            ):
                item.setPen(handle_brush)

            for item in (
                self.start_handle,
                self.length_handle,
                self.fade_in_handle,
                self.fade_out_handle,
                self.stretch_handle,
            ):
                item.setBrush(handle_brush)
        else:
            self.label.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_audio_label,
                ),
            )
            handle_brush = QColor(
                theme.SYSTEM_COLORS.daw.item_audio_handle,
            )
            for item in (
                self.start_handle,
                self.length_handle,
                self.fade_in_handle,
                self.fade_out_handle,
                self.stretch_handle,
                self.start_handle_line,
                self.length_handle_line,
                self.fade_in_handle_line,
                self.fade_out_handle_line,
                self.stretch_handle_line,
            ):
                item.setPen(handle_brush)

            for item in (
                self.start_handle,
                self.length_handle,
                self.fade_in_handle,
                self.fade_out_handle,
                self.stretch_handle,
            ):
                item.setBrush(handle_brush)

            track_colors = theme.SYSTEM_COLORS.daw.track_default_colors
            if a_index is None:
                i = self.audio_item.lane_num % len(track_colors)
                color = QColor(
                    track_colors[i],
                )
                self.setBrush(color)
            else:
                i = a_index % len(track_colors)
                color = QColor(
                    track_colors[i],
                )
                self.setBrush(color)

    def pos_to_musical_time(self, a_pos):
        return a_pos / _shared.AUDIO_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsPolygonItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
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
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
                    False,
                )

    def fade_in_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsPolygonItem.mousePressEvent(self.fade_in_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_in = True

    def fade_out_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsPolygonItem.mousePressEvent(self.fade_out_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_out = True

    def stretch_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsPolygonItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_sequence_pos = _shared.AUDIO_PX_PER_BEAT * shared.CURRENT_ITEM_LEN
        for f_item in shared.AUDIO_SEQ.audio_items:
            if (
                f_item.isSelected()
                and
                f_item.audio_item.time_stretch_mode >= 2
            ):
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
            shared.AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

    def copy_as_cc_automation(self):
        shared.CC_EDITOR.clipboard = envelope_to_automation(
            self.graph_object,
            True,
            TRANSPORT.tempo_spinbox.value(),
        )

    def copy_as_pb_automation(self):
        shared.PB_EDITOR.clipboard = envelope_to_automation(
            self.graph_object,
            False,
            TRANSPORT.tempo_spinbox.value(),
        )

    def copy_as_notes(self):
        shared.PIANO_ROLL_EDITOR.clipboard = envelope_to_notes(
            self.graph_object,
            TRANSPORT.tempo_spinbox.value(),
        )

    def normalize(self, a_value, audio_pool_by_uid):
        f_val = self.graph_object.normalize(a_value)
        entry = audio_pool_by_uid[self.audio_item.uid]
        entry.volume = f_val
        return entry

    def get_file_path(self):
        return constants.PROJECT.get_wav_path_by_uid(self.audio_item.uid)

    def mousePressEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            shared.AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)
            return

        if a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.AltModifier
        ):
            self.setSelected(not self.isSelected())
            return

        if not self.isSelected():
            shared.AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

        if a_event.button() == QtCore.Qt.MouseButton.RightButton:
            item_context_menu.show(self)
            return

        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            f_item = self.audio_item
            f_item_old = f_item.clone()
            f_item.fade_in = 0.0
            f_item_old.fade_out = 999.0
            f_width_percent = qt_event_pos(a_event).x() / self.rect().width()
            f_item.fade_out = clip_value(
                f_item.fade_out, (f_item.fade_in + 90.0), 999.0, True)
            f_item_old.fade_in /= f_width_percent
            f_item_old.fade_in = clip_value(
                f_item_old.fade_in, 0.0, (f_item_old.fade_out - 90.0), True)

            f_index = shared.CURRENT_ITEM.get_next_index()
            if f_index == -1:
                QMessageBox.warning(
                    glbl_shared.MAIN_WINDOW,
                    _("Error"),
                    _(
                        "No more available audio item slots, max per sequence "
                        "is {}"
                    ).format(MAX_AUDIO_ITEM_COUNT),
                )
                return
            else:
                shared.CURRENT_ITEM.add_item(f_index, f_item_old)
                f_per_item_fx = shared.CURRENT_ITEM.get_row(self.track_num)
                if f_per_item_fx is not None:
                    shared.CURRENT_ITEM.set_row(f_index, f_per_item_fx)

            f_event_pos = qt_event_pos(a_event).x()
            # for items that are not quantized
            f_pos = f_event_pos - (f_event_pos - _shared.quantize(f_event_pos))
            f_scene_pos = _shared.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(f_scene_pos)
            f_sample_shown = f_item.sample_end - f_item.sample_start
            f_sample_rect_pos = f_pos / self.rect().width()
            f_item.sample_start = \
                (f_sample_rect_pos * f_sample_shown) + f_item.sample_start
            f_item.sample_start = clip_value(
                f_item.sample_start, 0.0, 999.0, True)
            f_item.start_beat = f_musical_pos
            f_item_old.sample_end = f_item.sample_start
            item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            constants.DAW_PROJECT.commit(_("Split audio item"))
            global_open_audio_items(True)
        elif a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.ControlModifier
            |
            QtCore.Qt.KeyboardModifier.AltModifier
        ):
            self.is_amp_dragging = True
        elif a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.ControlModifier
            |
            QtCore.Qt.KeyboardModifier.ShiftModifier
        ):
            self.is_amp_curving = True
            f_list = [((x.audio_item.start_bar * 4.0) +
                x.audio_item.start_beat)
                for x in shared.AUDIO_SEQ.audio_items if x.isSelected()]
            f_list.sort()
            self.vc_start = f_list[0]
            self.vc_mid = (self.audio_item.start_bar *
                4.0) + self.audio_item.start_beat
            self.vc_end = f_list[-1]
        elif a_event.modifiers() == (
            QtCore.Qt.KeyboardModifier.AltModifier
            |
            QtCore.Qt.KeyboardModifier.ShiftModifier
        ):
            self.is_amp_dragging_audio_pool = True
        else:
            QGraphicsRectItem.mousePressEvent(self, a_event)
            QApplication.setOverrideCursor(QtCore.Qt.CursorShape.BlankCursor)
            self.event_pos_orig = qt_event_pos(a_event).x()
            lanes = []
            start_beats = []
            for f_item in shared.AUDIO_SEQ.get_selected():
                f_item.orig_pos_x = f_item.pos().x()
                start_beats.append(f_item.audio_item.start_beat)
                lanes.append(f_item.audio_item.lane_num)
                f_item.setZValue(2400.0)
                f_item_pos = f_item.pos().x()
                f_item.quantize_offset = \
                    f_item_pos - _shared.quantize_all(f_item_pos)
                if a_event.modifiers() == (
                    QtCore.Qt.KeyboardModifier.ControlModifier
                ):
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    f_item.per_item_fx = shared.CURRENT_ITEM.get_row(
                        f_item.track_num,
                    )
                    shared.AUDIO_SEQ.draw_item(
                        f_item.track_num,
                        f_item.audio_item,
                        f_item.graph_object,
                    )
                if self.is_fading_out:
                    f_item.fade_orig_pos = f_item.fade_out_handle.pos().x()
                elif self.is_fading_in:
                    f_item.fade_orig_pos = f_item.fade_in_handle.pos().x()
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()
                self._max_lane = (
                    _shared.AUDIO_ITEM_MAX_LANE +
                    (self.audio_item.lane_num - max(lanes))
                ) - 1
                self._min_lane = self.audio_item.lane_num - min(lanes)
                self._max_beat = (
                    shared.CURRENT_ITEM_LEN +
                    (self.audio_item.start_beat - max(start_beats))
                )
                self._min_beat = self.audio_item.start_beat - min(start_beats)
        if (
            self.is_amp_curving
            or
            self.is_amp_dragging
            or
            self.is_amp_dragging_audio_pool
        ):
            a_event.setAccepted(True)
            self.setSelected(True)
            self.event_pos_orig = qt_event_pos(a_event).x()
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = qt_event_pos(a_event).y()
            if self.is_amp_dragging_audio_pool:
                self._audio_pool = constants.PROJECT.get_audio_pool()
                self._audio_pool_by_uid = self._audio_pool.by_uid()
                # De-duplication, multiple selected items could have the
                # same audio file
                self._audio_pool_selected_uids = set()
                for f_item in shared.AUDIO_SEQ.get_selected():
                    self._audio_pool_selected_uids.add(f_item.audio_item.uid)
                    entry = self._audio_pool_by_uid[f_item.audio_item.uid]
                    f_item.orig_value = entry.volume
                    f_item.add_vol_line(f_item.orig_value)
            else:
                for f_item in shared.AUDIO_SEQ.get_selected():
                    f_item.orig_value = f_item.audio_item.vol
                    f_item.add_vol_line(f_item.orig_value)

    def hoverEnterEvent(self, a_event):
        shared.set_move_cursor()
        f_item_pos = self.pos().x()
        self.quantize_offset = f_item_pos - _shared.quantize_all(f_item_pos)
        super().hoverEnterEvent(a_event)

    def hoverMoveEvent(self, a_event):
        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            if not self.split_line_is_shown:
                self.split_line_is_shown = True
                self.split_line.show()
            f_x = qt_event_pos(a_event).x()
            f_x = _shared.quantize_all(f_x)
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

    def update_fade_in_line(self):
        f_pos = self.fade_in_handle.pos()
        self.fade_in_handle_line.setLine(
            f_pos.x(), 0.0, 0.0, _shared.AUDIO_ITEM_HEIGHT)

    def update_fade_out_line(self):
        f_pos = self.fade_out_handle.pos()
        self.fade_out_handle_line.setLine(
            f_pos.x() + shared.AUDIO_ITEM_HANDLE_SIZE, 0.0,
            self.rect().width(), _shared.AUDIO_ITEM_HEIGHT)

    def add_vol_line(self, vol):
        self.vol_line = QGraphicsLineItem(
            0.0,
            0.0,
            self.rect().width(),
            0.0,
            self,
        )
        self.vol_line.setPen(
            QPen(
                QColor(theme.SYSTEM_COLORS.daw.item_audio_vol_line),
                2.0,
            ),
        )
        self.set_vol_line(vol)

    def set_vol_line(self, vol):
        f_pos = (float(48 - (vol + 24))
            * 0.020833333) * _shared.AUDIO_ITEM_HEIGHT # 1.0 / 48.0
        self.vol_line.setPos(0, f_pos)
        self.label.setText(f"{vol}dB")

    def quantize_end(self, a_event, event_diff):
        """ Quantize the item length.  Allows the end to resize to the full
            length of the item unquantized
        """
        is_shift = bool(
            a_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        x = self.width_orig + event_diff + self.quantize_offset
        x = clip_value(
            x,
            shared.AUDIO_ITEM_HANDLE_SIZE,
            self.length_px_minus_start,
        )
        if not is_shift and x < self.length_px_minus_start:
            x = _shared.quantize(x)
            x -= self.quantize_offset
        return x

    def _mm_resize(self, a_event):
        f_event_diff = self._mm_event_diff(a_event)
        for item in shared.AUDIO_SEQ.audio_items:
            if item.isSelected():
                x = item.quantize_end(a_event, f_event_diff)
                item.length_handle.setPos(
                    x - shared.AUDIO_ITEM_HANDLE_SIZE,
                    _shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT,
                )

    def _mm_start_resize(self, a_event):
        f_event_diff = self._mm_event_diff(a_event)
        is_shift = bool(
            a_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = clip_value(
                    f_x,
                    f_item.sample_start_offset_px,
                    f_item.length_handle.pos().x(),
                )
                f_x = clip_min(f_x, f_item.min_start)
                if not is_shift and f_x > f_item.min_start:
                    f_x = _shared.quantize_start(
                        f_x,
                        f_item.length_handle.pos().x(),
                    )
                    f_x -= f_item.quantize_offset
                f_item.start_handle.setPos(
                    f_x,
                    _shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT,
                )

    def _mm_fade_in(self, a_event):
        f_event_diff = self._mm_event_diff(a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                #f_x = f_event_pos #f_item.width_orig + f_event_diff
                f_x = f_item.fade_orig_pos + f_event_diff
                f_x = clip_value(
                    f_x,
                    0.0,
                    f_item.fade_out_handle.pos().x() - 4.0,
                )
                f_item.fade_in_handle.setPos(f_x, 0.0)
                f_item.update_fade_in_line()

    def _mm_fade_out(self, a_event):
        f_event_diff = self._mm_event_diff(a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_x = f_item.fade_orig_pos + f_event_diff
                f_x = clip_value(
                    f_x,
                    f_item.fade_in_handle.pos().x() + 4.0,
                    f_item.width_orig - shared.AUDIO_ITEM_HANDLE_SIZE,
                )
                f_item.fade_out_handle.setPos(f_x, 0.0)
                f_item.update_fade_out_line()

    def _mm_stretch(self, a_event):
        is_shift = bool(
            a_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        f_event_diff = self._mm_event_diff(a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if (
                f_item.isSelected()
                and
                f_item.audio_item.time_stretch_mode >= 2
            ):
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = clip_value(
                    f_x,
                    f_item.stretch_width_default * 0.1,
                    f_item.stretch_width_default * 200.0,
                )
                f_x = clip_max(f_x, f_item.max_stretch)
                if not is_shift:
                    f_x = _shared.quantize(f_x)
                f_x -= f_item.quantize_offset
                f_item.stretch_handle.setPos(
                    f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                    (_shared.AUDIO_ITEM_HEIGHT * 0.5) -
                    (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
                )

    def _mm_vol_val(self, a_event):
        f_pos = qt_event_pos(a_event)
        f_y = f_pos.y()
        f_diff_y = self.orig_y - f_y
        f_val = (f_diff_y * 0.05)
        return f_val

    def _mm_item_vol(self, a_event):
        f_val = self._mm_vol_val(a_event)
        for f_item in shared.AUDIO_SEQ.get_selected():
            new_vol = clip_value(
                f_val + f_item.orig_value,
                -24.0,
                24.0,
            )
            new_vol = round(new_vol, 1)
            f_item.audio_item.vol = new_vol
            f_item.set_vol_line(new_vol)

    def _mm_ap_vol(self, a_event):
        f_val = self._mm_vol_val(a_event)
        for f_item in shared.AUDIO_SEQ.get_selected():
            new_vol = clip_value(
                f_val + f_item.orig_value,
                -24.0,
                24.0,
            )
            new_vol = round(new_vol, 1)
            ap_entry = self._audio_pool_by_uid[f_item.audio_item.uid]
            ap_entry.volume = new_vol
            f_item.set_vol_line(new_vol)

    def _mm_line_vol(self, a_event):
        f_val = self._mm_vol_val(a_event)
        shared.AUDIO_SEQ.setUpdatesEnabled(False)
        for f_item in shared.AUDIO_SEQ.get_selected():
            f_start = ((f_item.audio_item.start_bar * 4.0) +
                f_item.audio_item.start_beat)
            if f_start == self.vc_mid:
                new_vol = f_val + f_item.orig_value
            else:
                if f_start > self.vc_mid:
                    f_frac =  (f_start -
                        self.vc_mid) / (self.vc_end - self.vc_mid)
                    new_vol = linear_interpolate(
                        f_val, 0.3 * f_val, f_frac)
                else:
                    f_frac = (f_start -
                        self.vc_start) / (self.vc_mid - self.vc_start)
                    new_vol = linear_interpolate(
                        0.3 * f_val, f_val, f_frac)
                new_vol += f_item.orig_value
            new_vol = clip_value(new_vol, -24.0, 24.0)
            new_vol = round(new_vol, 1)
            f_item.audio_item.vol = new_vol
            f_item.set_vol_line(new_vol)
        shared.AUDIO_SEQ.setUpdatesEnabled(True)
        shared.AUDIO_SEQ.update()

    def _mm_else(self, a_event):
        QGraphicsRectItem.mouseMoveEvent(self, a_event)
        is_shift = bool(
            a_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        if _shared.AUDIO_QUANTIZE and not is_shift:
            max_x = (
                self._max_beat * _shared.AUDIO_PX_PER_BEAT
            ) - _shared.AUDIO_QUANTIZE_PX
        else:
            max_x = (
                self._max_beat * _shared.AUDIO_PX_PER_BEAT
            ) - shared.AUDIO_ITEM_HANDLE_SIZE
        min_x = self._min_beat * _shared.AUDIO_PX_PER_BEAT
        pos_x = self.pos().x()
        pos_x = clip_value(pos_x, min_x, max_x)
        if not is_shift:
            pos_x = _shared.quantize_all(pos_x)
        pos_x_offset = pos_x - self.orig_pos_x
        new_lane = clip_value(
            _shared.y_to_lane(a_event.scenePos().y()),
            self._min_lane,
            self._max_lane,
        )
        lane_offset = new_lane - self.audio_item.lane_num
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_pos_x = f_item.orig_pos_x + pos_x_offset
                f_pos_y = _shared.lane_to_y(
                    lane_offset + f_item.audio_item.lane_num,
                )
                f_item.setPos(f_pos_x, f_pos_y)
                if not f_item.is_moving:
                    f_item.setGraphicsEffect(
                        QGraphicsOpacityEffect(),
                    )
                    f_item.is_moving = True

    def _mm_event_diff(self, a_event):
        f_event_pos = qt_event_pos(a_event).x()
        f_event_diff = f_event_pos - self.event_pos_orig
        return f_event_diff

    def mouseMoveEvent(self, a_event):
        if glbl_shared.IS_PLAYING or self.event_pos_orig is None:
            return
        if self.is_resizing:
            self._mm_resize(a_event)
        elif self.is_start_resizing:
            self._mm_start_resize(a_event)
        elif self.is_fading_in:
            self._mm_fade_in(a_event)
        elif self.is_fading_out:
            self._mm_fade_out(a_event)
        elif self.is_stretching:
            self._mm_stretch(a_event)
        elif self.is_amp_dragging:
            self._mm_item_vol(a_event)
        elif self.is_amp_dragging_audio_pool:
            self._mm_ap_vol(a_event)
        elif self.is_amp_curving:
            self._mm_line_vol(a_event)
        else:
            self._mm_else(a_event)

    def mouseReleaseEvent(self, a_event):
        if glbl_shared.IS_PLAYING or self.event_pos_orig is None:
            return
        is_shift = bool(
            a_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        QApplication.restoreOverrideCursor()
        f_audio_items = shared.CURRENT_ITEM
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_event_pos = qt_event_pos(a_event).x()
        f_event_diff = f_event_pos - self.event_pos_orig

        for f_audio_item in shared.AUDIO_SEQ.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = f_audio_item.pos().x()
            if f_audio_item.is_resizing:
                x = f_audio_item.quantize_end(a_event, f_event_diff)
                f_audio_item.setRect(
                    0.0,
                    0.0,
                    float(x),
                    float(_shared.AUDIO_ITEM_HEIGHT),
                )
                f_item.sample_end = (
                    (
                        f_audio_item.rect().width()
                        +
                        f_audio_item.length_px_start
                    ) / f_audio_item.length_seconds_orig_px
                ) * 1000.0
                f_item.sample_end = clip_value(
                    f_item.sample_end,
                    1.0,
                    1000.0,
                    True,
                )
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = clip_min(f_x, 0.0)
                if not is_shift:
                    f_x = _shared.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_start_result = self.pos_to_musical_time(f_x)
                f_item.start_beat = f_start_result
                f_item.sample_start = (
                    (f_x - f_audio_item.start_handle_scene_min)
                    /
                    (
                        f_audio_item.start_handle_scene_max
                        -
                        f_audio_item.start_handle_scene_min
                    )
                ) * 1000.0
                f_item.sample_start = clip_value(
                    f_item.sample_start, 0.0, 999.0, True)
            elif f_audio_item.is_fading_in:
                f_pos = f_audio_item.fade_in_handle.pos().x()
                f_val = (f_pos / f_audio_item.rect().width()) * 1000.0
                f_item.fade_in = clip_value(f_val, 0.0, 997.0, True)
            elif f_audio_item.is_fading_out:
                f_pos = f_audio_item.fade_out_handle.pos().x()
                f_val = ((f_pos + shared.AUDIO_ITEM_HANDLE_SIZE) /
                    (f_audio_item.rect().width())) * 1000.0
                f_item.fade_out = clip_value(f_val, 1.0, 998.0, True)
            elif (
                f_audio_item.is_stretching
                and
                f_item.time_stretch_mode >= 2
            ):
                f_reset_selection = True
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = clip_value(
                    f_x,
                    f_audio_item.stretch_width_default * 0.1,
                    f_audio_item.stretch_width_default * 200.0,
                )
                f_x = clip_max(f_x, f_audio_item.max_stretch)
                if not is_shift:
                    f_x = _shared.quantize(f_x)
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
                    try:
                        constants.PROJECT.timestretch_audio_item(f_item)
                    except FileNotFoundError as ex:
                        QMessageBox.warning(
                            glbl_shared.MAIN_WINDOW,
                            _("Error"),
                            str(ex),
                        )
                        global_open_audio_items(f_reset_selection)
                        return
                f_audio_item.setRect(
                    0.0,
                    0.0,
                    float(f_x),
                    float(_shared.AUDIO_ITEM_HEIGHT),
                )
            elif (
                self.is_amp_curving
                or
                self.is_amp_dragging
                or
                self.is_amp_dragging_audio_pool
            ):
                f_did_change = True
            else:
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    f_index = f_audio_items.get_next_index()
                    if f_index == -1:
                        QMessageBox.warning(
                            glbl_shared.MAIN_WINDOW,
                            _("Error"),
                            _("No more available audio item slots, max per "
                            "sequence is {}").format(MAX_AUDIO_ITEM_COUNT)
                        )
                        break
                    else:
                        f_audio_items.add_item(f_index, f_item_old)
                        if f_audio_item.per_item_fx is not None:
                            shared.CURRENT_ITEM.set_row(
                                f_index,
                                f_audio_item.per_item_fx,
                            )
                else:
                    f_audio_item.set_brush(f_item.lane_num)
                #f_pos_x = _shared.quantize_all(f_pos_x)
                f_item.lane_num = _shared.y_to_lane(f_pos_y)
                #f_pos_y = _shared.lane_to_y(f_item.lane_num)
                #f_audio_item.setPos(f_pos_x, f_pos_y)
                f_start_result = f_audio_item.pos_to_musical_time(f_pos_x)
                f_item.set_pos(0, f_start_result)
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
        if f_did_change:
            f_audio_items.deduplicate_items()
            if self.is_amp_dragging_audio_pool:
                constants.PROJECT.save_audio_pool(self._audio_pool)
                for uid in self._audio_pool_selected_uids:
                    vol = self._audio_pool_by_uid[uid].volume
                    constants.IPC.audio_pool_entry_volume(uid, vol)
                self._audio_pool_selected_uids = None
                self._audio_pool = None
                self._audio_pool_by_uid = None
                # Any item containing this file now has an inaccurate
                # waveform, so take the brute force approach and force
                # everything to redraw
                daw_painter_path.clear_caches()
            elif f_was_stretching:
                constants.PROJECT.save_stretch_dicts()
            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )
            constants.DAW_PROJECT.commit(_("Update audio items"))
        global_open_audio_items(f_reset_selection)


