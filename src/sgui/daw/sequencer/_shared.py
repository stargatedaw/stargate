from .  import _shared
from sglib import constants
from sgui import shared as glbl_shared
from sgui.daw import shared
from sglib.models.daw import *
from sglib.lib.translate import _
from sglib.lib import util
from sglib.math import clip_min, clip_value
from sgui.sgqt import *


DRAW_SEQUENCER_GRAPHS = True
CACHED_SEQ_LEN = 32
LAST_ITEM_LENGTH = 4
SEQUENCE_EDITOR_MODE = 0

ATM_CLIPBOARD = []
SEQUENCE_CLIPBOARD = []

SEQUENCE_EDITOR_HEADER_ROW_HEIGHT = 18
SEQUENCE_EDITOR_HEADER_HEIGHT = SEQUENCE_EDITOR_HEADER_ROW_HEIGHT * 3

SEQUENCE_TRACK_WIDTH = 135  #Width of the tracks in px
SEQUENCE_EDITOR_TRACK_COUNT = 32

SEQUENCER_PX_PER_BEAT = 24
SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT
SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
SEQ_QUANTIZE = True

ATM_POINT_DIAMETER = 10.0
ATM_POINT_RADIUS = ATM_POINT_DIAMETER * 0.5

#gets updated by the sequence editor to it's real value:
SEQUENCE_EDITOR_TOTAL_HEIGHT = (
    SEQUENCE_EDITOR_TRACK_COUNT
    *
    shared.SEQUENCE_EDITOR_TRACK_HEIGHT
)

SEQUENCER_SNAP_VAL = 3
SEQ_QUANTIZE_AMT = 1.0
SEQ_LINES_ENABLED = False
SEQ_SNAP_RANGE = 8

SEQUENCE_EDITOR_DELETE_MODE = False

def pos_to_beat_and_track(a_pos):
    f_beat_frac = (a_pos.x() / SEQUENCER_PX_PER_BEAT)
    f_beat_frac = clip_min(f_beat_frac, 0.0)
    f_beat_frac = quantize(f_beat_frac)

    f_lane_num = int((a_pos.y() - SEQUENCE_EDITOR_HEADER_HEIGHT) /
        shared.SEQUENCE_EDITOR_TRACK_HEIGHT)
    f_lane_num = clip_value(
        f_lane_num,
        0,
        TRACK_COUNT_ALL - 1,
    )

    return f_beat_frac, f_lane_num

def quantize(a_beat):
    if SEQ_QUANTIZE:
        return int(a_beat * SEQ_QUANTIZE_AMT) / SEQ_QUANTIZE_AMT
    else:
        return a_beat

def set_seq_snap(a_val=None):
    global \
        SEQUENCER_SNAP_VAL, \
        SEQ_LINES_ENABLED, \
        SEQ_QUANTIZE_AMT, \
        SEQ_SNAP_RANGE, \
        SEQUENCER_QUANTIZE_PX
    if a_val is None:
        a_val = SEQUENCER_SNAP_VAL
    else:
        SEQUENCER_SNAP_VAL = a_val
    SEQ_SNAP_RANGE = 8
    f_divisor = util.ITEM_SNAP_DIVISORS[a_val]
    if a_val > 0:
        SEQ_QUANTIZE = True
        SEQ_LINES_ENABLED = False
        SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT / f_divisor
    else:
        SEQ_QUANTIZE = False
        SEQ_LINES_ENABLED = False
        SEQUENCER_QUANTIZE_PX = 1
    SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
    SEQ_QUANTIZE_AMT = f_divisor

def copy_selected():
    if not shared.SEQUENCER.enabled:
        shared.SEQUENCER.warn_no_sequence_selected()
        return
    if SEQUENCE_EDITOR_MODE == 0:
        global SEQUENCE_CLIPBOARD
        SEQUENCE_CLIPBOARD = [
            x.audio_item.clone()
            for x in shared.SEQUENCER.get_selected_items()
        ]
        if SEQUENCE_CLIPBOARD:
            SEQUENCE_CLIPBOARD.sort()
            f_start = int(SEQUENCE_CLIPBOARD[0].start_beat)
            for f_item in SEQUENCE_CLIPBOARD:
                f_item.start_beat -= f_start
    elif SEQUENCE_EDITOR_MODE == 1:
        global ATM_CLIPBOARD
        ATM_CLIPBOARD = [
            x.item.clone()
            for x in shared.SEQUENCER.get_selected_points(
                shared.SEQUENCER.current_coord[0]
            )
        ]
        if ATM_CLIPBOARD:
            ATM_CLIPBOARD.sort()
            f_start = int(ATM_CLIPBOARD[0].beat)
            for f_item in ATM_CLIPBOARD:
                f_item.beat -= f_start

def paste_orig():
    _paste()

def paste_selected():
    _paste(False)

def _paste(orig=True):
    if (
        glbl_shared.IS_PLAYING
        or
        not shared.SEQUENCER.current_coord
    ):
        return
    shared.SEQUENCER.scene.clearSelection()
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_beat = int(f_beat)
    if SEQUENCE_EDITOR_MODE == 0:
        if not SEQUENCE_CLIPBOARD:
            return
        shared.SEQUENCER.selected_item_strings = set()
        track_start = min(x.track_num for x in SEQUENCE_CLIPBOARD)
        for f_item in SEQUENCE_CLIPBOARD:
            f_new_item = f_item.clone()
            f_new_item.start_beat += f_beat
            if not orig:
                f_new_item.track_num += -track_start + f_track
            shared.CURRENT_SEQUENCE.add_item_ref_by_uid(f_new_item)
            shared.SEQUENCER.selected_item_strings.add(str(f_new_item))
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        shared.SEQ_WIDGET.open_sequence()
    elif SEQUENCE_EDITOR_MODE == 1:
        if not ATM_CLIPBOARD:
            return
        f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(
            shared.SEQUENCER.current_coord[0],
        )
        if f_track_port_num is None:
            QMessageBox.warning(
                shared.SEQUENCER,
                _("Error"),
                _("No automation selected for this track"),
            )
            return
        f_track_params = shared.TRACK_PANEL.get_atm_params(f_track)
        f_end = ATM_CLIPBOARD[-1].beat + f_beat
        f_point = ATM_CLIPBOARD[0]
        shared.ATM_SEQUENCE.clear_range(
            f_point.index,
            f_point.port_num,
            f_beat,
            f_end,
        )
        for f_point in ATM_CLIPBOARD:
            shared.ATM_SEQUENCE.add_point(
                DawAtmPoint(
                    f_point.beat + f_beat,
                    f_track_port_num,
                    f_point.cc_val,
                    *f_track_params,
                ),
            )
        shared.SEQUENCER.automation_save_callback()
        shared.SEQUENCER.open_atm_sequence()

def delete_selected():
    if shared.SEQUENCER.check_running():
        return
    if SEQUENCE_EDITOR_MODE == 0:
        f_item_list = shared.SEQUENCER.get_selected()
        shared.SEQUENCER.clear_selected_item_strings()
        if f_item_list:
            for f_item in f_item_list:
                shared.CURRENT_SEQUENCE.remove_item_ref(f_item.audio_item)
            constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
            constants.DAW_PROJECT.commit(_("Delete item(s)"))
            shared.SEQ_WIDGET.open_sequence()
            glbl_shared.clean_audio_pool()
    elif SEQUENCE_EDITOR_MODE == 1:
        for f_point in shared.SEQUENCER.get_selected_points():
            shared.ATM_SEQUENCE.remove_point(f_point.item)
        shared.SEQUENCER.automation_save_callback()

def init():
    global copy_action, delete_action, SEQUENCE_EDITOR_MODE
    SEQUENCE_EDITOR_MODE = 0
    copy_action = QAction(
        parent=shared.SEQUENCER,
        text=_("Copy"),
    )
    copy_action.setToolTip('Copy selected items to the clipboard')
    copy_action.triggered.connect(copy_selected)
    copy_action.setShortcut(QKeySequence.StandardKey.Copy)

    delete_action = QAction(text=_("Delete"))
    delete_action.setToolTip('Delete selected items')
    delete_action.triggered.connect(delete_selected)
    delete_action.setShortcut(QKeySequence.StandardKey.Delete)
