"""

"""
from . import _shared
from .item import AudioSeqItem
from ..abstract import AbstractItemEditor
from sglib.math import clip_min, clip_value
from sgui import shared as glbl_shared
from sgui import widgets
from sgui.daw import shared
from sgui.daw.filedragdrop import FileDragDropper
from sglib.models.daw import *
from sgui.daw.shared import *
from sgui.daw.lib import item as item_lib
from sglib import constants
from sglib.lib import util
from sglib.lib import strings as sg_strings
from sglib.lib.util import *
from sglib.lib.translate import _
from sglib.log import LOG
from sglib.math import linear_interpolate
from sgui.sgqt import *
from sglib.models import theme
from sglib.models.stargate.audio_pool import PerFileFX
from sglib.models.theme import get_asset_path
from sgui.util import get_font


PAIFX_TEXT = """\
Select exactly one item to use

This allows you to set effects per audio item.
Setting effects on one will not affect another,
but you can copy and paste effects between items.
"""

PAFFX_TEXT = """\
Select exactly one item to use

This allows you to set effects for every
instance of a file in an entire project.
"""

def papifx_val_callback(a_port, a_val):
    if _shared.CURRENT_ITEM is not None:
        constants.DAW_PROJECT.ipc().audio_per_file_fx(
            _shared.CURRENT_ITEM.audio_item.uid,
            a_port,
            a_val,
        )

def papifx_rel_callback(a_port, a_val):
    if _shared.CURRENT_ITEM is not None:
        pool = constants.PROJECT.get_audio_pool()
        controls = shared.AUDIO_SEQ_WIDGET.papifx.get_list()
        fx = PerFileFX(
            _shared.CURRENT_ITEM.audio_item.uid,
            controls,
        )
        pool.set_per_file_fx(fx)
        constants.PROJECT.save_audio_pool(pool)

def paif_val_callback(a_port, a_val):
    if (
        shared.CURRENT_ITEM is not None
        and
        _shared.CURRENT_AUDIO_ITEM_INDEX is not None
    ):
        constants.DAW_PROJECT.ipc().audio_per_item_fx(
            shared.CURRENT_ITEM.uid,
            _shared.CURRENT_AUDIO_ITEM_INDEX,
            a_port,
            a_val,
        )

def paif_rel_callback(a_port, a_val):
    if (
        shared.CURRENT_ITEM is not None
        and
        _shared.CURRENT_AUDIO_ITEM_INDEX is not None
    ):
        f_index_list = shared.AUDIO_SEQ_WIDGET.paifx.get_list()
        shared.CURRENT_ITEM.set_row(
            _shared.CURRENT_AUDIO_ITEM_INDEX,
            f_index_list,
        )
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )

class Silhouette(QGraphicsRectItem):
    def __init__(self):
        super().__init__()
        self.setRect(
            QtCore.QRectF(
                0.0,
                0.0,
                float(_shared.AUDIO_QUANTIZE_PX),
                float(_shared.AUDIO_ITEM_HEIGHT),
            ),
        )
        self.setBrush(
            QColor(theme.SYSTEM_COLORS.daw.drag_drop_silhouette),
        )

    def quantize(self, pos):
        lane = _shared.y_to_lane(pos.y())
        x = pos.x()
        quantized = _shared.quantize_all(x, _round=False)
        self.setPos(
            quantized,
            (lane * _shared.AUDIO_ITEM_HEIGHT) + _shared.AUDIO_RULER_HEIGHT,
        )

class AudioItemSeq(AbstractItemEditor):
    """ This is the QGraphicsView and QGraphicsScene for editing audio
        items within a SequencerItem on the "Items" tab.
    """
    def __init__(self):
        AbstractItemEditor.__init__(self)
        self.reset_line_lists()
        self.is_erasing = False
        self.h_zoom = 1.0
        self.v_zoom = 1.0
        self.scene = QGraphicsScene(self)
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseMoveEvent = self.sceneMouseMoveEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.scene.dropEvent = self.sceneDropEvent
        self.scene.dragEnterEvent = self.sceneDragEnterEvent
        self.scene.dragMoveEvent = self.sceneDragMoveEvent
        self.scene.dragLeaveEvent = self.sceneDragLeaveEvent
        self.scene.setBackgroundBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.default_scene_background,
            ),
        )
        self.scene.selectionChanged.connect(self.scene_selection_changed)
        self.setAcceptDrops(True)
        self.setScene(self.scene)
        self.audio_items = []
        self.track = 0
        self.gradient_index = 0
        self.playback_px = 0.0
        self.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignTop
            |
            QtCore.Qt.AlignmentFlag.AlignLeft
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.is_playing = False
        self.reselect_on_stop = []
        #Somewhat slow on my AMD 5450 using the FOSS driver
        #self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.context_menu_enabled = True
        self.setToolTip(sg_strings.AudioItemSeq)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    def reset_line_lists(self):
        self.text_list = []
        self.beat_line_list = []

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def keyPressEvent(self, a_event):
        #Done this way to prevent the sequence editor from grabbing the key
        if a_event.key() == QtCore.Qt.Key.Key_Delete:
            self.delete_selected()
        else:
            QGraphicsView.keyPressEvent(self, a_event)

    def scrollContentsBy(self, x, y):
        QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_y_pos()

    def set_header_y_pos(self):
        f_point = self.get_scene_pos()
        self.header.setPos(0.0, f_point.y())
        self.verticalScrollBar().setMinimum(0)

    def get_scene_pos(self):
        return QtCore.QPointF(
            float(self.horizontalScrollBar().value()),
            float(self.verticalScrollBar().value()),
        )

    def get_selected(self):
        return [x for x in self.audio_items if x.isSelected()]

    def delete_selected(self):
        if self.check_running():
            return
        f_items = shared.CURRENT_ITEM
        f_paif = shared.CURRENT_ITEM
        for f_item in self.get_selected():
            f_items.remove_item(f_item.track_num)
            f_paif.clear_row_if_exists(f_item.track_num)
        item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        constants.DAW_PROJECT.commit(_("Delete audio item(s)"))
        global_open_audio_items(True)

    def warn_multi_select(
        self,
        msg="You must have exactly one item selected",
    ) -> bool:
        if len(self.get_selected()) == 1:
            return True
        else:
            QMessageBox.warning(None, "Error", msg)
            return False

    def crossfade_selected(self):
        f_list = self.get_selected()
        if len(f_list) < 2:
            QMessageBox.warning(
                shared.MAIN_WINDOW,
                _("Error"),
                _("You must have at least 2 items selected to crossfade"),
            )
            return

        f_tempo = shared.CURRENT_SEQUENCE.get_tempo_at_pos(
            shared.CURRENT_ITEM_REF.start_beat,
        )
        f_changed = False

        for f_item in f_list:
            f_start_sec = util.musical_time_to_seconds(
                f_tempo, f_item.audio_item.start_bar,
                f_item.audio_item.start_beat)
            f_time_frac = f_item.audio_item.sample_end - \
                f_item.audio_item.sample_start
            f_time_frac *= 0.001
            f_time = f_item.graph_object.length_in_seconds * f_time_frac
            f_end_sec = f_start_sec + f_time
            f_list2 = [x for x in f_list if x.audio_item != f_item.audio_item]

            for f_item2 in f_list2:
                f_start_sec2 = util.musical_time_to_seconds(
                    f_tempo, f_item2.audio_item.start_bar,
                    f_item2.audio_item.start_beat)
                f_time_frac2 = f_item2.audio_item.sample_end - \
                    f_item2.audio_item.sample_start
                f_time_frac2 *= 0.001
                f_time2 = f_item2.graph_object.length_in_seconds * f_time_frac2
                f_end_sec2 = f_start_sec2 + f_time2

                if (
                    f_start_sec > f_start_sec2
                    and
                    f_end_sec > f_end_sec2
                    and
                    f_end_sec2 > f_start_sec  # item1 is after item2
                ):
                    f_changed = True
                    f_diff_sec = f_end_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_in(f_val)
                elif (
                    f_start_sec < f_start_sec2
                    and
                    f_end_sec < f_end_sec2
                    and
                    f_end_sec > f_start_sec2  # item1 is before item2
                ):
                    f_changed = True
                    f_diff_sec = f_start_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_out(f_val)

        if f_changed:
            item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            constants.DAW_PROJECT.commit(_("Crossfade audio items"))
            global_open_audio_items(True)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        set_audio_seq_zoom(self.h_zoom, self.v_zoom)
        global_open_audio_items(a_reload=False)

    def scene_selection_changed(self):
        f_selected_items = []
        for f_item in self.audio_items:
            f_item.set_brush()
            if f_item.isSelected():
                f_selected_items.append(f_item)
        if len(f_selected_items) == 1:
            _shared.CURRENT_ITEM = f_selected_items[0]
            _shared.CURRENT_AUDIO_ITEM_INDEX = f_selected_items[0].track_num
            shared.AUDIO_SEQ_WIDGET.paifx.widget.setEnabled(True)
            shared.AUDIO_SEQ_WIDGET.paifx.set_from_list(
                shared.CURRENT_ITEM.get_row(
                    _shared.CURRENT_AUDIO_ITEM_INDEX,
                ),
            )
            shared.AUDIO_SEQ_WIDGET.papifx.widget.setEnabled(True)

            pool = constants.PROJECT.get_audio_pool()
            per_file_fx_by_uid = pool.per_file_fx_by_uid()
            uid = _shared.CURRENT_ITEM.audio_item.uid
            if uid in per_file_fx_by_uid:
                fx = per_file_fx_by_uid[uid]
                shared.AUDIO_SEQ_WIDGET.papifx.set_from_list(fx.controls)
            else:
                shared.AUDIO_SEQ_WIDGET.papifx.clear_effects()
            shared.AUDIO_SEQ_WIDGET.paifx_stack.setCurrentIndex(0)
            shared.AUDIO_SEQ_WIDGET.papifx_stack.setCurrentIndex(0)
        elif len(f_selected_items) == 0:
            _shared.CURRENT_AUDIO_ITEM_INDEX = None
            _shared.CURRENT_ITEM = None
            shared.AUDIO_SEQ_WIDGET.paifx_stack.setCurrentIndex(1)
            shared.AUDIO_SEQ_WIDGET.papifx_stack.setCurrentIndex(1)
            shared.AUDIO_SEQ_WIDGET.papifx.widget.setDisabled(True)
            shared.AUDIO_SEQ_WIDGET.paifx.widget.setDisabled(True)
        else:
            _shared.CURRENT_ITEM = None
            shared.AUDIO_SEQ_WIDGET.paifx_stack.setCurrentIndex(1)
            shared.AUDIO_SEQ_WIDGET.papifx_stack.setCurrentIndex(1)
            shared.AUDIO_SEQ_WIDGET.papifx.widget.setDisabled(True)
            shared.AUDIO_SEQ_WIDGET.paifx.widget.setDisabled(True)

    def erase_tool(self, event):
        item = self.get_item_at_scene_pos(event.scenePos())
        if item:
            item.hide()
            self.items_to_delete.append(item)

    def erase_tool_start(self):
        self.is_erasing = True
        self.items_to_delete = []
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def erase_tool_finish(self):
        self.is_erasing = False
        self.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag,
        )
        if not self.items_to_delete:
            return
        items = shared.CURRENT_ITEM
        paif = shared.CURRENT_ITEM
        for item in self.items_to_delete:
            items.remove_item(item.track_num)
            paif.clear_row_if_exists(item.track_num)
        item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        constants.DAW_PROJECT.commit(_("Delete audio item(s)"))
        global_open_audio_items(True)

    def sceneMousePressEvent(self, event):
        if (
            event.button() == QtCore.Qt.MouseButton.LeftButton
            and
            shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE
        ):
            self.erase_tool_start()
            self.erase_tool(event)
            event.accept()
        QGraphicsScene.mousePressEvent(self.scene, event)

    def sceneMouseMoveEvent(self, event):
        if self.is_erasing:
            self.erase_tool(event)
            event.accept()
        QGraphicsScene.mouseMoveEvent(self.scene, event)

    def sceneMouseReleaseEvent(self, event):
        if self.is_erasing:
            self.erase_tool_finish()
            event.accept()
        QGraphicsScene.mouseReleaseEvent(self.scene, event)

    def sceneDragEnterEvent(self, a_event):
        a_event.setAccepted(True)
        self.last_drag_item = None
        self.silhouette = Silhouette()
        self.scene.addItem(self.silhouette)
        self.silhouette.quantize(a_event.scenePos())

    def sceneDragMoveEvent(self, a_event):
        self.silhouette.quantize(a_event.scenePos())
        a_event.setDropAction(QtCore.Qt.DropAction.CopyAction)
        item = self.get_item_at_scene_pos(a_event.scenePos())
        if item and item != self.last_drag_item:
            self.silhouette.hide()
            item.set_brush(override=True)
            if self.last_drag_item:
                self.last_drag_item.set_brush()
            self.last_drag_item = item
        elif not item:
            self.silhouette.show()
            if self.last_drag_item:
                self.last_drag_item.set_brush()

    def sceneDragLeaveEvent(self, a_event):
        self.silhouette.hide()
        if self.last_drag_item:
            self.last_drag_item.set_brush()
        QGraphicsScene.dragLeaveEvent(self.scene, a_event)

    def check_running(self):
        if (
            not shared.CURRENT_ITEM
            or
            glbl_shared.IS_PLAYING
        ):
            return True
        return False

    def sceneDropEvent(self, a_event):
        self.silhouette.hide()
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        if shared.AUDIO_ITEMS_TO_DROP:
            item = self.get_item_at_scene_pos(a_event.scenePos())
            if item and len(shared.AUDIO_ITEMS_TO_DROP) == 1:
                item.handleDropEvent(shared.AUDIO_ITEMS_TO_DROP[0])
            else:
                f_x = a_event.scenePos().x()
                f_y = a_event.scenePos().y()
                self.add_items(f_x, f_y, shared.AUDIO_ITEMS_TO_DROP)
        shared.clear_seq_drop()

    def get_item_at_scene_pos(self, pos):
        items = [
            x for x in self.scene.items(pos)
            if isinstance(x, AudioSeqItem)
        ]
        if len(items) == 1:
            return items[0]

    def add_items(self, f_x, f_y, a_item_list):
        if self.check_running():
            return

        f_beat_frac = f_x / _shared.AUDIO_PX_PER_BEAT
        f_beat_frac = clip_min(f_beat_frac, 0.0)
        LOG.info("f_beat_frac: {}".format(f_beat_frac))
        if _shared.AUDIO_QUANTIZE:
            f_beat_frac = int(
                f_beat_frac * _shared.AUDIO_QUANTIZE_AMT
            ) / _shared.AUDIO_QUANTIZE_AMT

        f_lane_num = _shared.y_to_lane(f_y)

        f_items = shared.CURRENT_ITEM

        for f_file_name in a_item_list:
            f_file_name_str = str(f_file_name)
            if not f_file_name_str is None and not f_file_name_str == "":
                f_index = f_items.get_next_index()
                if f_index == -1:
                    QMessageBox.warning(self, _("Error"),
                    _("No more available audio item slots, "
                    "max per sequence is {}").format(MAX_AUDIO_ITEM_COUNT))
                    break
                else:
                    f_uid = constants.PROJECT.get_wav_uid_by_name(
                        f_file_name_str,
                    )
                    f_item = DawAudioItem(
                        f_uid,
                        a_start_bar=0,
                        a_start_beat=f_beat_frac,
                        a_lane_num=f_lane_num,
                    )
                    f_items.add_item(f_index, f_item)
                    f_graph = constants.PROJECT.get_sample_graph_by_uid(
                        f_uid,
                    )
                    f_audio_item = shared.AUDIO_SEQ.draw_item(
                        f_index, f_item, f_graph)
                    f_audio_item.clip_at_sequence_end()
        item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        constants.DAW_PROJECT.commit(
            _("Added audio items to item {}").format(shared.CURRENT_ITEM.uid))
        global_open_audio_items()
        self.last_open_dir = os.path.dirname(f_file_name_str)

    def reset_selection(self):
        for f_item in self.audio_items:
            if str(f_item.audio_item) in self.reselect_on_stop:
                f_item.setSelected(True)

    def set_zoom(self, a_scale):
        self.h_zoom = a_scale
        self.update_zoom()

    def set_v_zoom(self, a_scale):
        self.v_zoom = a_scale
        self.update_zoom()

    def update_zoom(self):
        set_audio_seq_zoom(self.h_zoom, self.v_zoom)

    def check_line_count(self):
        """ Check that there are not too many vertical
            lines on the screen
        """
        f_num_count = len(self.text_list)
        if f_num_count == 0:
            return
        f_num_visible_count = int(f_num_count /
            clip_min(self.h_zoom, 1))

        if f_num_visible_count > 24:
            for f_line in self.beat_line_list:
                f_line.setVisible(False)
            f_factor = f_num_visible_count // 24
            if f_factor == 1:
                for f_num in self.text_list:
                    f_num.setVisible(True)
            else:
                f_factor = int(round(f_factor / 2.0) * 2)
                for f_num in self.text_list:
                    f_num.setVisible(False)
                for f_num in self.text_list[::f_factor]:
                    f_num.setVisible(True)
        else:
            for f_line in self.beat_line_list:
                f_line.setVisible(True)
            for f_num in self.text_list:
                f_num.setVisible(True)


    def draw_header(self):
        f_sequence_length = shared.CURRENT_ITEM_LEN
        f_size = _shared.AUDIO_PX_PER_BEAT * f_sequence_length
        self.total_height = (_shared.AUDIO_ITEM_LANE_COUNT *
            (_shared.AUDIO_ITEM_HEIGHT)) + _shared.AUDIO_RULER_HEIGHT
        AbstractItemEditor.draw_header(
            self,
            f_size,
            _shared.AUDIO_RULER_HEIGHT,
        )
        self.header.setZValue(1500.0)
        self.scene.addItem(self.header)
        if shared.ITEM_REF_POS:
            f_start, f_end = shared.ITEM_REF_POS
            f_start_x = f_start * _shared.AUDIO_PX_PER_BEAT
            f_end_x = f_end * _shared.AUDIO_PX_PER_BEAT
            f_start_line = QGraphicsLineItem(
                f_start_x,
                0.0,
                f_start_x,
                _shared.AUDIO_RULER_HEIGHT,
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
                _shared.AUDIO_RULER_HEIGHT,
                self.header,
            )
            end_pen = QPen(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_header_region,
                ),
                6.0,
            )
            f_end_line.setPen(end_pen)
        f_v_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.daw.seq_bar_line,
            )
        )
        #f_beat_pen = QPen(QColor(210, 210, 210))
        f_16th_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.daw.seq_beat_line,
            ),
        )
        track_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.daw.seq_track_line,
            ),
        )
        f_reg_pen = QPen(QtCore.Qt.GlobalColor.white)
        i3 = 0.0
        number_brush = QColor(
            theme.SYSTEM_COLORS.daw.seq_header_text,
        )
        if _shared.AUDIO_PX_PER_BEAT >= 20:
            for i in range(int(f_sequence_length)):
                f_number = get_font().QGraphicsSimpleTextItem(
                    "{}".format(i + 1),
                    self.header,
                )
                f_number.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
                )
                f_number.setBrush(number_brush)
                f_number.setZValue(1000.0)
                self.text_list.append(f_number)
                self.scene.addLine(i3, 0.0, i3, self.total_height, f_v_pen)
                f_number.setPos(i3 + 3.0, 2)
                if _shared.AUDIO_LINES_ENABLED:
                    for f_i4 in range(1, _shared.AUDIO_SNAP_RANGE):
                        f_sub_x = i3 + (_shared.AUDIO_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x,
                            _shared.AUDIO_RULER_HEIGHT,
                            f_sub_x,
                            self.total_height,
                            f_16th_pen,
                        )
                        self.beat_line_list.append(f_line)
#                for f_beat_i in range(1, 4):
#                    f_beat_x = i3 + (_shared.AUDIO_PX_PER_BEAT * f_beat_i)
#                    f_line = self.scene.addLine(
#                        f_beat_x, 0.0, f_beat_x, self.total_height, f_beat_pen)
#                    self.beat_line_list.append(f_line)
#                    if _shared.AUDIO_LINES_ENABLED:
#                        for f_i4 in range(1, _shared.AUDIO_SNAP_RANGE):
#                            f_sub_x = f_beat_x + (_shared.AUDIO_QUANTIZE_PX * f_i4)
#                            f_line = self.scene.addLine(
#                                f_sub_x, _shared.AUDIO_RULER_HEIGHT,
#                                f_sub_x, self.total_height, f_16th_pen)
#                            self.beat_line_list.append(f_line)
                i3 += _shared.AUDIO_PX_PER_BEAT
        self.scene.addLine(
            i3,
            _shared.AUDIO_RULER_HEIGHT,
            i3,
            self.total_height,
            f_reg_pen,
        )
        for i2 in range(_shared.AUDIO_ITEM_LANE_COUNT):
            f_y = (
                _shared.AUDIO_ITEM_HEIGHT * (i2 + 1)
            ) + _shared.AUDIO_RULER_HEIGHT
            self.scene.addLine(0, f_y, f_size, f_y, track_pen)
        self.check_line_count()
        self.set_header_y_pos()

    def clear_drawn_items(self):
        if self.is_playing:
            f_was_playing = True
            self.is_playing = False
        else:
            f_was_playing = False
        self.reset_line_lists()
        self.audio_items = []
        self.scene.clear()
        self.draw_header()
        if f_was_playing:
            self.is_playing = True

    def draw_item(self, a_audio_item_index, a_audio_item, a_graph):
        """a_start in seconds, a_length in seconds"""
        f_audio_item = AudioSeqItem(
            a_audio_item_index,
            a_audio_item,
            a_graph,
        )
        self.audio_items.append(f_audio_item)
        self.scene.addItem(f_audio_item)
        return f_audio_item

class AudioItemSeqWidget(FileDragDropper):
    """ The parent widget (including the file browser dialog) for the
        AudioItemSeq
    """
    def __init__(self):
        FileDragDropper.__init__(self, util.is_audio_file)
        self.list_file.setToolTip(
            'The files in the current directory.  Drag and drop the files '
            'into the current sequencer item to create audio items, or drop '
            'onto another audio item to replace it'
        )

        self.papifx = widgets.per_audio_item_fx_widget(
            papifx_rel_callback,
            papifx_val_callback,
        )
        self.papifx_widget = QWidget()
        self.papifx_widget.setObjectName("plugin_ui")
        self.papifx_vlayout = QVBoxLayout(self.papifx_widget)
        self.papifx_stack = QStackedWidget(self.folders_tab_widget)
        self.papifx_stack.addWidget(self.papifx_widget)
        self.papifx_stack.addWidget(QLabel(PAFFX_TEXT))
        self.papifx_stack.setCurrentIndex(1)
        self.folders_tab_widget.addTab(
            self.papifx_stack,
            _("Audio File Effects"),
        )
        self.papifx.widget.setDisabled(True)
        self.papifx_vlayout.addWidget(self.papifx.scroll_area)

        self.paifx = widgets.per_audio_item_fx_widget(
            paif_rel_callback,
            paif_val_callback,
        )
        self.paifx_widget = QWidget()
        self.paifx_widget.setObjectName("plugin_ui")
        self.paifx_vlayout = QVBoxLayout(self.paifx_widget)
        self.paifx_stack = QStackedWidget(self.folders_tab_widget)
        self.paifx_stack.addWidget(self.paifx_widget)
        self.paifx_stack.addWidget(QLabel(PAIFX_TEXT))
        self.paifx_stack.setCurrentIndex(1)
        self.folders_tab_widget.addTab(
            self.paifx_stack,
            _("Audio Item Effects"),
        )
        self.paifx.widget.setDisabled(True)
        self.paifx_vlayout.addWidget(self.paifx.scroll_area)

        self.widget = QWidget()
        self.widget.setContentsMargins(0, 0, 0, 0)
        self.vlayout = QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.widget.setLayout(self.vlayout)
        self.hlayout = QHBoxLayout()
        self.hlayout.setContentsMargins(5, 5, 5, 5)
        self.hlayout.setSpacing(5)
        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(shared.AUDIO_SEQ)

        self.menu_button = QToolButton()
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('menu.svg'),
            ),
            QIcon.Mode.Normal,
            #QIcon.State.On,
        )
        self.menu_button.setIcon(icon)
        self.menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        self.hlayout.addWidget(self.menu_button)
        self.action_menu = QMenu(self.widget)
        self.menu_button.setMenu(self.action_menu)

        self.copy_action = QAction(_("Copy"), self.action_menu)
        self.action_menu.addAction(self.copy_action)
        self.copy_action.setToolTip(
            'Copy selected audio items to the clipboard to be pasted into '
            'other sequencer items.  To copy items within the same item, '
            f'{util.KEY_CTRL}+click and drag'
        )
        self.copy_action.triggered.connect(self.on_copy)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)

        self.cut_action = QAction(_("Cut"), self.action_menu)
        self.action_menu.addAction(self.cut_action)
        self.cut_action.setToolTip(
            'Copy selected audio items to the clipboard and delete from '
            'the sequencer item'
        )
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)

        self.paste_action = QAction(_("Paste"), self.action_menu)
        self.action_menu.addAction(self.paste_action)
        self.paste_action.setToolTip(
            'Paste previously copied items into this item at the same '
            'position.  To copy items within the same item, '
            f'{KEY_CTRL}+click and drag'
        )
        self.paste_action.triggered.connect(self.on_paste)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)

        self.select_all_action = QAction(_("Select All"), self.action_menu)
        self.action_menu.addAction(self.select_all_action)
        self.select_all_action.setToolTip(
            'Select all audio items in this sequencer item'
        )
        self.select_all_action.triggered.connect(self.on_select_all)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)

        self.clear_selection_action = QAction(
            _("Clear Selection"),
            self.action_menu,
        )
        self.action_menu.addAction(self.clear_selection_action)
        self.clear_selection_action.setToolTip(
            'Unselect all selected audio items'
        )
        self.clear_selection_action.triggered.connect(
            shared.AUDIO_SEQ.scene.clearSelection,
        )
        self.clear_selection_action.setShortcut(
            QKeySequence.fromString("Esc"),
        )

        self.action_menu.addSeparator()

        self.delete_selected_action = QAction(_("Delete"), self.action_menu)
        self.action_menu.addAction(self.delete_selected_action)
        self.delete_selected_action.setToolTip(
            'Delete selected audio items from this sequencer item'
        )
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(
            QKeySequence.StandardKey.Delete,
        )

        self.action_menu.addSeparator()

        self.crossfade_action = QAction(
            _("Crossfade Selected"),
            self.action_menu,
        )
        self.action_menu.addAction(self.crossfade_action)
        self.crossfade_action.setToolTip(
            'Select multiple audio items in different lanes that partially '
            'overlap each other, and use this action to update their '
            'fade-in/out handles to create a cross-fade effect'
        )
        self.crossfade_action.triggered.connect(
            shared.AUDIO_SEQ.crossfade_selected,
        )
        self.crossfade_action.setShortcut(
            QKeySequence.fromString("CTRL+F"),
        )

        self.action_menu.addSeparator()

        self.v_zoom_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.v_zoom_slider.setToolTip(
            'Vertical zoom for the audio item editor.  Horizontal zoom for '
            'all item editors is on the upper right of the Item Editor tab'
        )
        self.v_zoom_slider.setObjectName("zoom_slider")
        self.v_zoom_slider.setRange(10, 100)
        self.v_zoom_slider.setValue(10)
        self.v_zoom_slider.setSingleStep(1)
        self.v_zoom_slider.setMaximumWidth(60)
        self.v_zoom_slider.valueChanged.connect(self.set_v_zoom)
        self.hlayout.addWidget(QLabel(_("V")))
        self.hlayout.addWidget(self.v_zoom_slider)

        scrollbar = QScrollBar()
        scrollbar.setToolTip(
            'The horizontal scrollbar for the audio item editor'
        )
        shared.AUDIO_SEQ.setHorizontalScrollBar(scrollbar)
        scrollbar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.hlayout.addWidget(scrollbar)

        self.audio_items_clipboard = []
        self.disable_on_play = (self.menu_button,)
        self.set_multiselect(False)
        self.paifx_clipboard = None

    def on_play(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(False)

    def on_stop(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(True)

    def on_select_all(self):
        if (
            shared.CURRENT_SEQUENCE is None
            or
            glbl_shared.IS_PLAYING
        ):
            return
        for f_item in shared.AUDIO_SEQ.audio_items:
            f_item.setSelected(True)

    def on_glue_selected(self):
        if (
            shared.CURRENT_SEQUENCE is None
            or
            glbl_shared.IS_PLAYING
        ):
            return
        shared.AUDIO_SEQ.glue_selected()

    def on_delete_selected(self):
        if (
            shared.CURRENT_SEQUENCE is None
            or
            glbl_shared.IS_PLAYING
        ):
            return
        shared.AUDIO_SEQ.delete_selected()

    def on_papifx_copy(self):
        if not shared.AUDIO_SEQ.warn_multi_select(
            "Only one item can be selected to copy, please select exactly one"
        ):
            return
        if _shared.CURRENT_ITEM is not None:
            self.paifx_clipboard = shared.AUDIO_SEQ_WIDGET.papifx.get_list()
        else:
            QMessageBox.warning(None, None, 'You must right click on an item')

    def on_papifx_paste(self):
        if self.paifx_clipboard is not None:
            pool = constants.PROJECT.get_audio_pool()
            uids = set()
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    uid = f_item.audio_item.uid,
                    fx = PerFileFX(
                        uid,
                        self.paifx_clipboard,
                    )
                    uids.add(uid)
                    pool.set_per_file_fx(fx)
            constants.PROJECT.save_audio_pool(pool)
            shared.AUDIO_SEQ_WIDGET.papifx.set_from_list(
                self.paifx_clipboard,
            )
            ipc = constants.DAW_PROJECT.ipc()
            for uid in uids:
                fx = PerFileFX(
                    uid,
                    self.paifx_clipboard,
                )
                ipc.audio_per_file_fx_paste(str(fx))
        else:
            QMessageBox.warning(None, None, 'You must copy to the clipboard')

    def on_papifx_clear(self):
        pool = constants.PROJECT.get_audio_pool()
        uids = set()
        for item in shared.AUDIO_SEQ.audio_items:
            if item.isSelected():
                uid = item.audio_item.uid
                pool.remove_per_file_fx(uid)
                uids.add(uid)
        constants.PROJECT.save_audio_pool(pool)
        ipc = constants.DAW_PROJECT.ipc()
        for uid in uids:
            ipc.audio_per_file_fx_clear(uid)
        self.papifx.clear_effects()


    def on_paifx_copy(self):
        if not shared.AUDIO_SEQ.warn_multi_select(
            "Only one item can be selected to copy, please select exactly one"
        ):
            return
        if (
            _shared.CURRENT_AUDIO_ITEM_INDEX is not None
            and
            shared.CURRENT_ITEM
        ):
            f_paif = shared.CURRENT_ITEM
            self.paifx_clipboard = f_paif.get_row(
                _shared.CURRENT_AUDIO_ITEM_INDEX,
            )
        else:
            QMessageBox.warning(None, None, 'You must right click on an item')

    def on_paifx_paste(self):
        if (
            self.paifx_clipboard is not None
            and
            shared.CURRENT_ITEM
        ):
            f_paif = shared.CURRENT_ITEM
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.set_row(
                        f_item.track_num,
                        self.paifx_clipboard,
                    )
            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )
            shared.AUDIO_SEQ_WIDGET.paifx.set_from_list(
                self.paifx_clipboard,
            )
        else:
            QMessageBox.warning(
                None,
                None,
                'You must copy to the clipboard and right click on an item'
            )

    def on_paifx_clear(self):
        if shared.CURRENT_ITEM:
            f_paif = shared.CURRENT_ITEM
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.clear_row_if_exists(f_item.track_num)
            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )
            self.paifx.clear_effects()

    def on_copy(self):
        if not shared.CURRENT_ITEM or glbl_shared.IS_PLAYING:
            return 0
        self.audio_items_clipboard = []
        f_per_item_fx_dict = shared.CURRENT_ITEM
        f_count = False
        for f_item in shared.AUDIO_SEQ.get_selected():
            f_count = True
            self.audio_items_clipboard.append(
                (str(f_item.audio_item),
                 f_per_item_fx_dict.get_row(f_item.track_num, True)))
        if not f_count:
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _("Nothing selected."),
            )
        return f_count

    def on_cut(self):
        if self.on_copy():
            self.on_delete_selected()

    def on_paste(self):
        if not shared.CURRENT_ITEM or glbl_shared.IS_PLAYING:
            return
        if not self.audio_items_clipboard:
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _("Nothing copied to the clipboard."),
            )
        shared.AUDIO_SEQ.reselect_on_stop = []
        f_per_item_fx_dict = shared.CURRENT_ITEM
#        f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
        for f_str, f_list in self.audio_items_clipboard:
            shared.AUDIO_SEQ.reselect_on_stop.append(f_str)
            f_index = shared.CURRENT_ITEM.get_next_index()
            if f_index == -1:
                break
            f_item = DawAudioItem.from_str(f_str)
            f_start = f_item.start_beat
            if f_start < shared.CURRENT_ITEM_LEN:
#                f_graph = constants.PROJECT.get_sample_graph_by_uid(f_item.uid)
#                f_item.clip_at_sequence_end(
#                    shared.CURRENT_ITEM_LEN, f_global_tempo,
#                    f_graph.length_in_seconds)
                shared.CURRENT_ITEM.add_item(f_index, f_item)
                if f_list is not None:
                    f_per_item_fx_dict.set_row(f_index, f_list)
        shared.CURRENT_ITEM.deduplicate_items()
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        constants.DAW_PROJECT.commit(_("Paste audio items"))
        global_open_audio_items(True)
        shared.AUDIO_SEQ.scene.clearSelection()
        shared.AUDIO_SEQ.reset_selection()

    def set_v_zoom(self, a_val=None):
        shared.AUDIO_SEQ.set_v_zoom(float(a_val) * 0.1)
        global_open_audio_items(a_reload=False)

def set_audio_seq_zoom(a_horizontal, a_vertical):
    # Normalize 1-10 to 0-1
    horizontal = (a_horizontal - 1.) * 1.11111111
    f_width = float(shared.AUDIO_SEQ.rect().width()) - \
        float(shared.AUDIO_SEQ.verticalScrollBar().width()) - 6.0
    f_sequence_length = shared.CURRENT_ITEM_LEN
    min_px_per_beat = f_width / f_sequence_length
    max_px_per_beat = max(
        min_px_per_beat * 6.,
        50.
    )

    _shared.AUDIO_PX_PER_BEAT = linear_interpolate(
        min_px_per_beat,
        max_px_per_beat,
        horizontal,
    )
    shared.AUDIO_SEQ.px_per_beat = _shared.AUDIO_PX_PER_BEAT
    _shared.set_audio_snap(_shared.AUDIO_SNAP_VAL)
    _shared.AUDIO_ITEM_HEIGHT = 75.0 * a_vertical
    shared.AUDIO_SEQ.scene.setSceneRect(
        0.0,
        0.0,
        float(_shared.AUDIO_PX_PER_BEAT * f_sequence_length),
        float(_shared.AUDIO_ITEM_HEIGHT * _shared.AUDIO_ITEM_MAX_LANE),
    )

