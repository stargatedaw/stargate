from . import shared
from .sgqt import (
    QDesktopServices,
    QMessageBox,
    QtCore,
)
from sglib.lib.updates import check_for_updates
from sglib.log import LOG

TIMER = None

def ui_check_updates():
    def go_to_releases_page():
        global TIMER
        url = QtCore.QUrl(
            "https://github.com/stargatedaw/stargate/releases",
        )
        QDesktopServices.openUrl(url)
        shared.IGNORE_CLOSE_EVENT = False
        TIMER = QtCore.QTimer()
        TIMER.timeout.connect(shared.MAIN_STACKED_WIDGET.close)
        TIMER.start(2000)
    try:
        update = check_for_updates()
    except Exception as ex:
        QMessageBox.warning(None, 'Error', f'Update check failed: {ex}')
        LOG.exception(ex)
        return
    if update[0]:
        QMessageBox.question(
            None,
            'Update available!',
            (
                f'{update[1]} installed, {update[2]} is available.\n'
                'Close Stargate and go to download page?'
            ),
            (
                QMessageBox.StandardButton.Yes
                |
                QMessageBox.StandardButton.No
            ),
            callbacks={
                QMessageBox.StandardButton.Yes: go_to_releases_page,
            }
        )
    else:
        QMessageBox.information(
            None,
            "No update available",
            f'{update[2]} is the latest, {update[1]} already installed',
        )
