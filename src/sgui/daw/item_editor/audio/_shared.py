from sglib import constants
from sglib.math import clip_value
from sglib.lib.util import pi_path, ITEM_SNAP_DIVISORS
from sglib.log import LOG
from sgui import shared as glbl_shared
from sgui.sgqt import *
import os

AUDIO_QUANTIZE = False
AUDIO_QUANTIZE_PX = 100.0
AUDIO_QUANTIZE_AMT = 1.0
AUDIO_LINES_ENABLED = True
AUDIO_SNAP_RANGE = 8
AUDIO_SNAP_VAL = 2
AUDIO_PX_PER_BEAT = 100.0

AUDIO_RULER_HEIGHT = 20.0
AUDIO_ITEM_HEIGHT = 75.0

AUDIO_ITEM_MAX_LANE = 23
AUDIO_ITEM_LANE_COUNT = 24

PAINTER_PATH_CACHE = {}

CURRENT_AUDIO_ITEM_INDEX = None
# The currently selected audio item
CURRENT_ITEM = None

def remove_path_from_painter_path_cache(path):
    path = pi_path(path)
    audio_pool = constants.PROJECT.get_audio_pool()
    by_path = audio_pool.by_path()
    if path in by_path:
        LOG.info('Removing {path} from audio item painter path cache')
        uid = by_path[path].uid
        remove_uid_from_painter_path_cache(uid)
    else:
        LOG.info(
            '{path} not in {by_path}, not removing from audio item '
            'painter path cache'
        )


def remove_uid_from_painter_path_cache(uid):
    if uid in PAINTER_PATH_CACHE:
        LOG.info(f'Removing {uid} from audio item painter path cache')
        PAINTER_PATH_CACHE.pop(uid)
    else:
        LOG.info(
            f'{uid} not in {PAINTER_PATH_CACHE}, not removing from '
            'painter path cache'
        )

def global_get_audio_file_from_clipboard():
    f_clipboard = QApplication.clipboard()
    f_path = f_clipboard.text()
    if not f_path:
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW,
            _("Error"),
            _("No text in the system clipboard"),
        )
    else:
        f_path = str(f_path).strip()
        if os.path.isfile(f_path):
            LOG.info(f_path)
            return f_path
        else:
            f_path = f_path[:100]
            QMessageBox.warning(
                glbl_shared.MAIN_WINDOW,
                _("Error"),
                _("{} is not a valid file").format(f_path),
            )
    return None

def set_audio_snap(a_val):
    global \
        AUDIO_QUANTIZE, \
        AUDIO_QUANTIZE_PX, \
        AUDIO_QUANTIZE_AMT, \
        AUDIO_SNAP_VAL, \
        AUDIO_LINES_ENABLED, \
        AUDIO_SNAP_RANGE

    AUDIO_SNAP_VAL = a_val
    AUDIO_QUANTIZE = True
    AUDIO_LINES_ENABLED = True
    AUDIO_SNAP_RANGE = 8

    f_divisor = ITEM_SNAP_DIVISORS[a_val]

    AUDIO_QUANTIZE_PX = AUDIO_PX_PER_BEAT / f_divisor
    AUDIO_SNAP_RANGE = int(f_divisor)
    AUDIO_QUANTIZE_AMT = f_divisor

    if a_val == 0:
        AUDIO_QUANTIZE = False
        AUDIO_LINES_ENABLED = False
    elif a_val == 1:
        AUDIO_LINES_ENABLED = False

def quantize_all(a_x, _round=True):
    func = round if _round else int
    if AUDIO_QUANTIZE:
        a_x = func(a_x / AUDIO_QUANTIZE_PX) * AUDIO_QUANTIZE_PX
    return a_x

def quantize(a_x):
    f_x = quantize_all(a_x)
    if AUDIO_QUANTIZE and f_x < AUDIO_QUANTIZE_PX:
        f_x = AUDIO_QUANTIZE_PX
    return f_x

def quantize_start(a_x, _min):
    f_x = quantize_all(a_x)
    if f_x >= _min:
        f_x -= AUDIO_QUANTIZE_PX
    return f_x

def y_to_lane(y):
    lane = int(
        (y - AUDIO_RULER_HEIGHT) / AUDIO_ITEM_HEIGHT
    )
    return clip_value(lane, 0, AUDIO_ITEM_MAX_LANE)

def lane_to_y(lane):
    lane = clip_value(
        lane,
        0,
        AUDIO_ITEM_MAX_LANE,
    )
    return (lane * AUDIO_ITEM_HEIGHT) + AUDIO_RULER_HEIGHT

