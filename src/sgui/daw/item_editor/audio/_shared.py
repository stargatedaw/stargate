from sglib import constants
from sglib.lib.util import pi_path
from sglib.log import LOG
from sgui.sgqt import *
import os


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
            shared.MAIN_WINDOW,
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
                shared.MAIN_WINDOW,
                _("Error"),
                _("{} is not a valid file").format(f_path),
            )
    return None

