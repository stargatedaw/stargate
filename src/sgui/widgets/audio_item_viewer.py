from . import _shared
from sglib.math import clip_max, clip_min, clip_value
from sglib.lib import util
from sglib.lib.translate import _
from sglib.models import theme
from sgui.shared import (
    AUDIO_ITEM_SCENE_HEIGHT,
    AUDIO_ITEM_SCENE_WIDTH,
)
from sgui.sgqt import *
from sgui.widgets.sample_graph import create_sample_graph

AUDIO_ITEM_END_MARKER_MIN_VAL = 6.0
AUDIO_ITEM_MAX_MARKER_VAL = 1000.0
AUDIO_ITEM_PX_TO_VAL = AUDIO_ITEM_MAX_MARKER_VAL / AUDIO_ITEM_SCENE_WIDTH
AUDIO_ITEM_SCENE_WIDTH_RECIP = 1.0 / AUDIO_ITEM_SCENE_WIDTH
AUDIO_ITEM_START_MARKER_MAX_VAL = 994.0
AUDIO_ITEM_VAL_TO_PX = AUDIO_ITEM_SCENE_WIDTH / AUDIO_ITEM_MAX_MARKER_VAL
AUDIO_MARKERS_CLIPBOARD = None
FADE_PEN = QPen(QColor.fromRgb(246, 30, 30), 6.0)
MARKER_MIN_DIFF = 1.0
START_END_GRADIENT = QLinearGradient(0.0, 0.0, 66.0, 66.0)
START_END_GRADIENT.setColorAt(0.0, QColor.fromRgb(246, 30, 30))
START_END_GRADIENT.setColorAt(1.0, QColor.fromRgb(226, 42, 42))
START_END_PEN = QPen(QColor.fromRgb(246, 30, 30), 12.0)


def global_set_audio_markers_clipboard(
    a_s,
    a_e,
    a_fi,
    a_fo,
    a_ls=0.0,
    a_le=1000.0,
):
    global AUDIO_MARKERS_CLIPBOARD
    AUDIO_MARKERS_CLIPBOARD = (a_s, a_e, a_fi, a_fo, a_ls, a_le)

class audio_marker_widget(QGraphicsRectItem):
    mode_start_end = 0
    mode_loop = 1
    def __init__(self, a_type, a_val, a_pen, a_brush, a_label, a_graph_object,
                 a_marker_mode, a_offset=0, a_callback=None):
        """ a_type:  0 == start, 1 == end, more types eventually... """
        self.audio_item_marker_height = 66.0
        QGraphicsRectItem.__init__(
            self,
            0.,
            0.,
            float(self.audio_item_marker_height),
            float(self.audio_item_marker_height),
        )
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.callback = a_callback
        self.graph_object = a_graph_object
        self.line = QGraphicsLineItem(
            0.0, 0.0, 0.0, AUDIO_ITEM_SCENE_HEIGHT)
        self.line.setParentItem(self)
        self.line.setPen(a_pen)
        self.marker_type = a_type
        self.marker_mode = a_marker_mode
        self.pos_x = 0.0
        self.max_x = \
            AUDIO_ITEM_SCENE_WIDTH - self.audio_item_marker_height
        self.value = a_val
        self.other = None
        self.fade_marker = None
        self.offset = a_offset
        if a_type == 0:
            self.min_x = 0.0
            self.y_pos = 0.0 + (a_offset * self.audio_item_marker_height)
            self.line.setPos(0.0, self.y_pos * -1.0)
        elif a_type == 1:
            self.min_x = 66.0
            self.y_pos = \
                AUDIO_ITEM_SCENE_HEIGHT - \
                self.audio_item_marker_height - \
                (a_offset * self.audio_item_marker_height)
            self.line.setPos(self.audio_item_marker_height, self.y_pos * -1.0)
        self.setPen(a_pen)
        self.setBrush(a_brush)
        self.text_item = QGraphicsTextItem(a_label)
        self.text_item.setParentItem(self)
        self.text_item.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )

    def __str__(self):
        f_val = self.value * 0.001 * self.graph_object.length_in_seconds
        f_val = util.seconds_to_time_str(f_val)
        if self.marker_type == 0 and self.marker_mode == 0:
            return "Start {}".format(f_val)
        elif self.marker_type == 1 and self.marker_mode == 0:
            return "End {}".format(f_val)
        elif self.marker_type == 0 and self.marker_mode == 1:
            return "Loop Start {}".format(f_val)
        elif self.marker_type == 1 and self.marker_mode == 1:
            return "Loop End {}".format(f_val)
        else:
            assert(False)

    def reset_default(self):
        if self.marker_type == 0:
            self.value = 0.0
        else:
            self.value = 1000.0
        self.set_pos()
        self.callback(self.value)

    def set_pos(self):
        if self.marker_type == 0:
            f_new_val = self.value * AUDIO_ITEM_VAL_TO_PX
        elif self.marker_type == 1:
            f_new_val = (self.value *
                AUDIO_ITEM_VAL_TO_PX) - self.audio_item_marker_height
        f_new_val = clip_value(
            f_new_val, self.min_x, self.max_x)
        self.setPos(f_new_val, self.y_pos)

    def set_value(self, a_value):
        self.value = float(a_value)
        self.set_pos()
        self.callback(self.value)

    def set_other(self, a_other, a_fade_marker=None):
        self.other = a_other
        self.fade_marker = a_fade_marker

    def mouseMoveEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseMoveEvent(self, a_event)
        self.pos_x = a_event.scenePos().x()
        self.pos_x = clip_value(
            self.pos_x,
            self.min_x,
            self.max_x,
        )
        self.setPos(self.pos_x, self.y_pos)
        if self.marker_type == 0:
            f_new_val = self.pos_x * AUDIO_ITEM_PX_TO_VAL
            if (
                self.fade_marker is not None
                and
                self.fade_marker.pos().x() < self.pos_x
            ):
                self.fade_marker.value = f_new_val
                self.fade_marker.set_pos()
        elif self.marker_type == 1:
            f_new_val = (
                self.pos_x + self.audio_item_marker_height
            ) * AUDIO_ITEM_PX_TO_VAL
            if (
                self.fade_marker is not None
                and
                self.fade_marker.pos().x() > self.pos_x
            ):
                self.fade_marker.value = f_new_val
                self.fade_marker.set_pos()
        f_new_val = clip_value(f_new_val, 0.0, 994.0)
        self.value = f_new_val
        if self.other is not None:
            if self.marker_type == 0:
                if self.value > self.other.value - MARKER_MIN_DIFF:
                    self.other.value = self.value + MARKER_MIN_DIFF
                    self.other.value = clip_value(
                        self.other.value,
                        MARKER_MIN_DIFF,
                        1000.0,
                        _round=True,
                    )
                    self.other.set_pos()
            elif self.marker_type == 1:
                if self.other.value > self.value - MARKER_MIN_DIFF:
                    self.other.value = self.value - MARKER_MIN_DIFF
                    self.other.value = clip_value(
                        self.other.value,
                        0.0,
                        1000.0 - MARKER_MIN_DIFF,
                        _round=True,
                    )
                    self.other.set_pos()
        if self.fade_marker is not None:
            self.fade_marker.draw_lines()

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        if self.callback is not None:
            self.callback(self.value)
        if self.other.callback is not None:
            self.other.callback(self.other.value)
        if self.fade_marker is not None:
            self.fade_marker.callback(self.fade_marker.value)


class audio_fade_marker_widget(QGraphicsRectItem):
    def __init__(self, a_type, a_val, a_pen, a_brush, a_label, a_graph_object,
                 a_offset=0, a_callback=None):
        """ a_type:  0 == start, 1 == end, more types eventually... """
        self.audio_item_marker_height = 66.0
        QGraphicsRectItem.__init__(
            self,
            0.,
            0.,
            float(self.audio_item_marker_height),
            float(self.audio_item_marker_height),
        )
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.callback = a_callback
        self.line = QGraphicsLineItem(
            0.0, 0.0, 0.0, AUDIO_ITEM_SCENE_HEIGHT)
        self.line.setParentItem(self)
        self.line.setPen(a_pen)
        self.marker_type = a_type
        self.pos_x = 0.0
        self.max_x = \
            AUDIO_ITEM_SCENE_WIDTH - self.audio_item_marker_height
        self.value = a_val
        self.other = None
        self.start_end_marker = None
        if a_type == 0:
            self.min_x = 0.0
            self.y_pos = 0.0 + (a_offset * self.audio_item_marker_height)
            self.line.setPos(0.0, self.y_pos * -1.0)
        elif a_type == 1:
            self.min_x = 66.0
            self.y_pos = AUDIO_ITEM_SCENE_HEIGHT - \
                self.audio_item_marker_height - \
                (a_offset * self.audio_item_marker_height)
            self.line.setPos(self.audio_item_marker_height, self.y_pos * -1.0)
        self.setPen(a_pen)
        self.setBrush(a_brush)
        self.text_item = QGraphicsTextItem(a_label)
        self.text_item.setParentItem(self)
        self.text_item.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )
        self.amp_lines = []
        self.graph_object = a_graph_object
        for f_i in range(self.graph_object.channels * 2):
            f_line = QGraphicsLineItem()
            self.amp_lines.append(f_line)
            f_line.setPen(FADE_PEN)

    def __str__(self):
        f_val = self.value * 0.001 * self.graph_object.length_in_seconds
        f_val = util.seconds_to_time_str(f_val)
        if self.marker_type == 0:
            return "Fade In {}".format(f_val)
        elif self.marker_type == 1:
            return "Fade Out {}".format(f_val)
        else:
            assert(False)

    def reset_default(self):
        if self.marker_type == 0:
            self.value = 0.0
        else:
            self.value = 1000.0
        self.set_pos()
        self.callback(self.value)

    def set_value(self, a_value):
        self.value = float(a_value)
        self.set_pos()
        self.callback(self.value)

    def draw_lines(self):
        f_inc = AUDIO_ITEM_SCENE_HEIGHT / float(len(self.amp_lines))
        f_y_pos = 0
        f_x_inc = 0
        if self.marker_type == 0:
            f_x_list = [self.scenePos().x(),
                        self.start_end_marker.scenePos().x()]
        elif self.marker_type == 1:
            f_x_list = [self.scenePos().x() + self.audio_item_marker_height,
                        self.start_end_marker.scenePos().x() +
                        self.audio_item_marker_height]
        for f_line in self.amp_lines:
            if f_x_inc == 0:
                f_line.setLine(
                    f_x_list[0], f_y_pos, f_x_list[1], f_y_pos + f_inc)
            else:
                f_line.setLine(
                    f_x_list[1], f_y_pos, f_x_list[0], f_y_pos + f_inc)
            f_y_pos += f_inc
            f_x_inc += 1
            if f_x_inc > 1:
                f_x_inc = 0

    def set_pos(self):
        if self.marker_type == 0:
            f_new_val = self.value * AUDIO_ITEM_VAL_TO_PX
        elif self.marker_type == 1:
            f_new_val = (self.value *
                AUDIO_ITEM_VAL_TO_PX) - self.audio_item_marker_height
        f_new_val = clip_value(
            f_new_val,
            self.min_x,
            self.max_x,
        )
        self.setPos(f_new_val, self.y_pos)
        self.draw_lines()

    def set_other(self, a_other, a_start_end_marker):
        self.other = a_other
        self.start_end_marker = a_start_end_marker

    def mouseMoveEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseMoveEvent(self, a_event)
        self.pos_x = a_event.scenePos().x()
        self.pos_x = clip_value(
            self.pos_x,
            self.min_x,
            self.max_x,
        )
        if self.marker_type == 0:
            self.pos_x = clip_max(
                self.pos_x, self.other.scenePos().x())
        elif self.marker_type == 1:
            self.pos_x = clip_min(
                self.pos_x, self.other.scenePos().x())
        self.setPos(self.pos_x, self.y_pos)
        if self.marker_type == 0:
            f_new_val = self.pos_x * AUDIO_ITEM_PX_TO_VAL
            if self.pos_x < self.start_end_marker.scenePos().x():
                self.start_end_marker.value = f_new_val
                self.start_end_marker.set_pos()
        elif self.marker_type == 1:
            f_new_val = (self.pos_x +
                self.audio_item_marker_height) * AUDIO_ITEM_PX_TO_VAL
            if self.pos_x > self.start_end_marker.scenePos().x():
                self.start_end_marker.value = f_new_val
                self.start_end_marker.set_pos()
        f_new_val = clip_value(f_new_val, 0.0, 1000.0)
        self.value = f_new_val
        self.draw_lines()

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        if self.callback is not None:
            self.callback(self.value)
        if self.start_end_marker is not None:
            self.start_end_marker.callback(self.start_end_marker.value)

class AudioItemViewerWidget(QGraphicsView):
    def __init__(
        self,
        a_start_callback,
        a_end_callback,
        a_fade_in_callback,
        a_fade_out_callback,
        bg_brush=None,
        fg_brush=None,
    ):
        QGraphicsView.__init__(self)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate,
        )
        self.start_callback_x = a_start_callback
        self.end_callback_x = a_end_callback
        self.fade_in_callback_x = a_fade_in_callback
        self.fade_out_callback_x = a_fade_out_callback
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.setBackgroundBrush(
            bg_brush if bg_brush else QColor(
                theme.SYSTEM_COLORS.widgets.default_scene_background,
            ),
        )
        self.scene.mousePressEvent = self.scene_mousePressEvent
        self.scene.mouseMoveEvent = self.scene_mouseMoveEvent
        self.scene.mouseReleaseEvent = self.scene_mouseReleaseEvent
        self.scene_context_menu = QMenu(self)
        self.reset_markers_action = QAction(
            _("Reset Markers"),
            self.scene_context_menu,
        )
        self.reset_markers_action.setToolTip(
            'Reset the start, end and loop markers to their default positions'
        )
        self.scene_context_menu.addAction(self.reset_markers_action)
        self.reset_markers_action.triggered.connect(self.reset_markers)

        self.copy_markers_action = QAction(
            _("Copy Markers"),
            self.scene_context_menu,
        )
        self.copy_markers_action.setToolTip(
            'Copy the marker settings from this file, to paste to another'
        )
        self.scene_context_menu.addAction(self.copy_markers_action)
        self.copy_markers_action.triggered.connect(self.copy_markers)

        self.paste_markers_action = QAction(
            _("Paste Markers"),
            self.scene_context_menu,
        )
        self.paste_markers_action.setToolTip(
            'Paste marker settings to this file that were previously copied '
            'using the Copy Markers action'
        )
        self.scene_context_menu.addAction(self.paste_markers_action)
        self.paste_markers_action.triggered.connect(self.paste_markers)

        self.tempo_sync_action = QAction(
            _("Tempo Sync Length"),
            self.scene_context_menu,
        )
        self.tempo_sync_action.setToolTip(
            'Tempo sync the length of this file to a musical time length'
        )
        self.scene_context_menu.addAction(self.tempo_sync_action)
        self.tempo_sync_action.triggered.connect(self.tempo_sync_dialog)

        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.scroll_bar_height = self.horizontalScrollBar().height()
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.waveform_brush = fg_brush if fg_brush else QColor(
            theme.SYSTEM_COLORS.widgets.audio_item_viewer_color,
        )
        self.waveform_pen = QPen(QtCore.Qt.PenStyle.NoPen)
        self.is_drag_selecting = False
        self.drag_start_pos = 0.0
        self.drag_start_markers = []
        self.drag_end_markers = []
        self.graph_object = None
        self.label = QLabel("")
        self.label.setMinimumWidth(420)
        self.last_ts_beat = 1
        self.last_tempo_combobox_index = 0

    def start_callback(self, a_val):
        self.start_callback_x(a_val)
        self.update_label()

    def end_callback(self, a_val):
        self.end_callback_x(a_val)
        self.update_label()

    def fade_in_callback(self, a_val):
        self.fade_in_callback_x(a_val)
        self.update_label()

    def fade_out_callback(self, a_val):
        self.fade_out_callback_x(a_val)
        self.update_label()

    def update_label(self):
        f_val = "\n".join([str(x) for x in
            self.length_str + self.drag_start_markers + self.drag_end_markers])
        self.label.setText(f_val)

    def tempo_sync_dialog(self):
        def sync_button_pressed(a_self=None):
            f_frac = 1.0
            f_switch = (f_beat_frac_combobox.currentIndex())
            f_dict = {
                0 : 0.25, 1 : 0.33333, 2 : 0.5, 3 : 0.666666, 4 : 0.75,
                5 : 1.0, 6 : 2.0, 7 : 4.0, 8 : 0.0,
            }
            f_frac = f_dict[f_switch] * count_spinbox.value()
            self.last_ts_beat = count_spinbox.value()
            bpm = bpm_spinbox.value()
            f_seconds_per_beat = 60 / bpm

            f_result = ((f_seconds_per_beat * f_frac) /
                self.graph_object.length_in_seconds) * 1000.0
            for f_marker in self.drag_end_markers:
                f_new = f_marker.other.value + f_result
                f_new = clip_value(
                    f_new, f_marker.other.value + 1.0, 1000.0)
                f_marker.set_value(f_new)
            self.last_tempo_combobox_index = \
                f_beat_frac_combobox.currentIndex()
            f_dialog.close()

        f_dialog = QDialog(self)
        f_dialog.setWindowTitle(_("Tempo Sync"))
        vlayout = QVBoxLayout(f_dialog)
        f_groupbox_layout = QGridLayout()
        vlayout.addLayout(f_groupbox_layout)
        bpm_spinbox = QDoubleSpinBox()
        bpm_spinbox.setToolTip(
            'The tempo to tempo sync length to'
        )
        bpm_spinbox.setDecimals(1)
        bpm_spinbox.setRange(60, 200)
        bpm_spinbox.setSingleStep(0.1)
        bpm_spinbox.setValue(float(_shared.TEMPO))
        f_beat_fracs = [
            "1/16", "1/12", "1/8", "2/12", "3/16",
            "1/4", "2/4", "4/4", "None",
        ]
        f_beat_frac_combobox = QComboBox()
        f_beat_frac_combobox.setToolTip(
            'The musical length to tempo sync to'
        )
        f_beat_frac_combobox.setMinimumWidth(75)
        f_beat_frac_combobox.addItems(f_beat_fracs)
        f_beat_frac_combobox.setCurrentIndex(self.last_tempo_combobox_index)
        count_spinbox = QSpinBox()
        count_spinbox.setToolTip(
            'The count of "Unit" to tempo sync to.  For example, a count of '
            '3 at 1/16 would be 3/16'
        )
        count_spinbox.setRange(1, 64)
        count_spinbox.setValue(int(self.last_ts_beat))
        f_sync_button = QPushButton(_("Sync"))
        f_sync_button.pressed.connect(sync_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_groupbox_layout.addWidget(QLabel(_("BPM")), 0, 0)
        f_groupbox_layout.addWidget(bpm_spinbox, 1, 0)
        f_groupbox_layout.addWidget(QLabel("Unit"), 0, 1)
        f_groupbox_layout.addWidget(f_beat_frac_combobox, 1, 1)
        f_groupbox_layout.addWidget(QLabel("Count"), 0, 2)
        f_groupbox_layout.addWidget(count_spinbox, 1, 2)
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(ok_cancel_layout)
        ok_cancel_layout.addWidget(f_sync_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def scene_contextMenuEvent(self):
        self.scene_context_menu.exec(QCursor.pos())

    def reset_markers(self):
        for f_marker in self.drag_start_markers + self.drag_end_markers:
            f_marker.reset_default()

    def copy_markers(self):
        if self.graph_object is not None:
            global_set_audio_markers_clipboard(
                self.start_marker.value, self.end_marker.value,
                self.fade_in_marker.value, self.fade_out_marker.value)

    def paste_markers(self):
        if self.graph_object is not None and \
        AUDIO_MARKERS_CLIPBOARD is not None:
            f_markers = (self.start_marker, self.end_marker,
                         self.fade_in_marker, self.fade_out_marker)
            for f_i in range(4):
                f_markers[f_i].set_value(AUDIO_MARKERS_CLIPBOARD[f_i])

    def clear_drawn_items(self):
        self.scene.clear()
        self.drag_start_markers = []
        self.drag_end_markers = []

    def pos_to_marker_val(self, a_pos_x):
        f_result = AUDIO_ITEM_SCENE_WIDTH_RECIP * a_pos_x * 1000.0
        f_result = clip_value(
            f_result, 0.0, AUDIO_ITEM_MAX_MARKER_VAL)
        return f_result

    def scene_mousePressEvent(self, a_event):
        if self.graph_object is None:
            return
        if a_event.button() == QtCore.Qt.MouseButton.RightButton:
            self.scene_contextMenuEvent()
            return
        QGraphicsScene.mousePressEvent(self.scene, a_event)
        if not a_event.isAccepted():
            self.is_drag_selecting = True
            f_pos_x = a_event.scenePos().x()
            f_val = self.pos_to_marker_val(f_pos_x)
            self.drag_start_pos = f_val
            if f_val < self.end_marker.value:
                for f_marker in self.drag_start_markers:
                    f_marker.value = f_val
                    f_marker.set_pos()
                    f_marker.callback(f_marker.value)

                if self.fade_out_marker.value <= f_val + MARKER_MIN_DIFF:
                    self.fade_out_marker.value = f_val + MARKER_MIN_DIFF
                    self.fade_out_marker.set_pos()
                    self.fade_out_marker.callback(self.fade_out_marker.value)

    def scene_mouseReleaseEvent(self, a_event):
        if self.graph_object is None:
            return
        QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        if not a_event.isAccepted():
            self.is_drag_selecting = False
            for f_marker in self.drag_start_markers + self.drag_end_markers:
                f_marker.callback(f_marker.value)

    def scene_mouseMoveEvent(self, a_event):
        if self.graph_object is None:
            return
        QGraphicsScene.mouseMoveEvent(self.scene, a_event)
        if not a_event.isAccepted() and self.is_drag_selecting:
            f_val = self.pos_to_marker_val(a_event.scenePos().x())

            for f_marker in self.drag_start_markers:
                if f_val < self.drag_start_pos:
                    f_marker.value = f_val
                else:
                    f_marker.value = self.drag_start_pos
                f_marker.set_pos()
            for f_marker in self.drag_end_markers:
                if f_val < self.drag_start_pos:
                    f_marker.value = self.drag_start_pos
                else:
                    f_marker.value = f_val
                f_marker.set_pos()

    def draw_item(
        self,
        a_graph_object,
        a_start,
        a_end,
        a_fade_in,
        a_fade_out,
    ):
        self.pixmaps = []
        self.graph_object = a_graph_object
        self.length_str = [
            "Length: {}".format(
                util.seconds_to_time_str(
                    self.graph_object.length_in_seconds,
                ),
            ),
        ]
        self.path_list = create_sample_graph(
            a_graph_object,
            True,
        )
        self.path_count = len(self.path_list)
        self.setUpdatesEnabled(False)
        self.redraw_item(a_start, a_end, a_fade_in, a_fade_out)
        self.setUpdatesEnabled(True)
        self.update()

    def redraw_item(self, a_start, a_end, a_fade_in, a_fade_out):
        self.clear_drawn_items()
        f_path_inc = AUDIO_ITEM_SCENE_HEIGHT / self.path_count
        f_path_y_pos = 0.0
        scene_background_brush = QColor(
            theme.SYSTEM_COLORS.widgets.default_scene_background,
        )
        if not self.pixmaps:
            for f_path in self.path_list:
                f_pixmap = QPixmap(
                    int(AUDIO_ITEM_SCENE_WIDTH),
                    int(f_path_inc),
                )
                f_painter = QPainter(f_pixmap)
                f_painter.setRenderHint(
                    QPainter.RenderHint.Antialiasing,
                )
                f_painter.setPen(self.waveform_pen)
                f_painter.setBrush(self.waveform_brush)
                f_painter.fillRect(
                    0,
                    0,
                    int(AUDIO_ITEM_SCENE_WIDTH),
                    int(f_path_inc),
                    scene_background_brush,
                )
                f_painter.drawPath(f_path)
                f_painter.end()
                self.pixmaps.append(f_pixmap)
        for f_pixmap in self.pixmaps:
            f_path_item = QGraphicsPixmapItem(f_pixmap)
            self.scene.addItem(f_path_item)
            f_path_item.setPos(0.0, f_path_y_pos)
            f_path_y_pos += f_path_inc
        self.start_marker = audio_marker_widget(
            0, a_start, START_END_PEN, START_END_GRADIENT,
            "S", self.graph_object, audio_marker_widget.mode_start_end,
            1, self.start_callback)
        self.scene.addItem(self.start_marker)
        self.end_marker = audio_marker_widget(
            1, a_end, START_END_PEN, START_END_GRADIENT, "E",
            self.graph_object, audio_marker_widget.mode_start_end,
            1, self.end_callback)
        self.scene.addItem(self.end_marker)

        self.fade_in_marker = audio_fade_marker_widget(
            0, a_fade_in, START_END_PEN, START_END_GRADIENT,
            "I", self.graph_object, 0, self.fade_in_callback)
        self.scene.addItem(self.fade_in_marker)
        for f_line in self.fade_in_marker.amp_lines:
            self.scene.addItem(f_line)
        self.fade_out_marker = audio_fade_marker_widget(
            1, a_fade_out, START_END_PEN, START_END_GRADIENT, "O",
            self.graph_object, 0, self.fade_out_callback)
        self.scene.addItem(self.fade_out_marker)
        for f_line in self.fade_out_marker.amp_lines:
            self.scene.addItem(f_line)
        self.fade_in_marker.set_other(self.fade_out_marker, self.start_marker)
        self.fade_out_marker.set_other(self.fade_in_marker, self.end_marker)
        #end fade stuff
        self.start_marker.set_other(self.end_marker, self.fade_in_marker)
        self.end_marker.set_other(self.start_marker, self.fade_out_marker)
        self.start_marker.set_pos()
        self.end_marker.set_pos()
        self.fade_in_marker.set_pos()
        self.fade_out_marker.set_pos()
        self.fade_in_marker.draw_lines()
        self.fade_out_marker.draw_lines()
        self.drag_start_markers = [self.start_marker, self.fade_in_marker]
        self.drag_end_markers = [self.end_marker, self.fade_out_marker]
        self.update_label()

    def resizeEvent(self, a_resize_event):
        QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / AUDIO_ITEM_SCENE_WIDTH
        self.last_y_scale = (f_rect.height() -
            self.scroll_bar_height) / AUDIO_ITEM_SCENE_HEIGHT
        self.scale(self.last_x_scale, self.last_y_scale)

