"""

"""
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.plugins import *
from sgui.sgqt import *
from sgui.util import TouchpadFilter

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
from sglib.math import clip_value
from sglib.models.theme import get_asset_path
from sgui.daw.lib import sequence as sequence_lib


class SequencerWidget:
    """ The widget that holds the sequencer """
    def __init__(self):
        self.enabled = False
        self._last_solo = set()
        self._last_mute = set()
        self.touchpad_filter = TouchpadFilter()
        self.widget = QWidget()
        self.widget.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum,
        )
        self.hlayout0 = QHBoxLayout(self.widget)
        self.hlayout0.setContentsMargins(1, 1, 1, 1)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(20, 20))
        self.hlayout0.addWidget(self.toolbar)

        # Hamburger menu
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('menu.svg'),
            ),
            QIcon.Mode.Normal,
            #QIcon.State.On,
        )
        self.menu_button = QToolButton()
        self.menu_button.setIcon(icon)
        self.menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.toolbar.addWidget(self.menu_button)
        self.menu = QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)
        self.reorder_tracks_action = QAction("Reorder Tracks...", self.menu)
        self.menu.addAction(self.reorder_tracks_action)
        self.reorder_tracks_action.setToolTip(
            'Re-order the sequencer tracks / plugin racks'
        )
        self.reorder_tracks_action.triggered.connect(self.set_track_order)

        # Edit Mode
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('edit-items.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('edit-atm.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        self.edit_checkbox = QAction(icon, '', self.toolbar)
        self.edit_checkbox.setToolTip(
            f'Toggle between editing items and automation ({KEY_CTRL}+E)'
        )
        self.edit_checkbox.setCheckable(True)
        self.toolbar.addAction(self.edit_checkbox)
        self.edit_checkbox.triggered.connect(self.edit_mode_changed)
        self.edit_checkbox.setShortcut(
            QKeySequence.fromString("CTRL+E")
        )

        # Follow
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('follow-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('follow-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.follow_checkbox = QAction(icon, '', self.toolbar)
        self.follow_checkbox.setToolTip(
            'Sequencer horizontal scroll follows the playback cursor'
            f" ({KEY_CTRL}+F)"
        )
        self.follow_checkbox.setCheckable(True)
        self.follow_checkbox.setChecked(True)
        self.toolbar.addAction(self.follow_checkbox)
        self.follow_checkbox.setShortcut(
            QKeySequence.fromString("CTRL+F")
        )

        # Un-solo
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('solo-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('solo-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.solo_checkbox = QAction(icon, '', self.toolbar)
        self.solo_checkbox.setToolTip(
            'Toggle disabling or enabling solo for any tracks that have '
            f'been soloed ({KEY_CTRL}+J)'
        )
        self.solo_checkbox.setCheckable(True)
        self.toolbar.addAction(self.solo_checkbox)
        self.solo_checkbox.setShortcut(
            QKeySequence.fromString("CTRL+J")
        )
        self.solo_checkbox.triggered.connect(self.unsolo_all)

        # Un-mute
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('mute-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('mute-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.mute_checkbox = QAction(icon, '', self.toolbar)
        self.mute_checkbox.setToolTip(
            'Toggle disabling or enabling mute for any tracks that have '
            f'been muted ({KEY_CTRL}+M)'
        )
        self.mute_checkbox.setCheckable(True)
        self.toolbar.addAction(self.mute_checkbox)
        self.mute_checkbox.setShortcut(
            QKeySequence.fromString("CTRL+M")
        )
        self.mute_checkbox.triggered.connect(self.unmute_all)

        self.hide_inactive = False
#        self.toggle_hide_action = self.menu.addAction(
#            _("Hide Inactive Instruments"))
#        self.toggle_hide_action.setCheckable(True)
#        self.toggle_hide_action.triggered.connect(self.toggle_hide_inactive)
#        self.toggle_hide_action.setShortcut(
#            QKeySequence.fromString("CTRL+H"))

        self.snap_combobox = QComboBox()
        self.snap_combobox.addItems(
            [_("None"), _("Beat"), "1/8", "1/12", "1/16"])
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        # Not currently doing this because the items snap to a new position
        # When clicked after different snap settings.  Fine positioning should
        # be done within the items and not at the sequencer level
        # self.menu_layout.addWidget(QLabel(_("Snap:")), 5, 0)
        # self.menu_layout.addWidget(self.snap_combobox, 5, 1)

        self.hlayout0.addWidget(QLabel("H"))
        self.hzoom_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hzoom_slider.setToolTip(
            f'Horizontal zoom.  {KEY_CTRL}+MouseWheel'
        )
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
        self.vzoom_slider.setToolTip(
            f'Vertical zoom.  SHIFT+MouseWheel'
        )
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

        self.scrollbar = QScrollBar()
        self.scrollbar.setToolTip(
            'The horizontal scrollbar for the sequencer'
        )
        shared.SEQUENCER.setHorizontalScrollBar(self.scrollbar)
        self.scrollbar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.scrollbar.sliderPressed.connect(self.scrollbar_pressed)
        self.scrollbar.sliderReleased.connect(self.scrollbar_released)
        self.hlayout0.addWidget(self.scrollbar)
        self.scrollbar.setSingleStep(_shared.SEQUENCER_PX_PER_BEAT)

        self.widgets_to_disable = (
            self.hzoom_slider,
            self.vzoom_slider,
            self.menu_button,
            self.edit_checkbox,
        )

    def update_solo_all(self):
        for track in shared.TRACK_PANEL.tracks.values():
            if track.solo_checkbox.isChecked():
                self.solo_checkbox.setChecked(True)
                return
        self.solo_checkbox.setChecked(False)

    def update_mute_all(self):
        for track in shared.TRACK_PANEL.tracks.values():
            if track.mute_checkbox.isChecked():
                self.mute_checkbox.setChecked(True)
                return
        self.mute_checkbox.setChecked(False)

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

    def inc_hzoom(self, up: bool):
        up = self.touchpad_filter.run(up)
        glbl_shared.MAIN_STACKED_WIDGET.setUpdatesEnabled(False)
        val = self.hzoom_slider.value()
        step = self.hzoom_slider.singleStep()
        val = (val + 1) if up else (val - 1)
        val = clip_value(val, 6, self.hzoom_slider.maximum())
        self.hzoom_slider.setValue(val)
        self.last_hzoom = val
        shared.SEQUENCER.ignore_moves = False
        _shared.DRAW_SEQUENCER_GRAPHS = True
        old_px_per_beat = _shared.SEQUENCER_PX_PER_BEAT
        _shared.SEQUENCER_PX_PER_BEAT = ((self.last_hzoom - 6) * 4) + 24
        shared.SEQUENCER.open_sequence()
        self.scrollbar.setValue(
            int(
                (
                    _shared.SEQUENCER_PX_PER_BEAT
                    /
                    old_px_per_beat
                ) * self.scrollbar.value()
            )
        )
        self.scrollbar.setSingleStep(int(_shared.SEQUENCER_PX_PER_BEAT))
        _shared.set_seq_snap()
        glbl_shared.MAIN_STACKED_WIDGET.setUpdatesEnabled(True)
        glbl_shared.MAIN_STACKED_WIDGET.update()

    def inc_vzoom(self, up: bool):
        up = self.touchpad_filter.run(up)
        glbl_shared.MAIN_STACKED_WIDGET.setUpdatesEnabled(False)
        val = self.vzoom_slider.value()
        step = self.vzoom_slider.singleStep()
        val = (val + step) if up else (val - step)
        val = clip_value(
            val,
            self.vzoom_slider.minimum(),
            self.vzoom_slider.maximum(),
        )
        self.vzoom_slider.setValue(val)
        self.last_vzoom = val
        old_height_px = shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        shared.SEQUENCE_EDITOR_TRACK_HEIGHT = (self.last_vzoom * 8) + 64
        _shared.SEQUENCE_EDITOR_TOTAL_HEIGHT = (
            _shared.SEQUENCE_EDITOR_TRACK_COUNT
            *
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        )
        shared.TRACK_PANEL.set_track_height()
        shared.SEQUENCER.open_sequence()
        f_scrollbar = shared.MAIN_WINDOW.midi_scroll_area.verticalScrollBar()
        f_scrollbar.setValue(
            int(
                (shared.SEQUENCE_EDITOR_TRACK_HEIGHT / old_height_px)
                * f_scrollbar.value()
            ),
        )
        shared.MAIN_WINDOW.vscrollbar_released()  # Quantizes the vertical pos
        f_scrollbar.setSingleStep(shared.SEQUENCE_EDITOR_TRACK_HEIGHT)
        glbl_shared.MAIN_STACKED_WIDGET.setUpdatesEnabled(True)
        glbl_shared.MAIN_STACKED_WIDGET.update()

    def set_snap(self, a_val=None):
        _shared.set_seq_snap(a_val)
        shared.MAIN_WINDOW.tab_changed()

    def edit_mode_changed(self, a_value=None):
        _shared.SEQUENCE_EDITOR_MODE = int(a_value)
        shared.SEQUENCER.open_sequence()

    def toggle_hide_inactive(self):
        self.hide_inactive = self.toggle_hide_action.isChecked()
        global_update_hidden_rows()

    def unsolo_all(self):
        if self.solo_checkbox.isChecked():
            for k in shared.TRACK_PANEL.tracks:
                track = shared.TRACK_PANEL.tracks[k]
                if (
                    (
                        track.solo_checkbox.isChecked()
                        and
                        k not in self._last_solo
                    ) or (
                        not track.solo_checkbox.isChecked()
                        and
                        k in self._last_solo
                    )
                ):
                    track.solo_checkbox.trigger()
        else:
            self._last_solo.clear()
            for k in shared.TRACK_PANEL.tracks:
                track = shared.TRACK_PANEL.tracks[k]
                if track.solo_checkbox.isChecked():
                    self._last_solo.add(k)
                    track.solo_checkbox.trigger()
        self.update_solo_all()

    def unmute_all(self):
        if self.mute_checkbox.isChecked():
            for k in shared.TRACK_PANEL.tracks:
                track = shared.TRACK_PANEL.tracks[k]
                if (
                    (
                        track.mute_checkbox.isChecked()
                        and
                        k not in self._last_mute
                    ) or (
                        not track.mute_checkbox.isChecked()
                        and
                        k in self._last_mute
                    )
                ):
                    track.mute_checkbox.trigger()
        else:
            self._last_mute.clear()
            for k in shared.TRACK_PANEL.tracks:
                track = shared.TRACK_PANEL.tracks[k]
                if track.mute_checkbox.isChecked():
                    self._last_mute.add(k)
                    track.mute_checkbox.trigger()
        self.update_mute_all()

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
            # Avoid a situation where the default song is playing and
            # a different song is displaying
            sequence_lib.change_sequence(
                shared.PLAYLIST_EDITOR._current_sequence,
            )

