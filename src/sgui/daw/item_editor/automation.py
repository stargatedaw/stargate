from .abstract import AbstractItemEditor
from sglib.math import clip_min, clip_value
from sgui import shared as glbl_shared
from sgui import widgets
from sgui.daw import shared
from sgui.daw.lib import item as item_lib
from sglib import constants
from sglib.log import LOG
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.models import stargate as sg_project
from sglib.lib import strings as sg_strings, util
from sglib.lib.util import *
from sglib.lib.translate import _
from sgui.sgqt import *
from sglib.models import theme
from sgui.util import get_font


AUTOMATION_POINT_DIAMETER = 15.0
AUTOMATION_POINT_RADIUS = AUTOMATION_POINT_DIAMETER * 0.5
AUTOMATION_RULER_WIDTH = 36.0

AUTOMATION_MIN_HEIGHT = AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS

LAST_IPB_VALUE = 18  #For the 'add point' dialog to remember settings


class AutomationEditor(AbstractItemEditor):
    """ This is the class for both the pitchbend and CC
        QGraphicsView and QGraphicsScene editors on the "Items" tab.
    """
    def __init__(self, a_is_cc=True):
        """ @a_is_cc: True to make self a CC editor, False for a pitchbend
                      editor
        """
        AbstractItemEditor.__init__(self, AUTOMATION_RULER_WIDTH)
        self.is_cc = a_is_cc
        self.set_width()
        self.set_scale()
        self.grid_max_start_time = self.automation_width + \
            AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS
        self.automation_points = []
        self.clipboard = []
        self.selected_str = []

        self.axis_size = AUTOMATION_RULER_WIDTH

        self.px_per_beat = self.automation_width / shared.CURRENT_ITEM_LEN
        self.value_width = self.px_per_beat / 16.0
        self.lines = []

        self.setMinimumHeight(370)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.default_scene_background,
            )
        )
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setScene(self.scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorViewCenter,
        )
        self.cc_num = 1
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        shared.AUTOMATION_EDITORS.append(self)
        self.selection_enabled = True
        self.scene.selectionChanged.connect(self.selection_changed)

    def set_width(self):
        self.automation_width = shared.MIDI_SCALE * (self.width() - 60.0)

    def selection_changed(self, a_event=None):
        if self.selection_enabled:
            for f_item in self.automation_points:
                f_item.set_brush()

    def set_tooltips(self, a_enabled=False):
        if a_enabled:
            if self.is_cc:
                f_start = _("Select the CC you wish to "
                    "automate using the comboboxes below\n")
            else:
                f_start = ""
            self.setToolTip(
                _("{}Draw points by double-clicking, then click "
                "the 'smooth' button to "
                "draw extra points between them.\nClick+drag "
                "to select points\n"
                "Press the 'delete' button to delete selected "
                "points.").format(f_start))
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.selection_enabled = False
        self.scene.clearSelection()
        self.scene.clear()

    def copy_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            return
        self.clipboard = [x.cc_item.clone()
            for x in self.automation_points if x.isSelected()]
        self.clipboard.sort()

    def cut(self):
        self.copy_selected()
        self.delete_selected()

    def paste(self):
        if not shared.ITEM_EDITOR.enabled:
            return
        self.selected_str = []
        if self.clipboard:
            self.clear_range(
                self.clipboard[0].start, self.clipboard[-1].start)
            for f_item in self.clipboard:
                f_item2 = f_item.clone()
                if self.is_cc:
                    f_item2.cc_num = self.cc_num
                    shared.CURRENT_ITEM.add_cc(f_item2)
                else:
                    shared.CURRENT_ITEM.add_pb(f_item2)
                self.selected_str.append(hash(str(f_item2)))
            global_save_and_reload_items()

    def clear_range(self, a_start_beat, a_end_beat, a_save=False):
        for f_point in self.automation_points:
            f_pt_start = f_point.cc_item.start
            if f_pt_start >= a_start_beat and \
            f_pt_start <= a_end_beat:
                if self.is_cc:
                    shared.CURRENT_ITEM.remove_cc(f_point.cc_item)
                else:
                    shared.CURRENT_ITEM.remove_pb(f_point.cc_item)
        if a_save:
            self.selected_str = []
            global_save_and_reload_items()

    def delete_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            return
        self.selection_enabled = False
        for f_point in self.automation_points:
            if f_point.isSelected():
                if self.is_cc:
                    shared.CURRENT_ITEM.remove_cc(f_point.cc_item)
                else:
                    shared.CURRENT_ITEM.remove_pb(f_point.cc_item)
        self.selected_str = []
        global_save_and_reload_items()
        self.selection_enabled = True

    def clear_current_item(self):
        """ If this is a CC editor, it only clears the selected CC.  """
        self.selection_enabled = False
        if not self.automation_points:
            return
        for f_point in self.automation_points:
            if self.is_cc:
                shared.CURRENT_ITEM.remove_cc(f_point.cc_item)
            else:
                shared.CURRENT_ITEM.remove_pb(f_point.cc_item)
        self.selected_str = []
        global_save_and_reload_items()
        self.selection_enabled = True

    def sceneMousePressEvent(self, a_event):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        if shared.EDITOR_MODE == shared.EDITOR_MODE_DRAW:
            f_pos_x = a_event.scenePos().x() - AUTOMATION_POINT_RADIUS
            f_pos_y = a_event.scenePos().y() - AUTOMATION_POINT_RADIUS
            f_cc_start = (f_pos_x - AUTOMATION_MIN_HEIGHT) / self.px_per_beat
            f_cc_start = clip_min(f_cc_start, 0.0)
            if self.is_cc:
                f_cc_val = int(127.0 - (((f_pos_y - AUTOMATION_MIN_HEIGHT) /
                    self.viewer_height) * 127.0))
                f_cc_val = clip_value(f_cc_val, 0, 127)
                shared.ITEM_EDITOR.add_cc(
                    sg_project.cc(
                        f_cc_start,
                        self.cc_num,
                        f_cc_val,
                    )
                )
            else:
                f_cc_val = 1.0 - (((f_pos_y - AUTOMATION_MIN_HEIGHT) /
                    self.viewer_height) * 2.0)
                f_cc_val = clip_value(f_cc_val, -1.0, 1.0)
                shared.ITEM_EDITOR.add_pb(
                    sg_project.pitchbend(
                        f_cc_start,
                        f_cc_val,
                    )
                )
            self.selected_str = []
            global_save_and_reload_items()
        QGraphicsScene.mousePressEvent(self.scene, a_event)

    def draw_header(self):
        AbstractItemEditor.draw_header(
            self, self.automation_width, self.axis_size)
        self.header.setPos(self.axis_size, 0)
        self.scene.addItem(self.header)
        self.y_axis = QGraphicsRectItem(
            0.,
            0.,
            float(self.axis_size),
            float(self.viewer_height),
        )
        self.y_axis.setPos(0, self.axis_size)
        self.scene.addItem(self.y_axis)
        if shared.ITEM_REF_POS:
            f_start, f_end = shared.ITEM_REF_POS
            f_start_x = f_start * self.px_per_beat
            f_end_x = f_end * self.px_per_beat
            f_start_line = QGraphicsLineItem(
                f_start_x,
                0.0,
                f_start_x,
                self.axis_size,
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
                f_end_x, 0.0, f_end_x, self.axis_size, self.header)
            end_pen = QPen(
                QColor(
                    theme.SYSTEM_COLORS.daw.seq_header_region,
                ),
                6.0,
            )
            f_end_line.setPen(end_pen)

    def draw_grid(self):
        self.set_width()
        f_beat_pen = QPen()
        f_beat_pen.setWidth(2)

        if self.is_cc:
            f_labels = [0, '127', 0, '64', 0, '0']
        else:
            f_labels = [0, '1.0', 0, '0', 0, '-1.0']
        for i in range(1, 6):
            f_line = QGraphicsLineItem(
                0,
                0,
                self.automation_width,
                0,
                self.y_axis,
            )
            f_line.setPos(self.axis_size, self.viewer_height * (i - 1) / 4)
            if i % 2:
                f_label = get_font().QGraphicsSimpleTextItem(
                    f_labels[i], self.y_axis)
                f_label.setPos(1, self.viewer_height * (i - 1) / 4)
                f_label.setBrush(QtCore.Qt.GlobalColor.white)
            if i == 3:
                f_line.setPen(f_beat_pen)

        for i in range(0, int(shared.CURRENT_ITEM_LEN) + 1):
            f_beat = QGraphicsLineItem(
                0, 0, 0,
                self.viewer_height + self.axis_size - f_beat_pen.width(),
                self.header)
            f_beat.setPos(self.px_per_beat * i, 0.5 * f_beat_pen.width())
            f_beat.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            )

            f_beat.setPen(f_beat_pen)
            f_beat.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            )
            if i < shared.CURRENT_ITEM_LEN:
                f_number = get_font().QGraphicsSimpleTextItem(
                    str(i + 1), self.header)
                f_number.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
                )
                f_number.setPos(self.px_per_beat * i + 5, 2)
                f_number.setBrush(QtCore.Qt.GlobalColor.white)
        self.setSceneRect(
            0.0,
            0.0,
            float((self.px_per_beat * shared.CURRENT_ITEM_LEN) + 20.0),
            float(self.height()),
        )
#                for j in range(0, 16):
#                    f_line = QGraphicsLineItem(
#                        0, 0, 0, self.viewer_height, self.header)
#                    if float(j) == 8:
#                        f_line.setLine(0, 0, 0, self.viewer_height)
#                        f_line.setPos(
#                            (self.px_per_beat * i) + (self.value_width * j),
#                            self.axis_size)
#                    else:
#                        f_line.setPos((self.px_per_beat * i) +
#                            (self.value_width * j), self.axis_size)
#                        f_line.setPen(f_line_pen)

    def clear_drawn_items(self):
        self.selection_enabled = False
        self.scene.clear()
        self.automation_points = []
        self.lines = []
        self.draw_header()
        self.draw_grid()
        self.selection_enabled = True

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        shared.ITEM_EDITOR.tab_changed()

    def set_scale(self):
        f_rect = self.rect()
        self.viewer_height = float(f_rect.height()) - \
            self.horizontalScrollBar().height() - \
            30.0 - AUTOMATION_RULER_WIDTH
        self.total_height = AUTOMATION_RULER_WIDTH + \
            self.viewer_height - AUTOMATION_POINT_RADIUS

    def set_cc_num(self, a_cc_num):
        self.cc_num = a_cc_num
        self.clear_drawn_items()
        self.draw_item()

    def draw_item(self):
        self.set_width()
        self.setUpdatesEnabled(False)
        self.set_scale()
        self.px_per_beat = self.automation_width / shared.CURRENT_ITEM_LEN
        self.value_width = self.px_per_beat / 16.0
        self.grid_max_start_time = (self.automation_width +
            AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_DIAMETER)
        self.clear_drawn_items()
        if not shared.ITEM_EDITOR.enabled:
            self.setUpdatesEnabled(True)
            return

        f_note_height = (self.viewer_height / 120.0)
        f_note_pen = QPen(QtCore.Qt.GlobalColor.white, f_note_height)

        if self.is_cc:
            for f_cc in shared.CURRENT_ITEM.ccs:
                if f_cc.cc_num == self.cc_num:
                    self.draw_point(f_cc)
        else:
            for f_pb in shared.CURRENT_ITEM.pitchbends:
                self.draw_point(f_pb)
        for f_note in shared.CURRENT_ITEM.notes:
            f_note_start = (f_note.start *
                self.px_per_beat) + AUTOMATION_RULER_WIDTH
            f_note_end = f_note_start + (f_note.length * self.px_per_beat)
            f_note_y = AUTOMATION_RULER_WIDTH + (120.0 -
                f_note.note_num) * f_note_height
            f_note_item = QGraphicsLineItem(
                f_note_start, f_note_y, f_note_end, f_note_y)
            f_note_item.setPen(f_note_pen)
            self.scene.addItem(f_note_item)

        self.setSceneRect(
            0.0,
            0.0,
            float(self.grid_max_start_time + 20.0),
            float(self.height()),
        )
        self.setUpdatesEnabled(True)
        self.update()

    def draw_point(self, a_cc, a_select=True):
        """ a_cc is an instance of the sg_project.cc class"""
        f_time = self.axis_size + (a_cc.start * self.px_per_beat)
        if self.is_cc:
            f_value = self.axis_size +  self.viewer_height / 127.0 * (127.0 -
                a_cc.cc_val)
        else:
            f_value = self.axis_size +  self.viewer_height / 2.0 * (1.0 -
                a_cc.pb_val)
        f_point = AutomationItem(
            f_time, f_value, a_cc, self, self.is_cc)
        self.automation_points.append(f_point)
        self.scene.addItem(f_point)
        if a_select and hash(str(a_cc)) in self.selected_str:
            f_point.setSelected(True)

    def select_all(self):
        self.setUpdatesEnabled(False)
        for f_item in self.automation_points:
            f_item.setSelected(True)
        self.setUpdatesEnabled(True)
        self.update()

class AutomationEditorWidget:
    def __init__(self, a_viewer, a_is_cc=True):
        self.is_cc = a_is_cc
        self.widget = QWidget()
        self.vlayout = QVBoxLayout()
        self.widget.setLayout(self.vlayout)
        self.automation_viewer = a_viewer
        self.hlayout = QHBoxLayout()

        if a_is_cc:
            self.control_combobox = QComboBox()
            self.control_combobox.addItems([str(x) for x in range(1, 128)])
            self.control_combobox.setMinimumWidth(90)
            self.hlayout.addWidget(QLabel(_("CC")))
            self.hlayout.addWidget(self.control_combobox)
            self.control_combobox.currentIndexChanged.connect(
                self.control_changed)
            self.ccs_in_use_combobox = QComboBox()
            self.ccs_in_use_combobox.setMinimumWidth(90)
            self.suppress_ccs_in_use = False
            self.ccs_in_use_combobox.currentIndexChanged.connect(
                self.ccs_in_use_combobox_changed)
            self.hlayout.addWidget(QLabel(_("In Use:")))
            self.hlayout.addWidget(self.ccs_in_use_combobox)

        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(self.automation_viewer)

        self.smooth_button = QPushButton(_("Smooth"))
        self.smooth_button.setToolTip(
            _("By default, the control points are steppy, "
            "this button draws extra points between the existing points."))
        self.smooth_button.pressed.connect(self.smooth_pressed)
        self.hlayout.addWidget(self.smooth_button)
        self.hlayout.addItem(QSpacerItem(10, 10))
        self.edit_button = QPushButton(_("Menu"))
        self.hlayout.addWidget(self.edit_button)
        self.edit_menu = QMenu(self.widget)
        self.copy_action = self.edit_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(
            self.automation_viewer.copy_selected)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.cut_action = self.edit_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.automation_viewer.cut)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.paste_action = self.edit_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.automation_viewer.paste)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.select_all_action = self.edit_menu.addAction(_("Select All"))
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(
            QKeySequence.StandardKey.SelectAll,
        )
        self.delete_action = self.edit_menu.addAction(_("Delete"))
        self.delete_action.triggered.connect(
            self.automation_viewer.delete_selected)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)

        self.edit_menu.addSeparator()
        self.add_point_action = self.edit_menu.addAction(_("Add Point..."))
        if self.is_cc:
            self.add_point_action.triggered.connect(self.add_cc_point)
            self.paste_point_action = self.edit_menu.addAction(
                _("Paste Point from Plugin..."))
            self.paste_point_action.triggered.connect(self.paste_cc_point)
        else:
            self.add_point_action.triggered.connect(self.add_pb_point)
        self.edit_menu.addSeparator()
        self.clear_action = self.edit_menu.addAction(_("Clear"))
        self.clear_action.triggered.connect(self.clear)
        self.edit_button.setMenu(self.edit_menu)
        self.hlayout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Policy.Expanding),
        )

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)

    def set_cc_num(self, a_val=None):
        f_cc_num = int(str(self.control_combobox.currentText()))
        self.automation_viewer.set_cc_num(f_cc_num)

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str != "":
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str))

    def update_ccs_in_use(self, a_ccs):
        self.suppress_ccs_in_use = True
        self.ccs_in_use_combobox.clear()
        self.ccs_in_use_combobox.addItem("")
        for f_cc in sorted(a_ccs):
            self.ccs_in_use_combobox.addItem(str(f_cc))
        self.suppress_ccs_in_use = False

    def smooth_pressed(self):
        if self.is_cc:
            f_cc_num = int(str(self.control_combobox.currentText()))
            shared.CURRENT_ITEM.smooth_automation_points(self.is_cc, f_cc_num)
        else:
            shared.CURRENT_ITEM.smooth_automation_points(self.is_cc)
        self.automation_viewer.selected_str = []
        global_save_and_reload_items()

    def select_all(self):
        self.automation_viewer.select_all()

    def clear(self):
        self.automation_viewer.clear_current_item()

    def paste_cc_point(self):
        if glbl_shared.CC_CLIPBOARD is None:
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _(
                    "Nothing copied to the clipboard.\n"
                    "Right-click->'Copy' on any knob on any plugin."
                ),
            )
            return
        self.add_cc_point(glbl_shared.CC_CLIPBOARD)

    def add_cc_point(self, a_value=None):
        if not shared.ITEM_EDITOR.enabled:  #TODO:  Make this global...
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        def ok_handler():
            f_cc = sg_project.cc(
                f_pos_spinbox.value() - 1.0,
                self.automation_viewer.cc_num,
                f_value_spinbox.value(),
            )
            shared.CURRENT_ITEM.add_cc(f_cc)

            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )
            global_open_items(shared.CURRENT_ITEM_NAME)
            constants.DAW_PROJECT.commit(_("Add automation point"))
            self.automation_viewer.draw_item()

        def goto_start():
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        def cancel_handler():
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, shared.CURRENT_ITEM_LEN + 0.98)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        f_end_button = QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QLabel(_("Value")), 10, 0)
        f_value_spinbox = QDoubleSpinBox()
        f_value_spinbox.setRange(0.0, 127.0)
        f_value_spinbox.setDecimals(4)
        if a_value is not None:
            f_value_spinbox.setValue(float(a_value))
        f_layout.addWidget(f_value_spinbox, 10, 1)

        f_ok = QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec()

    def add_pb_point(self):
        if not shared.ITEM_EDITOR.enabled:  #TODO:  Make this global...
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        def ok_handler():
            f_value = clip_value(
                f_epb_spinbox.value() / f_ipb_spinbox.value(),
                -1.0,
                1.0,
                _round=True,
            )
            f_pb = sg_project.pitchbend(
                f_pos_spinbox.value() - 1.0,
                f_value,
            )
            shared.CURRENT_ITEM.add_pb(f_pb)

            global LAST_IPB_VALUE
            LAST_IPB_VALUE = f_ipb_spinbox.value()

            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )
            global_open_items(shared.CURRENT_ITEM_NAME)
            constants.DAW_PROJECT.commit(_("Add pitchbend automation point"))
            self.automation_viewer.draw_item()

        def cancel_handler():
            f_window.close()

        def ipb_changed(a_self=None, a_event=None):
            f_epb_spinbox.setRange(
                int(f_ipb_spinbox.value() * -1),
                int(f_ipb_spinbox.value()),
            )

        def goto_start():
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, shared.CURRENT_ITEM_LEN + 0.98)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        f_end_button = QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QLabel(_("Instrument Pitchbend")), 10, 0)
        f_ipb_spinbox = QSpinBox()
        f_ipb_spinbox.setToolTip(
            _("Set this to the same setting that your instrument plugin uses"),
        )
        f_ipb_spinbox.setRange(2, 36)
        f_ipb_spinbox.setValue(int(LAST_IPB_VALUE))
        f_layout.addWidget(f_ipb_spinbox, 10, 1)
        f_ipb_spinbox.valueChanged.connect(ipb_changed)

        f_layout.addWidget(QLabel(_("Effective Pitchbend")), 20, 0)
        f_epb_spinbox = QSpinBox()
        f_epb_spinbox.setToolTip("")
        f_epb_spinbox.setRange(-18, 18)
        f_layout.addWidget(f_epb_spinbox, 20, 1)

        f_layout.addWidget(
            QLabel(sg_strings.pitchbend_dialog),
            30,
            1,
        )

        f_ok = QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec()

class AutomationItem(QGraphicsEllipseItem):
    """ This is a CC or pitchbend event in an AutomationEditor
    """
    def __init__(self, a_time, a_value, a_cc, a_view, a_is_cc):
        QGraphicsEllipseItem.__init__(
            self, 0, 0, AUTOMATION_POINT_DIAMETER, AUTOMATION_POINT_DIAMETER)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges,
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
        )
        self.setPos(
            a_time - AUTOMATION_POINT_RADIUS,
            a_value - AUTOMATION_POINT_RADIUS,
        )
        self.setBrush(
            QColor(
                theme.SYSTEM_COLORS.daw.item_atm_point,
            ),
        )
        f_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.daw.item_atm_point_pen,
            ),
            2.0,
        )
        self.setPen(f_pen)
        self.cc_item = a_cc
        self.parent_view = a_view
        self.is_cc = a_is_cc

    def set_brush(self):
        if self.isSelected():
            self.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_atm_point_selected,
                ),
            )
        else:
            self.setBrush(
                QColor(
                    theme.SYSTEM_COLORS.daw.item_atm_point,
                ),
            )

    def mouseMoveEvent(self, a_event):
        QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        for f_point in self.parent_view.automation_points:
            if f_point.isSelected():
                if f_point.pos().x() < AUTOMATION_MIN_HEIGHT:
                    f_point.setPos(
                        AUTOMATION_MIN_HEIGHT, f_point.pos().y())
                elif f_point.pos().x() > self.parent_view.grid_max_start_time:
                    f_point.setPos(
                        self.parent_view.grid_max_start_time,
                        f_point.pos().y(),
                    )
                if f_point.pos().y() < AUTOMATION_MIN_HEIGHT:
                    f_point.setPos(f_point.pos().x(), AUTOMATION_MIN_HEIGHT)
                elif f_point.pos().y() > self.parent_view.total_height:
                    f_point.setPos(
                        f_point.pos().x(), self.parent_view.total_height)

    def mouseReleaseEvent(self, a_event):
        QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        self.parent_view.selected_str = []
        for f_point in self.parent_view.automation_points:
            if f_point.isSelected():
                f_pos_x = f_point.pos().x()
                f_cc_start = (f_pos_x -
                    AUTOMATION_MIN_HEIGHT) / self.parent_view.px_per_beat
                f_cc_start = clip_min(f_cc_start, 0.0)
                f_cc_start = round(f_cc_start, 6)
                if self.is_cc:
                    shared.CURRENT_ITEM.ccs.remove(f_point.cc_item)
                    f_cc_val = (127.0 - (((f_point.pos().y() -
                        AUTOMATION_MIN_HEIGHT) /
                        self.parent_view.viewer_height) * 127.0))

                    f_point.cc_item.start = f_cc_start
                    f_point.cc_item.set_val(f_cc_val)
                    shared.CURRENT_ITEM.ccs.append(f_point.cc_item)
                    shared.CURRENT_ITEM.ccs.sort()
                else:
                    #try:
                    shared.CURRENT_ITEM.pitchbends.remove(f_point.cc_item)
                    #except ValueError:
                    #LOG.info("Exception removing {} from list".format(
                        #f_point.cc_item))
                    f_cc_val = (1.0 - (((f_point.pos().y() -
                        AUTOMATION_MIN_HEIGHT) /
                        self.parent_view.viewer_height) * 2.0))

                    f_point.cc_item.start = f_cc_start
                    f_point.cc_item.set_val(f_cc_val)
                    shared.CURRENT_ITEM.pitchbends.append(f_point.cc_item)
                    shared.CURRENT_ITEM.pitchbends.sort()
                self.parent_view.selected_str.append(
                    hash(str(f_point.cc_item)))
        global_save_and_reload_items()

