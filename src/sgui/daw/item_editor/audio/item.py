from sglib.models.daw import *
from sgui.daw.shared import *
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


PAINTER_PATH_CACHE = {}

class AudioSeqItemHandle(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)
        self.setRect(
            QtCore.QRectF(
                0.0,
                0.0,
                float(shared.AUDIO_ITEM_HANDLE_SIZE),
                float(shared.AUDIO_ITEM_HANDLE_HEIGHT),
            ),
        )


    def hoverEnterEvent(self, a_event):
        QApplication.setOverrideCursor(
            QtCore.Qt.CursorShape.SizeHorCursor,
        )
        super().hoverEnterEvent(a_event)

    def hoverLeaveEvent(self, a_event):
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
        if f_uid in PAINTER_PATH_CACHE:
            self.painter_paths = PAINTER_PATH_CACHE[f_uid]
        else:
            self.painter_paths = create_sample_graph(
                a_graph,
                True,
            )
            PAINTER_PATH_CACHE[f_uid] = self.painter_paths

        self.y_inc = shared.AUDIO_ITEM_HEIGHT / len(self.painter_paths)
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

        self.start_handle = AudioSeqItemHandle(parent=self)
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            0.0,
            (
                shared.AUDIO_ITEM_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle,
        )

        self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

        self.length_handle = AudioSeqItemHandle(parent=self)
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE, shared.AUDIO_ITEM_HANDLE_HEIGHT,
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (shared.AUDIO_ITEM_HEIGHT * -1.0) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.fade_in_handle = AudioSeqItemHandle(parent=self)
        self.fade_in_handle.mousePressEvent = \
            self.fade_in_handle_mouseClickEvent
        self.fade_in_handle_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            0.0,
            self,
        )

        self.fade_out_handle = AudioSeqItemHandle(parent=self)
        self.fade_out_handle.mousePressEvent = \
            self.fade_out_handle_mouseClickEvent
        self.fade_out_handle_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            0.0,
            self,
        )

        self.stretch_handle = AudioSeqItemHandle(parent=self)
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5
            ) - (shared.AUDIO_ITEM_HEIGHT * 0.5),
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.AUDIO_ITEM_HEIGHT * 0.5
            ) + (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle,
        )
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            shared.AUDIO_ITEM_HEIGHT,
            self,
        )
        self.split_line.mapFromParent(0.0, 0.0)
        self.split_line.hide()
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
        f_start *= shared.AUDIO_PX_PER_BEAT

        f_length_seconds = seconds_to_beats(
            f_temp_seconds) * shared.AUDIO_PX_PER_BEAT
        self.length_seconds_orig_px = f_length_seconds
        self.rect_orig = QtCore.QRectF(
            0.0,
            0.0,
            float(f_length_seconds),
            float(shared.AUDIO_ITEM_HEIGHT),
        )
        self.length_px_start = (self.audio_item.sample_start *
            0.001 * f_length_seconds)
        self.length_px_minus_start = f_length_seconds - self.length_px_start
        self.length_px_minus_end = (self.audio_item.sample_end *
            0.001 * f_length_seconds)
        f_length = self.length_px_minus_end - self.length_px_start

        f_track_num = (shared.AUDIO_RULER_HEIGHT +
            shared.AUDIO_ITEM_HEIGHT * self.audio_item.lane_num)

        f_fade_in = self.audio_item.fade_in * 0.001
        f_fade_out = self.audio_item.fade_out * 0.001
        self.setRect(
            0.0,
            0.0,
            float(f_length),
            float(shared.AUDIO_ITEM_HEIGHT),
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
                    (1.0 - self.vol_linear) * (shared.AUDIO_ITEM_HEIGHT * 0.5)
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
            shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0,
            shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT,
        )
        if (
            self.audio_item.time_stretch_mode >= 2
            and (
                    self.audio_item.time_stretch_mode != 5
                    and
                    self.audio_item.time_stretch_mode != 2
            ) or (
                self.audio_item.timestretch_amt_end ==
                    self.audio_item.timestretch_amt
            )
        ):
            self.stretch_handle.show()
            self.stretch_handle.setPos(
                f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
                (
                    shared.AUDIO_ITEM_HEIGHT * 0.5
                ) - (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            )

    def set_tooltips(self):
        self.start_handle.setToolTip(
            _("Use this handle to resize the item by changing "
            "the start point."))
        self.length_handle.setToolTip(
            _("Use this handle to resize the item by "
            "changing the end point."))
        self.fade_in_handle.setToolTip(
            _("Use this handle to change the fade in."))
        self.fade_out_handle.setToolTip(
            _("Use this handle to change the fade out."))
        self.stretch_handle.setToolTip(
            _("Use this handle to resize the item by "
            "time-stretching it."))
        self.setToolTip(sg_strings.AudioSeqItem)

    def clip_at_sequence_end(self):
        f_max_x = shared.CURRENT_ITEM_LEN * shared.AUDIO_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(
                0.0,
                0.0,
                float(f_end_px),
                float(shared.AUDIO_ITEM_HEIGHT),
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

    def set_brush(self, a_index=None):
        if self.isSelected():
            self.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_selected_item,
                ),
            )
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_in_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_out_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_in_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_out_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_audio_label_selected,
                ),
            )
            handle_brush = QColor(
                theme.SYSTEM_COLORS.daw.item_audio_handle_selected,
            )
            self.start_handle.setBrush(handle_brush)
            self.length_handle.setBrush(handle_brush)
            self.fade_in_handle.setBrush(handle_brush)
            self.fade_out_handle.setBrush(handle_brush)
            self.stretch_handle.setBrush(handle_brush)
        else:
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.fade_in_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.fade_out_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(shared.AUDIO_ITEM_HANDLE_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.fade_in_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.fade_out_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_audio_label,
                ),
            )
            handle_brush = QColor(
                theme.SYSTEM_COLORS.daw.item_audio_handle,
            )
            self.start_handle.setBrush(handle_brush)
            self.length_handle.setBrush(handle_brush)
            self.fade_in_handle.setBrush(handle_brush)
            self.fade_out_handle.setBrush(handle_brush)
            self.stretch_handle.setBrush(handle_brush)
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
        return a_pos / shared.AUDIO_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
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
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
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
        QGraphicsRectItem.mousePressEvent(self.fade_in_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_in = True

    def fade_out_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.fade_out_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_out = True

    def stretch_handle_mouseClickEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_sequence_pos = shared.AUDIO_PX_PER_BEAT * shared.CURRENT_ITEM_LEN
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

    def set_paif_for_all_instance(self):
        f_paif = constants.DAW_PROJECT.get_audio_per_item_fx_sequence(
            shared.CURRENT_SEQUENCE.uid,
        )
        f_paif_row = f_paif.get_row(self.track_num)
        constants.DAW_PROJECT.set_paif_for_all_audio_items(
            self.audio_item.uid, f_paif_row)

    def set_fades_for_all_instances(self):
        constants.DAW_PROJECT.set_fades_for_all_audio_items(self.audio_item)
        global_open_audio_items()

    def set_vol_for_all_instances(self):
        def ok_handler():
            f_index = f_reverse_combobox.currentIndex()
            f_reverse_val = None
            if f_index == 1:
                f_reverse_val = False
            elif f_index == 2:
                f_reverse_val = True
            constants.DAW_PROJECT.set_vol_for_all_audio_items(
                self.audio_item.uid, get_vol(), f_reverse_val,
                f_same_vol_checkbox.isChecked(), self.audio_item.vol)
            f_dialog.close()
            global_open_audio_items()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            f_vol_label.setText("{}dB".format(get_vol()))

        def get_vol():
            return round(f_vol_slider.value() * 0.1, 1)

        f_dialog = QDialog(shared.MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        f_vol_slider = QSlider(QtCore.Qt.Orientation.Vertical)
        f_vol_slider.setRange(-240, 240)
        f_vol_slider.setMinimumHeight(360)
        f_vol_slider.valueChanged.connect(vol_changed)
        f_layout.addWidget(
            f_vol_slider,
            0,
            1,
            QtCore.Qt.AlignmentFlag.AlignCenter,
        )
        f_vol_label = QLabel("0dB")
        f_layout.addWidget(f_vol_label, 1, 1)
        f_vol_slider.setValue(int(self.audio_item.vol))
        f_reverse_combobox = QComboBox()
        f_reverse_combobox.addItems(
            [_("Either"), _("Not-Reversed"), _("Reversed")])
        f_reverse_combobox.setMinimumWidth(105)
        f_layout.addWidget(QLabel(_("Reversed Items?")), 2, 0)
        f_layout.addWidget(f_reverse_combobox, 2, 1)
        f_same_vol_checkbox = QCheckBox(
            _("Only items with same volume?"))
        f_layout.addWidget(f_same_vol_checkbox, 3, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 1)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def normalize(self, a_value, audio_pool_by_uid):
        f_val = self.graph_object.normalize(a_value)
        entry = audio_pool_by_uid[self.audio_item.uid]
        entry.volume = f_val
        return entry

    def get_file_path(self):
        return constants.PROJECT.get_wav_path_by_uid(self.audio_item.uid)

    def mousePressEvent(self, a_event):
        if glbl_shared.IS_PLAYING:
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
            f_pos = f_event_pos - (f_event_pos - self.quantize(f_event_pos))
            f_scene_pos = self.quantize(a_event.scenePos().x())
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
            self.event_pos_orig = qt_event_pos(a_event).x()
            for f_item in shared.AUDIO_SEQ.get_selected():
                f_item.setZValue(2400.0)
                f_item_pos = f_item.pos().x()
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == (
                    QtCore.Qt.KeyboardModifier.ControlModifier
                ):
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    f_item.per_item_fx = shared.CURRENT_ITEM.get_row(
                        f_item.track_num)
                    shared.AUDIO_SEQ.draw_item(
                        f_item.track_num, f_item.audio_item,
                        f_item.graph_object)
                if self.is_fading_out:
                    f_item.fade_orig_pos = f_item.fade_out_handle.pos().x()
                elif self.is_fading_in:
                    f_item.fade_orig_pos = f_item.fade_in_handle.pos().x()
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()
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
            QApplication.setOverrideCursor(QtCore.Qt.CursorShape.BlankCursor)
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
        if self.split_line_is_shown:
            self.split_line_is_shown = False
            self.split_line.hide()
        super().hoverLeaveEvent(a_event)

    def y_pos_to_lane_number(self, a_y_pos):
        f_lane_num = int((a_y_pos - shared.AUDIO_RULER_HEIGHT) / shared.AUDIO_ITEM_HEIGHT)
        f_lane_num = clip_value(
            f_lane_num, 0, shared.AUDIO_ITEM_MAX_LANE)
        f_y_pos = (f_lane_num * shared.AUDIO_ITEM_HEIGHT) + shared.AUDIO_RULER_HEIGHT
        return f_lane_num, f_y_pos

    def lane_number_to_y_pos(self, a_lane_num):
        a_lane_num = clip_value(
            a_lane_num,
            0,
            TRACK_COUNT_ALL,
        )
        return (a_lane_num * shared.AUDIO_ITEM_HEIGHT) + shared.AUDIO_RULER_HEIGHT

    def quantize_all(self, a_x):
        f_x = a_x
        if shared.AUDIO_QUANTIZE:
            f_x = round(f_x / shared.AUDIO_QUANTIZE_PX) * shared.AUDIO_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if shared.AUDIO_QUANTIZE and f_x < shared.AUDIO_QUANTIZE_PX:
            f_x = shared.AUDIO_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= shared.AUDIO_QUANTIZE_PX
        return f_x

    def quantize_scene(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        return f_x

    def update_fade_in_line(self):
        f_pos = self.fade_in_handle.pos()
        self.fade_in_handle_line.setLine(
            f_pos.x(), 0.0, 0.0, shared.AUDIO_ITEM_HEIGHT)

    def update_fade_out_line(self):
        f_pos = self.fade_out_handle.pos()
        self.fade_out_handle_line.setLine(
            f_pos.x() + shared.AUDIO_ITEM_HANDLE_SIZE, 0.0,
            self.rect().width(), shared.AUDIO_ITEM_HEIGHT)

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
            * 0.020833333) * shared.AUDIO_ITEM_HEIGHT # 1.0 / 48.0
        self.vol_line.setPos(0, f_pos)
        self.label.setText(f"{vol}dB")

    def _mm_resize(self, a_event):
        f_event_diff = self._mm_event_diff(a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = clip_value(
                    f_x, shared.AUDIO_ITEM_HANDLE_SIZE,
                    f_item.length_px_minus_start)
                if f_x < f_item.length_px_minus_start:
                    f_x = f_item.quantize(f_x)
                    f_x -= f_item.quantize_offset
                f_item.length_handle.setPos(
                    f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                    shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT,
                )

    def _mm_start_resize(self, a_event):
        f_event_diff = self._mm_event_diff(a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
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
                    f_x,
                    shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT,
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
                f_x = f_item.quantize(f_x)
                f_x -= f_item.quantize_offset
                f_item.stretch_handle.setPos(
                    f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                    (shared.AUDIO_ITEM_HEIGHT * 0.5) -
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
        if shared.AUDIO_QUANTIZE:
            f_max_x = (shared.CURRENT_ITEM_LEN *
                shared.AUDIO_PX_PER_BEAT) - shared.AUDIO_QUANTIZE_PX
        else:
            f_max_x = (shared.CURRENT_ITEM_LEN *
                shared.AUDIO_PX_PER_BEAT) - shared.AUDIO_ITEM_HANDLE_SIZE
        f_new_lane, f_ignored = self.y_pos_to_lane_number(
            a_event.scenePos().y(),
        )
        f_lane_offset = f_new_lane - self.audio_item.lane_num
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_pos_x = f_item.pos().x()
                f_pos_x = clip_value(f_pos_x, 0.0, f_max_x)
                f_pos_x = f_item.quantize_scene(f_pos_x)
                f_pos_y = self.lane_number_to_y_pos(
                    f_lane_offset + f_item.audio_item.lane_num,
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
                f_x = (
                    f_audio_item.width_orig
                    +
                    f_event_diff
                    +
                    f_audio_item.quantize_offset
                )
                f_x = clip_value(
                    f_x,
                    shared.AUDIO_ITEM_HANDLE_SIZE,
                    f_audio_item.length_px_minus_start,
                )
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(
                    0.0,
                    0.0,
                    float(f_x),
                    float(shared.AUDIO_ITEM_HEIGHT),
                )
                f_item.sample_end = (
                    (
                        f_audio_item.rect().width()
                        +
                        f_audio_item.length_px_start
                    ) / f_audio_item.length_seconds_orig_px
                ) * 1000.0
                f_item.sample_end = clip_value(
                    f_item.sample_end, 1.0, 1000.0, True)
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
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
                    float(shared.AUDIO_ITEM_HEIGHT),
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
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.lane_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
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


