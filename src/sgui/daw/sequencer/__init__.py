"""

"""
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.plugins import *
from sgui.sgqt import *

from . import _shared
from .atm_item import SeqAtmItem
from .item import SequencerItem
from .itemlist import ItemListWidget
from .playlist import PlaylistWidget
from .seq import ItemSequencer
from .track import SeqTrack, TrackPanel
from sglib import constants
from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui import widgets
from sglib.lib.translate import _

class SequencerWidget:
    """ The widget that holds the sequencer """
    def __init__(self):
        self.enabled = False
        self.widget = QWidget()
        self.widget.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum,
        )
        self.hlayout0 = QHBoxLayout(self.widget)
        self.hlayout0.setContentsMargins(1, 1, 1, 1)

        self.menu_button = QPushButton(_("Menu"))
        self.hlayout0.addWidget(self.menu_button)
        self.menu = QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)

        self.action_widget = QWidgetAction(self.menu)
        self.menu_widget = QWidget(self.menu)
        self.menu_layout = QGridLayout(self.menu_widget)
        self.menu_layout.addWidget(QLabel(_("Edit Mode:")), 0, 0)
        self.edit_mode_combobox = QComboBox()
        self.edit_mode_combobox.setMinimumWidth(132)
        self.edit_mode_combobox.addItems([_("Items"), _("Automation")])
        self.edit_mode_combobox.currentIndexChanged.connect(
            self.edit_mode_changed,
        )
        self.edit_mode_combobox.setToolTip(
            'Change the edit mode.  Edit items or automation'
        )
        self.menu_layout.addWidget(self.edit_mode_combobox, 0, 1)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.menu.addAction(self.action_widget)

        self.toggle_edit_mode_action = QAction(
            _("Toggle Edit Mode"),
            self.menu,
        )
        self.toggle_edit_mode_action.setToolTip(
            'Toggle between item and automation editing mode in the sequencer'
        )
        self.toggle_edit_mode_action.setShortcut(
            QKeySequence.fromString("CTRL+E"),
        )
        #self.menu_button.addAction(self.toggle_edit_mode_action)
        self.menu.addAction(self.toggle_edit_mode_action)
        self.toggle_edit_mode_action.triggered.connect(self.toggle_edit_mode)

        self.menu.addSeparator()

        self.reorder_tracks_action = QAction(
            _("Reorder Tracks..."),
            self.menu,
        )
        self.menu.addAction(self.reorder_tracks_action)
        self.reorder_tracks_action.setToolTip(
            'Re-order the sequencer tracks / plugin racks'
        )
        self.reorder_tracks_action.triggered.connect(self.set_track_order)

        #self.menu.addSeparator()

        self.hide_inactive = False
#        self.toggle_hide_action = self.menu.addAction(
#            _("Hide Inactive Instruments"))
#        self.toggle_hide_action.setCheckable(True)
#        self.toggle_hide_action.triggered.connect(self.toggle_hide_inactive)
#        self.toggle_hide_action.setShortcut(
#            QKeySequence.fromString("CTRL+H"))
        self.menu.addSeparator()

        self.unsolo_action = QAction(_("Un-Solo All"), self.menu)
        self.menu.addAction(self.unsolo_action)
        self.widget.addAction(self.unsolo_action)
        self.unsolo_action.setToolTip(
            'Disable solo for any tracks that have been soloed'
        )
        self.unsolo_action.triggered.connect(self.unsolo_all)
        self.unsolo_action.setShortcut(QKeySequence.fromString("CTRL+J"))

        self.unmute_action = QAction(_("Un-Mute All"), self.menu)
        self.menu.addAction(self.unmute_action)
        self.widget.addAction(self.unmute_action)
        self.unmute_action.setToolTip(
            'Disable mute for any tracks that have been muted'
        )
        self.unmute_action.triggered.connect(self.unmute_all)
        self.unmute_action.setShortcut(QKeySequence.fromString("CTRL+M"))

        self.snap_combobox = QComboBox()
        self.snap_combobox.addItems(
            [_("None"), _("Beat"), "1/8", "1/12", "1/16"])
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        # Not currently doing this because the items snap to a new position
        # When clicked after different snap settings.  Fine positioning should
        # be done within the items and not at the sequencer level
        # self.menu_layout.addWidget(QLabel(_("Snap:")), 5, 0)
        # self.menu_layout.addWidget(self.snap_combobox, 5, 1)

        self.follow_checkbox = QCheckBox(_("Follow"))
        self.follow_checkbox.setToolTip(
            'Sequencer horizontal scroll follows the playback cursor'
        )
        self.follow_checkbox.setChecked(True)
        self.hlayout0.addWidget(self.follow_checkbox)

        self.hlayout0.addWidget(QLabel("H"))
        self.hzoom_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hzoom_slider.setToolTip('Horizontal zoom')
        self.hlayout0.addWidget(self.hzoom_slider)
        self.hzoom_slider.setObjectName("zoom_slider")
        self.hzoom_slider.setRange(0, 30)
        self.last_hzoom = 3
        self.hzoom_slider.setValue(self.last_hzoom)
        self.hzoom_slider.setFixedWidth(75)
        self.hzoom_slider.sliderPressed.connect(self.hzoom_pressed)
        self.hzoom_slider.sliderReleased.connect(self.hzoom_released)
        self.hzoom_slider.valueChanged.connect(self.set_hzoom)
        self.is_hzooming = False

        self.hlayout0.addWidget(QLabel("V"))
        self.vzoom_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.vzoom_slider.setToolTip('Vertical zoom')
        self.hlayout0.addWidget(self.vzoom_slider)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setRange(0, 60)
        self.last_vzoom = 0
        self.vzoom_slider.setValue(self.last_vzoom)
        self.vzoom_slider.setFixedWidth(75)
        self.vzoom_slider.sliderPressed.connect(self.vzoom_pressed)
        self.vzoom_slider.sliderReleased.connect(self.vzoom_released)
        self.vzoom_slider.valueChanged.connect(self.set_vzoom)
        self.is_vzooming = False

        # Ignore key and mouse wheel events, they do not work well with
        # how the zoom sliders visualize their changes
        self.hzoom_slider.wheelEvent = \
            self.hzoom_slider.keyPressEvent = \
            self.vzoom_slider.wheelEvent = \
            self.vzoom_slider.keyPressEvent = lambda x: None

        self.size_label = QLabel()
        self.size_label.setObjectName("seq_zoom_size_label")
        self.size_label.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint,
        )

        self.scrollbar = shared.SEQUENCER.horizontalScrollBar()
        self.scrollbar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.scrollbar.sliderPressed.connect(self.scrollbar_pressed)
        self.scrollbar.sliderReleased.connect(self.scrollbar_released)
        self.hlayout0.addWidget(self.scrollbar)
        self.scrollbar.setSingleStep(_shared.SEQUENCER_PX_PER_BEAT)

        self.widgets_to_disable = (
            self.hzoom_slider, self.vzoom_slider, self.menu_button)

    def toggle_edit_mode(self):
        if not glbl_shared.IS_PLAYING:
            # This relies on the assumption that only 2 modes exist
            current_mode = self.edit_mode_combobox.currentIndex()
            self.edit_mode_combobox.setCurrentIndex(int(not current_mode))

    def scrollbar_pressed(self, a_val=None):
        if (
            glbl_shared.IS_PLAYING
            and
            self.follow_checkbox.isChecked()
        ):
            self.follow_checkbox.setChecked(False)

    def scrollbar_released(self, a_val=None):
        f_val = round(self.scrollbar.value() /
            _shared.SEQUENCER_PX_PER_BEAT) * _shared.SEQUENCER_PX_PER_BEAT
        self.scrollbar.setValue(int(f_val))

    def vzoom_pressed(self, a_val=None):
        self.is_vzooming = True
        self.old_px_per_beat = _shared.SEQUENCER_PX_PER_BEAT
        #self.size_label.move(QCursor.pos())
        self.size_label.setText("Track Height")
        self.set_vzoom_size()
        f_widget = shared.MAIN_WINDOW.midi_scroll_area
        f_point = QtCore.QPoint(
            0,
            int(_shared.SEQUENCE_EDITOR_HEADER_HEIGHT + 2),
        )
        self.size_label.setParent(f_widget)
        self.size_label.move(f_point)
        self.size_label.show()
        self.old_height_px = shared.SEQUENCE_EDITOR_TRACK_HEIGHT

    def vzoom_released(self, a_val=None):
        self.is_vzooming = False
        shared.TRACK_PANEL.set_track_height()
        self.open_sequence()

        f_scrollbar = shared.MAIN_WINDOW.midi_scroll_area.verticalScrollBar()
        f_scrollbar.setValue(
            int(
                (shared.SEQUENCE_EDITOR_TRACK_HEIGHT / self.old_height_px)
                * f_scrollbar.value()
            ),
        )
        shared.MAIN_WINDOW.vscrollbar_released()  # Quantizes the vertical pos
        f_scrollbar.setSingleStep(shared.SEQUENCE_EDITOR_TRACK_HEIGHT)
        self.size_label.hide()

    def set_vzoom_size(self):
        self.size_label.setFixedSize(
            _shared.SEQUENCE_TRACK_WIDTH,
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT + 2,
        )

    def set_vzoom(self, a_val=None):
        if not self.is_vzooming:
            self.vzoom_slider.setValue(self.last_vzoom)
            return
        self.last_vzoom = self.vzoom_slider.value()
        shared.SEQUENCE_EDITOR_TRACK_HEIGHT = (self.last_vzoom * 8) + 64
        _shared.SEQUENCE_EDITOR_TOTAL_HEIGHT = (
            _shared.SEQUENCE_EDITOR_TRACK_COUNT
            *
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        )
        self.set_vzoom_size()

    def force_hzoom(self, val):
        self.hzoom_pressed()
        self.hzoom_slider.setValue(3)
        self.set_hzoom(3)
        self.hzoom_released()

    def hzoom_pressed(self, a_val=None):
        self.is_hzooming = True
        self.old_px_per_beat = _shared.SEQUENCER_PX_PER_BEAT
        #self.size_label.move(QCursor.pos())
        self.size_label.setText("Beat")
        self.set_hzoom_size()
        f_point = QtCore.QPoint(
            int(_shared.SEQUENCE_TRACK_WIDTH + 6),
            2,
        )
        f_widget = shared.MAIN_WINDOW.midi_scroll_area
        self.size_label.setParent(f_widget)
        self.size_label.move(f_point)
        self.size_label.show()

    def hzoom_released(self, a_val=None):
        self.is_hzooming = False
        _shared.set_seq_snap()
        self.open_sequence()
        self.scrollbar.setValue(
            int(
                (
                    _shared.SEQUENCER_PX_PER_BEAT
                    /
                    self.old_px_per_beat
                ) * self.scrollbar.value()
            )
        )
        self.scrollbar.setSingleStep(int(_shared.SEQUENCER_PX_PER_BEAT))
        self.size_label.hide()

    def set_hzoom_size(self):
        self.size_label.setFixedSize(
            int(_shared.SEQUENCER_PX_PER_BEAT),
            int(_shared.SEQUENCE_EDITOR_HEADER_HEIGHT),
        )

    def set_hzoom(self, a_val=None):
        if not self.is_hzooming:
            self.hzoom_slider.setValue(self.last_hzoom)
            return
        self.last_hzoom = self.hzoom_slider.value()
        if self.last_hzoom < 3:
            shared.SEQUENCER.ignore_moves = True
            _shared.DRAW_SEQUENCER_GRAPHS = False
            f_length = get_current_sequence_length()
            f_width = shared.SEQUENCER.width()
            f_factor = {0:1, 1:2, 2:4}[self.last_hzoom]
            _shared.SEQUENCER_PX_PER_BEAT = (f_width / f_length) * f_factor
            self.size_label.setText("Project * {}".format(f_factor))
            self.size_label.setFixedSize(
                150,
                _shared.SEQUENCE_EDITOR_HEADER_HEIGHT,
            )
        else:
            shared.SEQUENCER.ignore_moves = False
            if self.last_hzoom < 6:
                self.last_hzoom = 6
            _shared.DRAW_SEQUENCER_GRAPHS = True
            _shared.SEQUENCER_PX_PER_BEAT = ((self.last_hzoom - 6) * 4) + 24
            self.size_label.setText("Beat")
            self.set_hzoom_size()

    def set_snap(self, a_val=None):
        _shared.set_seq_snap(a_val)
        shared.MAIN_WINDOW.tab_changed()

    def edit_mode_changed(self, a_value=None):
        _shared.SEQUENCE_EDITOR_MODE = a_value
        shared.SEQUENCER.open_sequence()

    def toggle_hide_inactive(self):
        self.hide_inactive = self.toggle_hide_action.isChecked()
        global_update_hidden_rows()

    def unsolo_all(self):
        for track in shared.TRACK_PANEL.tracks.values():
            if track.solo_checkbox.isChecked():
                track.solo_checkbox.trigger()

    def unmute_all(self):
        for track in shared.TRACK_PANEL.tracks.values():
            if track.mute_checkbox.isChecked():
                track.mute_checkbox.trigger()

    def open_sequence(self, uid=None):
        self.enabled = False
        if shared.CURRENT_SEQUENCE:
            self.clear_items()
        if uid is None:
            uid = constants.DAW_CURRENT_SEQUENCE_UID
        else:
            constants.DAW_CURRENT_SEQUENCE_UID = uid
        shared.CURRENT_SEQUENCE = constants.DAW_PROJECT.get_sequence(uid)
        self.enabled = True
        shared.SEQUENCER.open_sequence()
        global_update_hidden_rows()
        #shared.TRANSPORT.set_time(shared.TRANSPORT.get_bar_value(), 0.0)

    def clear_items(self):
        shared.SEQUENCER.clear_drawn_items()
        shared.CURRENT_SEQUENCE = None

    def clear_new(self):
        shared.CURRENT_SEQUENCE = None
        shared.SEQUENCER.clear_new()

    def on_play(self):
        for f_widget in self.widgets_to_disable:
            f_widget.setEnabled(False)

    def on_stop(self):
        for f_widget in self.widgets_to_disable:
            f_widget.setEnabled(True)

    def set_track_order(self):
        f_result = widgets.ordered_table_dialog(
            shared.TRACK_NAMES[1:],
            [x + 1 for x in range(len(shared.TRACK_NAMES[1:]))],
            30, 200, shared.MAIN_WINDOW,
        )
        if f_result:
            f_result = {f_result[x]:x + 1 for x in range(len(f_result))}
            f_result[0] = 0  # main track
            constants.DAW_PROJECT.reorder_tracks(f_result)
            shared.TRACK_PANEL.open_tracks()
            self.open_sequence()
            shared.MIDI_DEVICES_DIALOG.set_routings()
            shared.TRANSPORT.open_project()
            shared.PLUGIN_RACK.set_track_order(
                f_result,
                shared.TRACK_NAMES,
            )

