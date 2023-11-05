from .abstract import AbstractItemEditor
from .audio._shared import set_audio_snap
from .automation import AutomationEditorWidget
from sglib import constants
from sgui.daw import shared
from sgui.daw.lib import item as item_lib
from sgui.daw.shared import *
from sglib.constants import MIDI_CHANNELS
from sglib.lib import util
from sglib.lib.util import *
from sglib.lib.translate import _
from sglib.models.daw import loop_marker
from sglib.models.theme import get_asset_path
from sgui.sgqt import *


class ItemEditorWidget:
    """ This is the "Item Editor" tab in MainWindow
    """
    def __init__(self):
        self.enabled = False
        self.events_follow_default = True

        self.widget = QWidget()
        self.widget.setContentsMargins(0, 0, 0, 0)
        self.main_vlayout = QVBoxLayout()
        self.main_vlayout.setContentsMargins(0, 0, 0, 0)
        self.main_vlayout.setSpacing(0)
        self.widget.setLayout(self.main_vlayout)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName('item_editor')
        self.main_vlayout.addWidget(self.tab_widget)

        shared.AUDIO_SEQ_WIDGET.hsplitter.insertWidget(
            0,
            shared.AUDIO_SEQ_WIDGET.widget,
        )
        self.tab_widget.addTab(
            shared.AUDIO_SEQ_WIDGET.hsplitter,
            _("Audio"),
        )

        self.piano_roll_tab = QWidget()
        self.piano_roll_tab.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(
            self.piano_roll_tab,
            _("Piano Roll"),
        )
        self.cc_tab = QWidget()
        self.cc_tab.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(
            self.cc_tab,
            _("CC"),
        )
        self.cc_vlayout = QVBoxLayout(self.cc_tab)
        self.cc_vlayout.setContentsMargins(0, 0, 0, 0)
        self.cc_vlayout.setSpacing(0)
        self.cc_vlayout.addWidget(shared.CC_EDITOR_WIDGET.widget)

        self.pitchbend_tab = QWidget()
        self.pitchbend_tab.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(
            self.pitchbend_tab,
            _("Pitchbend"),
        )

        self.piano_roll_hlayout = QHBoxLayout(self.piano_roll_tab)
        self.piano_roll_hlayout.setSpacing(0)
        self.piano_roll_hlayout.setContentsMargins(0, 0, 0, 0)
        self.piano_roll_hlayout.addWidget(
            shared.PIANO_ROLL_EDITOR_WIDGET.widget,
        )

        self.pb_viewer_widget = AutomationEditorWidget(
            shared.PB_EDITOR,
            False,
        )
        self.pb_hlayout = QHBoxLayout()
        self.pb_hlayout.setSpacing(0)
        self.pb_hlayout.setContentsMargins(0, 0, 0, 0)
        self.pitchbend_tab.setLayout(self.pb_hlayout)
        self.pb_auto_vlayout = QVBoxLayout()
        self.pb_auto_vlayout.setSpacing(0)
        self.pb_auto_vlayout.setContentsMargins(0, 0, 0, 0)
        self.pb_hlayout.addLayout(self.pb_auto_vlayout)
        self.pb_auto_vlayout.addWidget(self.pb_viewer_widget.widget)

        self.zoom_widget = QWidget()
        #self.zoom_widget.setContentsMargins(0, 0, 2, 0)
        self.zoom_hlayout = QHBoxLayout(self.zoom_widget)
        self.zoom_hlayout.setContentsMargins(2, 0, 2, 0)
        #self.zoom_hlayout.setSpacing(0)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(16, 16))
        self.zoom_hlayout.addWidget(self.toolbar)

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

        self.open_last_action = QAction(
            _("Open Last Item"),
            self.menu,
        )
        self.menu.addAction(self.open_last_action)
        self.open_last_action.setToolTip(
            'Open the previously opened sequencer item.  Use this to rapidly '
            'switch between 2 related sequencer items that you are editing'
        )
        self.open_last_action.triggered.connect(shared.open_last)
        self.open_last_action.setShortcut(QKeySequence.fromString("ALT+F"))

        self.open_rack_action = QAction(
            _("Open Plugin Rack For Item"),
            self.menu,
        )
        self.menu.addAction(self.open_rack_action)
        self.open_rack_action.setToolTip(
            'Open the plugin rack for this item.  If the item exists on '
            'multiple tracks, open the track that the item was double-clicked '
            'on'
        )
        self.open_rack_action.triggered.connect(
            lambda: shared.open_rack(shared.CURRENT_ITEM_TRACK)
        )

        # Loop button
        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('loop-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('loop-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.loop_mode_checkbox = QAction(icon, '', self.toolbar)
        self.loop_mode_checkbox.setToolTip(
            'Toggle looping the current item. Set the sequencer region to the '
            'start and end of this item, set the playback cursor to the '
            'beginning of the item and enable looping in the transport.  '
        )
        self.loop_mode_checkbox.setCheckable(True)
        self.toolbar.addAction(self.loop_mode_checkbox)
        self.loop_mode_checkbox.triggered.connect(self.on_loop_mode_changed)

        # Solo
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
            'Toggle soloing the track of the current item being edited.  This '
            'does not alter the solo state of other tracks, if you are '
            'already soloing any other tracks you will still hear them'
        )
        self.solo_checkbox.setCheckable(True)
        self.toolbar.addAction(self.solo_checkbox)
        self.solo_checkbox.triggered.connect(self.solo_pressed)

        # MIDI Channel
        self.midi_channel_combobox = QComboBox()
        self.midi_channel_combobox.setMinimumWidth(48)
        self.midi_channel_combobox.setToolTip(
            'The MIDI channel to view and edit note, CC and pitchbend events '
            'on.  Use multiple MIDI channels to send different MIDI events '
            'to different plugins in the same rack.  Channels with events '
            'have a (*)'
        )
        self.midi_channel_combobox.addItems(MIDI_CHANNELS)
        self.zoom_hlayout.addWidget(QLabel('MIDI Channel'))
        self.zoom_hlayout.addWidget(self.midi_channel_combobox)

        self.midi_channel_combobox.currentIndexChanged.connect(
            self.channel_changed
        )

        self.snap_combobox = QComboBox()
        self.snap_combobox.setToolTip(
            'Snap to grid for audio items and MIDI notes.  Adding or moving '
            'items will be quantized to this length'
        )
        self.snap_combobox.setMinimumWidth(90)
        self.snap_combobox.addItems([
            _("None"),
            "1/4",
            "1/8",
            "1/12",
            "1/16",
            "1/32",
            "1/64",
            "1/128",
        ])
        self.zoom_hlayout.addWidget(QLabel(_("Snap:")))
        self.zoom_hlayout.addWidget(self.snap_combobox)
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        self.item_name_lineedit = QLineEdit()
        self.item_name_lineedit.setToolTip(
            'The name of the sequencer item being edited, double click an '
            'item in the sequencer to open.  You can edit item names here '
            'or by right clicking in the sequencer'
        )
        self.item_name_lineedit.setReadOnly(True)
        self.item_name_lineedit.editingFinished.connect(self.on_item_rename)
        self.item_name_lineedit.setMinimumWidth(150)
        self.zoom_hlayout.addWidget(self.item_name_lineedit)

        self.zoom_hlayout.addWidget(QLabel("H"))
        self.zoom_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.zoom_slider.setToolTip(
            'Horizontal zoom for all of the item editors.  Some item editors '
            'have independent vertical zoom sliders on their own tab'
        )
        self.zoom_hlayout.addWidget(self.zoom_slider)
        self.zoom_slider.setObjectName("zoom_slider")
        self.zoom_slider.setRange(10, 100)
        self.zoom_slider.valueChanged.connect(self.set_midi_zoom)
        self.tab_widget.setCornerWidget(self.zoom_widget)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.default_note_start = 0.0
        self.default_note_length = 1.0
        self.default_note_note = 0
        self.default_note_octave = 3
        self.default_note_velocity = 100
        self.default_cc_num = 0
        self.default_cc_start = 0.0
        self.default_cc_val = 0
        self.default_quantize = 5
        self.default_pb_start = 0
        self.default_pb_val = 0
        self.default_pb_quantize = 0

    def channel_changed(self, idx=None):
        shared.PIANO_ROLL_EDITOR.selected_note_strings = []
        shared.global_open_items()
        self.tab_changed()

    def set_active_channels(self, channels: int):
        """ Update the channels combobox to show active channels  """
        for i, name in zip(range(len(MIDI_CHANNELS)), MIDI_CHANNELS):
            self.midi_channel_combobox.setItemText(
                i,
                name+'*' if i in channels else name,
            )

    def on_play(self):
        self.menu_button.setEnabled(False)
        self.loop_mode_checkbox.setEnabled(False)

    def on_stop(self):
        self.menu_button.setEnabled(True)
        self.loop_mode_checkbox.setEnabled(True)

    def clear_solo_loop(self):
        if self.solo_checkbox.isChecked():
            self.solo_checkbox.trigger()
        if self.loop_mode_checkbox.isChecked():
            self.loop_mode_checkbox.trigger()

    def solo_pressed(self, val=None):
        if shared.CURRENT_ITEM_TRACK is None:
            self.solo_checkbox.setChecked(False)
            return
        track = shared.TRACK_PANEL.tracks[shared.CURRENT_ITEM_TRACK]
        soloed = track.solo_checkbox.isChecked()
        if val != soloed:
            track.solo_checkbox.trigger()

    def on_loop_mode_changed(self, val=None):
        if not shared.CURRENT_ITEM_REF:
            self.loop_mode_checkbox.setChecked(False)
            return
        if val:
            if shared.CURRENT_SEQUENCE.loop_marker:
                self._loop_orig = (
                    shared.CURRENT_SEQUENCE.loop_marker.start_beat,
                    shared.CURRENT_SEQUENCE.loop_marker.beat,
                )
            else:
                self._loop_orig = None
            self._loop_enabled = \
                shared.TRANSPORT.loop_mode_checkbox.isChecked()
            self._loop_pos = shared.SEQUENCER.playback_pos
            marker = loop_marker(
                (
                    shared.CURRENT_ITEM_REF.start_beat
                    +
                    shared.CURRENT_ITEM_REF.length_beats
                ),
                shared.CURRENT_ITEM_REF.start_beat,
            )
            shared.CURRENT_SEQUENCE.set_loop_marker(marker)
            shared.global_set_playback_pos(shared.CURRENT_ITEM_REF.start_beat)
            if not self._loop_enabled:
                shared.TRANSPORT.loop_mode_checkbox.trigger()
        else:
            if self._loop_orig:
                shared.CURRENT_SEQUENCE.loop_marker.beat = self._loop_orig[1]
                shared.CURRENT_SEQUENCE.loop_marker.start_beat = \
                    self._loop_orig[0]
            if (
                shared.TRANSPORT.loop_mode_checkbox.isChecked()
                !=
                self._loop_enabled
            ):
                shared.TRANSPORT.loop_mode_checkbox.trigger()
            shared.global_set_playback_pos(self._loop_pos)
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        shared.SEQ_WIDGET.open_sequence()

    def get_midi_channel(self):
        return self.midi_channel_combobox.currentIndex()

    def on_item_rename(self, a_val=None):
        name = str(self.item_name_lineedit.text()).strip()
        # Avoid shenanigans when Qt calls this event when the widget is not
        # even focused or being edited
        if name == shared.CURRENT_ITEM_NAME:
            return
        constants.DAW_PROJECT.rename_items([shared.CURRENT_ITEM_NAME], name)
        constants.DAW_PROJECT.commit(_("Rename items"))
        items_dict = constants.DAW_PROJECT.get_items_dict()
        name = items_dict.get_name_by_uid(shared.CURRENT_ITEM.uid)
        self.item_name_lineedit.setText(name)
        shared.global_open_items(name)

    def set_snap(self, a_val=None):
        f_index = self.snap_combobox.currentIndex()
        set_piano_roll_quantize(f_index)
        set_audio_snap(f_index)
        if shared.CURRENT_ITEM:
            shared.PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
            self.tab_changed()
        else:
            shared.PIANO_ROLL_EDITOR.clear_drawn_items()

    def clear_new(self):
        self.enabled = False
        shared.PIANO_ROLL_EDITOR.clear_drawn_items()
        self.item = None

    def quantize_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def quantize_ok_handler():
            f_quantize_text = f_quantize_combobox.currentText()
            self.events_follow_default = f_events_follow_notes.isChecked()
            f_clip = shared.CURRENT_ITEM.quantize(
                f_quantize_text,
                self.get_midi_channel(),
                f_events_follow_notes.isChecked(),
                a_selected_only=f_selected_only.isChecked(),
            )
            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )

            if f_selected_only.isChecked():
                shared.PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                shared.PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            shared.PIANO_ROLL_EDITOR.draw_item()
            constants.DAW_PROJECT.commit(_("Quantize item(s)"))
            f_window.close()

        def quantize_cancel_handler():
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Quantize"))
        vlayout = QVBoxLayout()
        f_window.setLayout(vlayout)
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)

        f_layout.addWidget(QLabel(_("Quantize")), 0, 0)
        f_quantize_combobox = QComboBox()
        f_quantize_combobox.setToolTip('The note length to quantize items to')
        f_quantize_combobox.addItems(BAR_FRACS)
        f_layout.addWidget(f_quantize_combobox, 0, 1)
        f_events_follow_notes = QCheckBox(
            _("CCs and pitchbend follow notes?"))
        f_events_follow_notes.setChecked(self.events_follow_default)
        f_layout.addWidget(f_events_follow_notes, 1, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(quantize_ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_selected_only = QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 2, 1)

        vlayout.addLayout(f_ok_cancel_layout)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(quantize_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec()

    def transpose_dialog(self, a_selected_only=False, channel=None):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def transpose_ok_handler():
            f_clip = shared.CURRENT_ITEM.transpose(
                f_semitone.value(),
                f_octave.value(),
                a_selected_only=f_selected_only.isChecked(),
                a_duplicate=f_duplicate_notes.isChecked(),
                channel=channel,
            )
            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )

            if f_selected_only.isChecked():
                shared.PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                shared.PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            shared.PIANO_ROLL_EDITOR.draw_item()
            constants.DAW_PROJECT.commit(_("Transpose item(s)"))
            f_window.close()

        def transpose_cancel_handler():
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Transpose"))
        vlayout = QVBoxLayout()
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_window.setLayout(vlayout)

        f_semitone = QSpinBox()
        f_semitone.setRange(-12, 12)
        f_semitone.setToolTip(
            'The number of semitones to transpose the notes by'
        )
        f_layout.addWidget(QLabel(_("Semitones")), 0, 0)
        f_layout.addWidget(f_semitone, 0, 1)
        f_octave = QSpinBox()
        f_octave.setToolTip(
            'The number of octaves to transpose the notes by'
        )
        f_octave.setRange(-5, 5)
        f_layout.addWidget(QLabel(_("Octaves")), 1, 0)
        f_layout.addWidget(f_octave, 1, 1)
        f_duplicate_notes = QCheckBox(_("Duplicate notes?"))
        f_duplicate_notes.setToolTip(_(
            "Checking this box causes the transposed notes "
            "to be added rather than moving the existing notes."
        ))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_selected_only = QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 4, 1)
        f_ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(f_ok_cancel_layout)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_ok_cancel_layout.addWidget(f_ok)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec()

    def set_transport_tool_visibility(self, index=None):
        if index is None:
            index = self.tab_widget.currentIndex()
        args = {
            shared.TAB_IE_AUDIO: {"draw": False},
            shared.TAB_IE_NOTES: {"split": False},
            shared.TAB_IE_CC: {"erase": False, "split": False},
            shared.TAB_IE_PB: {"erase": False, "split": False},
        }
        shared.TRANSPORT.set_tool_button_visibility(**args[index])

    def tab_changed(self, a_val=None):
        f_list = [
            shared.AUDIO_SEQ,
            shared.PIANO_ROLL_EDITOR,
            shared.CC_EDITOR,
            shared.PB_EDITOR,
        ]
        f_index = self.tab_widget.currentIndex()
        self.set_transport_tool_visibility(f_index)
        if f_index == 0:
            global_open_audio_items()
        else:
            if f_index == 1:
                set_piano_roll_quantize()
            if f_index < len(f_list):
                f_list[f_index].draw_item()
            shared.PIANO_ROLL_EDITOR.click_enabled = True
            #^^^^huh?

    def show_not_enabled_warning(self):
        QMessageBox.warning(
            shared.MAIN_WINDOW,
            _("Error"),
           _(
               "You must open an item first by double-clicking on one in "
               "the 'Sequencer' tab."
            ),
        )

    def set_midi_zoom(self, a_val):
        global_set_midi_zoom(a_val * 0.1)
        #global_open_items()
        shared.AUDIO_SEQ.set_zoom(float(a_val) * 0.1)
        self.tab_changed()

    def increment_hzoom(self, up):
        inc = 1 if up else -1
        self.zoom_slider.setValue(
            self.zoom_slider.value() + inc,
        )

    def add_cc(self, a_cc):
        shared.CURRENT_ITEM.add_cc(a_cc)

    def add_note(self, a_note):
        shared.CURRENT_ITEM.add_note(a_note, False)

    def add_pb(self, a_pb):
        shared.CURRENT_ITEM.add_pb(a_pb)

