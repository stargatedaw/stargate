from .sgqt import (
    QMessageBox,
    QtCore,
    QDesktopServices,
)
from sglib.lib.updates import check_for_updates
from sglib.log import LOG


def ui_check_updates():
    def go_to_releases_page():
        url = QtCore.QUrl(
            "https://github.com/stargatedaw/stargate/releases",
        )
        QDesktopServices.openUrl(url)
    try:
        update = check_for_updates()
    except Exception as ex:
        QMessageBox.warning(None, 'Error', f'Update check failed: {ex}')
        LOG.exception(ex)
        return
    if update:
        QMessageBox.question(
            None,
            'Update available!',
            f'{update} is available. Go to download page?',
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
            'You are already running the latest version of Stargate DAW',
        )
