from sglib.models import theme
from sgui import shared
from sgui.util import svg_to_pixmap, ui_scaler_factory
from sgui.sgqt import QSplashScreen, QtCore
import os


class SplashScreen(QSplashScreen):
    def __init__(self, screen_height):
        scaled_height = int(screen_height * 0.9)
        self.pixmap = svg_to_pixmap(
            os.path.join(
                theme.ASSETS_DIR,
                theme.SYSTEM_COLORS.widgets.splash_screen,
            ),
            height=scaled_height,
        )
        QSplashScreen.__init__(
            self,
            self.pixmap,
        )
        self.setFixedSize(
            self.pixmap.width(),
            self.pixmap.height(),
        )
        self.show()
        shared.APP.processEvents()

    def status_update(self, a_text):
        self.showMessage(
            a_text,
            QtCore.Qt.AlignmentFlag.AlignBottom,
            QtCore.Qt.GlobalColor.white,
        )
        shared.APP.processEvents()
