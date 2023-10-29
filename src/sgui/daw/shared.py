from collections import defaultdict

from sglib.models.daw import *
from sgui.sgqt import *

from sglib import constants
from sglib.log import LOG
from sglib.math import clip_min
from sglib.models import theme
from sglib.models.daw.project import DawProject
from sglib.lib import util
from sglib.lib.translate import _
from sgui import shared as glbl_shared
from sglib.models import theme
from sgui.daw.lib import item as item_lib


AUDIO_ITEMS_TO_DROP = []
MIDI_FILES_TO_DROP = []
ITEM_TO_DROP = None

def clear_seq_drop():
    global ITEM_TO_DROP
    ITEM_TO_DROP = None
    AUDIO_ITEMS_TO_DROP.clear()
    MIDI_FILES_TO_DROP.clear()

AUDIO_ITEM_HANDLE_HEIGHT = 12.0
AUDIO_ITEM_HANDLE_SIZE = 6.25

BOTTOM_LEFT_TRI = QtGui.QPolygonF()
BOTTOM_LEFT_TRI.append(
    QtCore.QPointF(0.0, 0.0)
)
BOTTOM_LEFT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    )
)
BOTTOM_LEFT_TRI.append(
    QtCore.QPointF(
        0.0,
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    ),
)
BOTTOM_LEFT_TRI.append(
    QtCore.QPointF(0.0, 0.0)
)

BOTTOM_RIGHT_TRI = QtGui.QPolygonF()
BOTTOM_RIGHT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    )
)
BOTTOM_RIGHT_TRI.append(
    QtCore.QPointF(
        0.0,
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    ),
)
BOTTOM_RIGHT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        0.0,
    ),
)
BOTTOM_RIGHT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    )
)

TOP_LEFT_TRI = QtGui.QPolygonF()
TOP_LEFT_TRI.append(
    QtCore.QPointF(0.0, 0.0)
)
TOP_LEFT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        0.0,
    )
)
TOP_LEFT_TRI.append(
    QtCore.QPointF(
        0.0,
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    ),
)
TOP_LEFT_TRI.append(
    QtCore.QPointF(0.0, 0.0)
)

TOP_RIGHT_TRI = QtGui.QPolygonF()
TOP_RIGHT_TRI.append(
    QtCore.QPointF(0.0, 0.0),
)
TOP_RIGHT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        0.0,
    ),
)
TOP_RIGHT_TRI.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    ),
)
TOP_RIGHT_TRI.append(
    QtCore.QPointF(0.0, 0.0),
)

RECT_ITEM_HANDLE = QtGui.QPolygonF()
RECT_ITEM_HANDLE.append(
    QtCore.QPointF(0.0, 0.0),
)
RECT_ITEM_HANDLE.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        0.0,
    ),
)
RECT_ITEM_HANDLE.append(
    QtCore.QPointF(
        float(AUDIO_ITEM_HANDLE_SIZE),
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    ),
)
RECT_ITEM_HANDLE.append(
    QtCore.QPointF(
        0.0,
        float(AUDIO_ITEM_HANDLE_HEIGHT),
    ),
)
RECT_ITEM_HANDLE.append(
    QtCore.QPointF(0.0, 0.0),
)

NO_PEN = QPen(QtCore.Qt.PenStyle.NoPen)
NO_PEN.setWidth(0)

CURRENT_SEQUENCE = None
CURRENT_SEQUENCE_NAME = None

TRACK_COLORS = None

DRAW_LAST_ITEMS = False

CURRENT_ITEM_NAME = None
LAST_ITEM_NAME = None
LAST_ITEM_TRACK = None
CURRENT_ITEM = None
CURRENT_ITEM_TRACK = None
CURRENT_ITEM_REF = None
LAST_ITEM = None
LAST_ITEM_REF = None
CURRENT_ITEM_LEN = 4

TAB_SEQUENCER = 0
TAB_PLUGIN_RACK = 1
TAB_ITEM_EDITOR = 2
TAB_ROUTING = 3
TAB_MIXER = 4
TAB_HARDWARE = 5
TAB_NOTES = 6

# Nested tabs within the item editor
TAB_IE_AUDIO = 0
TAB_IE_NOTES = 1
TAB_IE_CC = 2
TAB_IE_PB = 3

SEQUENCE_EDITOR_TRACK_HEIGHT = 64
constants.DAW_PROJECT = DawProject(util.WITH_AUDIO)
TRACK_NAMES = [
    "Main" if x == 0 else "track{}".format(x)
    for x in range(TRACK_COUNT_ALL)
]

# Used by the transport tool selector radio buttons
EDITOR_MODE_SELECT = 0
EDITOR_MODE_DRAW = 1
EDITOR_MODE_ERASE = 2
EDITOR_MODE_SPLIT = 3
# The global variable that editors reference on mousePressEvent
EDITOR_MODE = EDITOR_MODE_SELECT

CURSORS = {
    EDITOR_MODE_SELECT: QtCore.Qt.CursorShape.ArrowCursor,
    EDITOR_MODE_DRAW: QtCore.Qt.CursorShape.DragCopyCursor,
    EDITOR_MODE_ERASE: QtCore.Qt.CursorShape.ForbiddenCursor,
    EDITOR_MODE_SPLIT: QtCore.Qt.CursorShape.SplitHCursor,
}

IS_IN_CURSOR_WIDGET = False

def set_cursor():
    if IS_IN_CURSOR_WIDGET:
        QApplication.restoreOverrideCursor()
        shape = CURSORS[EDITOR_MODE]
        QApplication.setOverrideCursor(QCursor(shape))

def _is_move_cursor():
    return EDITOR_MODE in (EDITOR_MODE_SELECT, EDITOR_MODE_DRAW)

def set_move_cursor():
    if _is_move_cursor():
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.CursorShape.SizeAllCursor),
        )

def restore_move_cursor():
    if _is_move_cursor():
        QApplication.restoreOverrideCursor()

class HoverCursorChange(QtCore.QObject):
    def enterEvent(self, event):
        global IS_IN_CURSOR_WIDGET
        IS_IN_CURSOR_WIDGET = True
        set_cursor()

    def leaveEvent(self, event):
        global IS_IN_CURSOR_WIDGET
        IS_IN_CURSOR_WIDGET = False
        for i in range(6):
            QApplication.restoreOverrideCursor()
            if not QApplication.overrideCursor():
                break

PLAYBACK_POS = 0.0
SUPPRESS_TRACK_COMBOBOX_CHANGES = False
TRACK_NAME_COMBOBOXES = []

ITEM_REF_POS = None
MIDI_SCALE = 1.0

ALL_PEAK_METERS = defaultdict(lambda: [])

LAST_NOTE_RESIZE = 0.25

PIANO_ROLL_SNAP = False
PIANO_ROLL_GRID_WIDTH = 1000.0
PIANO_KEYS_WIDTH = 34  #Width of the piano keys in px
PIANO_ROLL_GRID_MAX_START_TIME = 999.0 + PIANO_KEYS_WIDTH
PIANO_ROLL_NOTE_HEIGHT = util.get_file_setting("PIANO_VZOOM", int, 21)
PIANO_ROLL_SNAP_DIVISOR = 4.0
PIANO_ROLL_SNAP_BEATS = 1.0
PIANO_ROLL_SNAP_VALUE = PIANO_ROLL_GRID_WIDTH / PIANO_ROLL_SNAP_DIVISOR
PIANO_ROLL_NOTE_COUNT = 120
#gets updated by the piano roll to it's real value:
PIANO_ROLL_TOTAL_HEIGHT = 1000
PIANO_ROLL_QUANTIZE_INDEX = 4
PIANO_ROLL_MIN_NOTE_LENGTH = PIANO_ROLL_GRID_WIDTH / 128.0

# Placeholders for global access to UI comonents

ATM_SEQUENCE = None
AUDIO_SEQ = None
AUDIO_SEQ_WIDGET = None
AUTOMATION_EDITORS = []
CC_EDITOR = None
CC_EDITOR_WIDGET = None
HARDWARE_WIDGET = None
ITEM_EDITOR = None
MAIN_WINDOW = None
MIDI_DEVICES_DIALOG = None
MIDI_EDITORS = None
MIXER_WIDGET = None
PB_EDITOR = None
PIANO_ROLL_EDITOR = None
PIANO_ROLL_EDITOR_WIDGET = None
PLAYLIST_EDITOR = None
ITEMLIST = None
PLUGIN_RACK = None
ROUTING_GRAPH_WIDGET = None
SEQUENCER = None
SEQ_WIDGET = None
TRACK_PANEL = None
TRANSPORT = None

def get_current_sequence_length():
    return CURRENT_SEQUENCE.get_length() if CURRENT_SEQUENCE else 32

def global_update_hidden_rows(a_val=None):
    return # TODO
#    SEQUENCE_EDITOR.setUpdatesEnabled(False)
#    if CURRENT_SEQUENCE and SEQ_WIDGET.hide_inactive:
#        f_active = {x.track_num for x in CURRENT_SEQUENCE.items}
#        for k, v in TRACK_PANEL.tracks.items():
#            v.group_box.setHidden(k not in f_active)
#    else:
#        for v in TRACK_PANEL.tracks.values():
#            v.group_box.setHidden(False)
#    SEQUENCE_EDITOR.setUpdatesEnabled(True)
#    SEQUENCE_EDITOR.update()

def global_set_midi_zoom(a_val):
    global MIDI_SCALE
    MIDI_SCALE = a_val
    set_piano_roll_quantize()


def global_open_items(
    a_items=None,
    a_reset_scrollbar=False,
    a_new_ref=None,
    item_track=None,
):
    """
        @a_items:
            str, The name of the item.
            Leave blank to reopen the existing item.
        @a_reset_scrollbar:
            bool, True to reset the horizontal scrollbar of all editors to 0
    """
    global \
        CURRENT_ITEM, \
        CURRENT_ITEM_LEN, \
        CURRENT_ITEM_NAME, \
        CURRENT_ITEM_REF, \
        CURRENT_ITEM_TRACK, \
        ITEM_REF_POS, \
        LAST_ITEM, \
        LAST_ITEM_NAME, \
        LAST_ITEM_REF, \
        LAST_ITEM_TRACK

    if a_items is not None:
        ITEM_EDITOR.clear_solo_loop()

    if item_track is not None:
        LAST_ITEM_TRACK = CURRENT_ITEM_TRACK
        CURRENT_ITEM_TRACK = item_track

    if a_new_ref:
        LAST_ITEM_REF = CURRENT_ITEM_REF
        CURRENT_ITEM_REF = a_new_ref

    if CURRENT_ITEM_REF:
        f_ref_end = (
            CURRENT_ITEM_REF.length_beats + CURRENT_ITEM_REF.start_offset
        )
        ITEM_REF_POS = (CURRENT_ITEM_REF.start_offset, f_ref_end)
    else:
        ITEM_REF_POS = (0.0, 4.0)

    if a_items is not None:
        if a_items != CURRENT_ITEM_NAME:
            # Don't allow undo/redo to items that are no
            # longer open in the editor
            constants.DAW_PROJECT.clear_undo_context(TAB_ITEM_EDITOR)
            LAST_ITEM_NAME = CURRENT_ITEM_NAME
            LAST_ITEM = CURRENT_ITEM
            CURRENT_ITEM_NAME = a_items
        ITEM_EDITOR.enabled = True
        PIANO_ROLL_EDITOR.selected_note_strings = []
        set_piano_roll_quantize()
        if a_reset_scrollbar:
            for f_editor in MIDI_EDITORS:
                f_editor.horizontalScrollBar().setSliderPosition(0)
        f_items_dict = constants.DAW_PROJECT.get_items_dict()
        f_uid = f_items_dict.get_uid_by_name(a_items)
        CURRENT_ITEM = constants.DAW_PROJECT.get_item_by_uid(f_uid)
        ITEM_EDITOR.item_name_lineedit.setText(a_items)
        ITEM_EDITOR.item_name_lineedit.setReadOnly(False)

    if CURRENT_ITEM:
        CURRENT_ITEM_LEN = CURRENT_ITEM.get_length(
            CURRENT_SEQUENCE.get_tempo_at_pos(
                CURRENT_ITEM_REF.start_beat
            )
        )
        CURRENT_ITEM_LEN = max(
            (
                CURRENT_ITEM_LEN,
                CURRENT_ITEM_REF.length_beats + CURRENT_ITEM_REF.start_offset,
            )
        )
        ITEM_EDITOR.set_active_channels(CURRENT_ITEM.get_channels())
    else:
        CURRENT_ITEM_LEN = 4
        ITEM_EDITOR.set_active_channels(tuple())

    CC_EDITOR.clear_drawn_items()
    PB_EDITOR.clear_drawn_items()
    ITEM_EDITOR.items = []
    f_cc_set = set()
    channel = ITEM_EDITOR.get_midi_channel()

    if CURRENT_ITEM:
        for cc in (x for x in CURRENT_ITEM.ccs if x.channel == channel):
            f_cc_set.add(cc.cc_num)

        CC_EDITOR_WIDGET.update_ccs_in_use(list(sorted(f_cc_set)))

        if a_items is not None and f_cc_set:
            CC_EDITOR_WIDGET.set_cc_num(sorted(f_cc_set)[0])

    #ITEM_EDITOR.tab_changed()

def global_save_and_reload_items():
    item_lib.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
    global_open_items()
    constants.DAW_PROJECT.commit(_("Edit item"))
    ITEM_EDITOR.tab_changed()

def open_last():
    if LAST_ITEM_NAME:
        global_open_items(
            LAST_ITEM_NAME,
            a_new_ref=LAST_ITEM_REF,
            item_track=LAST_ITEM_TRACK,
        )
        MAIN_WINDOW.tab_changed()
    else:
        QMessageBox.warning(
            None,
            "Error",
            (
                "You musst open at least 2 items from the sequencer to use "
                "this feature"
            ),
        )

def global_open_project(a_project_file):
    """ Opens or creates a new project """
    # TODO: SG DEPRECATED
    global PROJECT, TRACK_NAMES, TRACK_COLORS
    constants.DAW_PROJECT = DawProject(util.WITH_AUDIO)
    constants.DAW_PROJECT.suppress_updates = True
    constants.DAW_PROJECT.open_project(a_project_file, False)

    TRACK_COLORS = constants.DAW_PROJECT.get_track_colors()
    TRACK_PANEL.open_tracks()
    constants.DAW_PROJECT.suppress_updates = False
    f_scale = constants.DAW_PROJECT.get_midi_scale()
    if f_scale is not None:
        PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.setCurrentIndex(f_scale[0])
        PIANO_ROLL_EDITOR_WIDGET.scale_combobox.setCurrentIndex(f_scale[1])
    MAIN_WINDOW.open_project()
    ROUTING_GRAPH_WIDGET.draw_graph(
        constants.DAW_PROJECT.get_routing_graph(),
        TRACK_PANEL.get_track_names(),
    )
    global_open_mixer()
    MIDI_DEVICES_DIALOG.set_routings()
    SEQ_WIDGET.open_sequence()
    SEQ_WIDGET.snap_combobox.setCurrentIndex(1)
    TRANSPORT.open_project()
    PLUGIN_RACK.initialize(constants.DAW_PROJECT)
    MIXER_WIDGET.set_project(constants.DAW_PROJECT)
    PIANO_ROLL_EDITOR.default_vposition()
    TRACK_PANEL.set_track_names()
    reset_globals()

def global_new_project(a_project_file):
    # TODO: SG DEPRECATED   # EDIT: What is deprecated?
    global PROJECT, TRACK_COLORS, TRACK_NAMES
    TRACK_NAMES = [
        "Main" if x == 0 else "track{}".format(x)
        for x in range(TRACK_COUNT_ALL)
    ]
    constants.DAW_PROJECT = DawProject(util.WITH_AUDIO)
    constants.DAW_PROJECT.new_project(a_project_file)
    TRACK_COLORS = constants.DAW_PROJECT.get_track_colors()

    global_update_track_comboboxes()
    MAIN_WINDOW.new_project()
    ROUTING_GRAPH_WIDGET.scene.clear()
    global_open_mixer()
    SEQ_WIDGET.open_sequence()
    SEQ_WIDGET.snap_combobox.setCurrentIndex(1)
    PLUGIN_RACK.initialize(constants.DAW_PROJECT)
    MIXER_WIDGET.set_project(constants.DAW_PROJECT)
    PIANO_ROLL_EDITOR.default_vposition()
    TRACK_PANEL.set_track_names()
    reset_globals()

def reset_globals():
    global \
        CURRENT_ITEM, \
        CURRENT_ITEM_LEN, \
        CURRENT_ITEM_NAME, \
        CURRENT_ITEM_REF, \
        CURRENT_ITEM_TRACK, \
        ITEM_REF_POS, \
        LAST_ITEM, \
        LAST_ITEM_NAME, \
        LAST_ITEM_REF, \
        LAST_ITEM_TRACK

    CURRENT_ITEM = None
    CURRENT_ITEM_LEN = 4
    CURRENT_ITEM_NAME = None
    CURRENT_ITEM_REF = None
    CURRENT_ITEM_TRACK = None
    ITEM_REF_POS = None
    LAST_ITEM = None
    LAST_ITEM_NAME = None
    LAST_ITEM_REF = None
    LAST_ITEM_TRACK = None

def global_set_playback_pos(a_beat=None):
    if a_beat is not None:
        global PLAYBACK_POS
        PLAYBACK_POS = float(a_beat)
    TRANSPORT.set_pos_from_cursor(PLAYBACK_POS)
    for f_editor in (
        SEQUENCER,
        AUDIO_SEQ,
        PIANO_ROLL_EDITOR,
        PB_EDITOR,
        CC_EDITOR,
    ):
        f_editor.set_playback_pos(PLAYBACK_POS)
    TRANSPORT.set_time(PLAYBACK_POS)

def global_update_peak_meters(a_val):
    for f_val in a_val.split("|"):
        f_list = f_val.split(":")
        f_index = int(f_list[0])
        if f_index in ALL_PEAK_METERS:
            for f_pkm in ALL_PEAK_METERS[f_index]:
                f_pkm.set_value(f_list[1:])
        else:
            LOG.info("{} not in ALL_PEAK_METERS".format(f_index))

def active_audio_pool_uids():
    return constants.DAW_PROJECT.active_audio_pool_uids()

def global_close_all():
    global AUDIO_ITEMS_TO_DROP
    if glbl_shared.PLUGIN_UI_DICT:
        glbl_shared.PLUGIN_UI_DICT.close_all_plugin_windows()
    SEQ_WIDGET.clear_new()
    ITEM_EDITOR.clear_new()
    AUDIO_SEQ.clear_drawn_items()
    PB_EDITOR.clear_drawn_items()
    TRANSPORT.reset()
    AUDIO_ITEMS_TO_DROP = []

def global_ui_refresh_callback(a_restore_all=False):
    """ Use this to re-open all existing items/sequences/song in
        their editors when the files have been changed externally
    """
    global_open_items(CURRENT_ITEM_NAME)
    TRACK_PANEL.open_tracks()
    SEQ_WIDGET.open_sequence()
    MAIN_WINDOW.tab_changed()
    constants.DAW_PROJECT.ipc().open_song(
        constants.DAW_PROJECT.project_folder,
        a_restore_all,
    )


def on_ready():
    """ Called after re-opening the audio engine """
    # Ensure that loop mode is restored in the engine
    # to the same setting as the UI, since this is not part
    # of the saved data
    check_state = TRANSPORT.loop_mode_checkbox.isChecked()
    TRANSPORT.on_loop_mode_changed(check_state)

def get_mixer_peak_meters():
    for k, v in MIXER_WIDGET.tracks.items():
        ALL_PEAK_METERS[k].append(v.peak_meter)

def routing_graph_toggle_callback(a_src, a_dest, conn_type):
    f_graph = constants.DAW_PROJECT.get_routing_graph()
    f_result = f_graph.toggle(a_src, a_dest, conn_type)
    if f_result:
        QMessageBox.warning(MAIN_WINDOW, _("Error"), f_result)
    else:
        constants.DAW_PROJECT.save_routing_graph(f_graph)
        ROUTING_GRAPH_WIDGET.draw_graph(f_graph, TRACK_NAMES)
        constants.DAW_PROJECT.commit(_("Update routing"))


def global_open_mixer():
    """ Update the mixer to reflect the current routing and track names """
    f_graph = constants.DAW_PROJECT.get_routing_graph()
    f_track_names = {
        f_i:x
        for f_i, x in zip(
            range(
                len(TRACK_NAMES),
            ),
            TRACK_NAMES
        )
    }
    f_plugins = {}
    for k in f_track_names:
        f_track_plugins = constants.DAW_PROJECT.get_track_plugins(k)
        if f_track_plugins:
            f_plugins[k] = {x.index:x for x in f_track_plugins.plugins}
    MIXER_WIDGET.update_sends(f_graph, f_plugins)
    MIXER_WIDGET.update_track_names(
        {
            f_i: x
            for f_i, x in zip(
                range(len(TRACK_NAMES)),
                TRACK_NAMES
            )
        },
        f_graph,
    )

def set_piano_roll_quantize(a_index=None):
    global PIANO_ROLL_SNAP, PIANO_ROLL_SNAP_VALUE, PIANO_ROLL_SNAP_DIVISOR, \
        PIANO_ROLL_SNAP_BEATS, LAST_NOTE_RESIZE, PIANO_ROLL_QUANTIZE_INDEX, \
        PIANO_ROLL_MIN_NOTE_LENGTH, PIANO_ROLL_GRID_WIDTH

    if a_index is not None:
        PIANO_ROLL_QUANTIZE_INDEX = a_index

    f_width = float(PIANO_ROLL_EDITOR.rect().width()) - \
        float(PIANO_ROLL_EDITOR.verticalScrollBar().width()) - 6.0 - \
        PIANO_KEYS_WIDTH
    f_sequence_scale = f_width / 1000.0

    PIANO_ROLL_GRID_WIDTH = 1000.0 * MIDI_SCALE * f_sequence_scale

    if PIANO_ROLL_QUANTIZE_INDEX == 0:
        PIANO_ROLL_SNAP = False
    else:
        PIANO_ROLL_SNAP = True

    PIANO_ROLL_SNAP_DIVISOR = util.ITEM_SNAP_DIVISORS[
        PIANO_ROLL_QUANTIZE_INDEX
    ]

    PIANO_ROLL_SNAP_BEATS = 1.0 / PIANO_ROLL_SNAP_DIVISOR
    LAST_NOTE_RESIZE = clip_min(
        LAST_NOTE_RESIZE,
        PIANO_ROLL_SNAP_BEATS,
    )
    PIANO_ROLL_EDITOR.set_grid_div(PIANO_ROLL_SNAP_DIVISOR)
    PIANO_ROLL_SNAP_VALUE = (
        PIANO_ROLL_GRID_WIDTH
        /
        CURRENT_ITEM_LEN
        /
        PIANO_ROLL_SNAP_DIVISOR
    )
    PIANO_ROLL_MIN_NOTE_LENGTH = (
        PIANO_ROLL_GRID_WIDTH
        /
        CURRENT_ITEM_LEN
        /
        32.0
    )

def global_open_audio_items(
    a_update_viewer=True,
    a_reload=True,
):
    if a_update_viewer:
        f_selected_list = []
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_selected_list.append(str(f_item.audio_item))
        AUDIO_SEQ.setUpdatesEnabled(False)
        AUDIO_SEQ.update_zoom()
        AUDIO_SEQ.clear_drawn_items()
        if CURRENT_ITEM:
            for k, v in CURRENT_ITEM.items.items():
#                try:
                    f_graph = constants.PROJECT.get_sample_graph_by_uid(v.uid)
                    if f_graph is None:
                        LOG.info(
                            _(
                                "Error drawing item for {}, could not get "
                                "sample graph object"
                            ).format(v.uid)
                        )
                        continue
                    AUDIO_SEQ.draw_item(k, v, f_graph)
#                except:
#                    if glbl_shared.IS_PLAYING:
#                        LOG.info(_("Exception while loading {}".format(v.uid)))
#                    else:
#                        f_path = constants.PROJECT.get_wav_path_by_uid(v.uid)
#                        if os.path.isfile(f_path):
#                            f_error_msg = _(
#                                "Unknown error loading sample f_path {}, "
#                                "\n\n{}").format(f_path, locals())
#                        else:
#                            f_error_msg = _(
#                                "Error loading '{}', file does not "
#                                "exist.").format(f_path)
#                        QMessageBox.warning(
#                            MAIN_WINDOW, _("Error"), f_error_msg)
        for f_item in AUDIO_SEQ.audio_items:
            if str(f_item.audio_item) in f_selected_list:
                f_item.setSelected(True)
        AUDIO_SEQ.setUpdatesEnabled(True)
        AUDIO_SEQ.update()
        AUDIO_SEQ.horizontalScrollBar().setMinimum(0)

def global_update_track_comboboxes(a_index=None, a_value=None):
    if (
        a_index is not None
        and
        a_value is not None
    ):
        TRACK_NAMES[int(a_index)] = str(a_value)
    global SUPPRESS_TRACK_COMBOBOX_CHANGES
    SUPPRESS_TRACK_COMBOBOX_CHANGES = True
    for f_cbox in TRACK_NAME_COMBOBOXES:
        f_current_index = f_cbox.currentIndex()
        f_cbox.clear()
        f_cbox.clearEditText()
        f_cbox.addItems(TRACK_NAMES)
        f_cbox.setCurrentIndex(f_current_index)

    PLUGIN_RACK.set_track_names(TRACK_NAMES)

    SUPPRESS_TRACK_COMBOBOX_CHANGES = False
    ROUTING_GRAPH_WIDGET.draw_graph(
        constants.DAW_PROJECT.get_routing_graph(),
        TRACK_PANEL.get_track_names(),
    )
    global_open_mixer()

def seconds_to_beats(a_seconds):
    return a_seconds * (
        CURRENT_SEQUENCE.get_tempo_at_pos(
            CURRENT_ITEM_REF.start_beat
        ) / 60.0
    )

def open_rack(track_index: int):
    """ Open a particular track in the plugin rack
    """
    if track_index is None:
        QMessageBox.warning(
            None,
            "Error",
            "You musst open an item first",
        )
        return
    PLUGIN_RACK.set_index(track_index)
    MAIN_WINDOW.setCurrentIndex(TAB_PLUGIN_RACK)

def setup():
    global \
        AUDIO_ITEM_HANDLE_PEN, \
        AUDIO_ITEM_LINE_PEN, \
        AUDIO_ITEM_HANDLE_SELECTED_PEN, \
        AUDIO_ITEM_LINE_SELECTED_PEN, \
        SPLIT_LINE_PEN

    AUDIO_ITEM_HANDLE_PEN = QPen(
        QColor(theme.SYSTEM_COLORS.daw.seq_item_handle),
    )
    AUDIO_ITEM_LINE_PEN = QPen(
        QColor(theme.SYSTEM_COLORS.daw.seq_item_handle),
        2.0,
    )
    AUDIO_ITEM_HANDLE_SELECTED_PEN = QPen(
        QColor(theme.SYSTEM_COLORS.daw.seq_item_handle_selected),
    )
    AUDIO_ITEM_LINE_SELECTED_PEN = QPen(
        QColor(theme.SYSTEM_COLORS.daw.seq_item_handle_selected),
        2.0,
    )
    SPLIT_LINE_PEN = QPen(
        QColor(theme.SYSTEM_COLORS.daw.seq_item_handle_selected),
        3.0,
    )

# Only functions, globals must accessed through the module
__all__ = [
    'active_audio_pool_uids',
    'get_mixer_peak_meters',
    'global_close_all',
    'global_new_project',
    'global_open_audio_items',
    'global_open_items',
    'global_open_mixer',
    'global_open_project',
    'global_save_and_reload_items',
    'global_set_midi_zoom',
    'global_set_playback_pos',
    'global_ui_refresh_callback',
    'global_update_hidden_rows',
    'global_update_peak_meters',
    'global_update_track_comboboxes',
    'on_ready',
    'open_last',
    'get_current_sequence_length',
    'seconds_to_beats',
    'set_piano_roll_quantize',
    'routing_graph_toggle_callback',
    'HoverCursorChange',
    'set_cursor',
]
