from sglib.log import LOG
from sgui.sgqt import *
import os

CURRENT_AUDIO_ITEM_INDEX = None
# The currently selected audio item
CURRENT_ITEM = None

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

