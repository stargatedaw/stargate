from sglib.models import theme
from sgui import shared
from sgui.util import svg_to_pixmap, ui_scaler_factory
from sgui.sgqt import (
    QLabel,
    QWidget,
    QtCore,
    QGridLayout,
    QSizePolicy,
    QSpacerItem,
)
import os

SPLASHSCREEN = None

class SplashScreen(QWidget):
    def __init__(self, parent):
        global SPLASHSCREEN
        super().__init__(parent)
        self.setObjectName('splash_widget')
        scaler = ui_scaler_factory()
        scaled_height = int(scaler.y_res * 0.8)
        self.pixmap = svg_to_pixmap(
            os.path.join(
                theme.ASSETS_DIR,
                theme.SYSTEM_COLORS.widgets.splash_screen,
            ),
            height=scaled_height,
        )
        self.layout = QGridLayout(self)
        self.pixmap_label =  QLabel(self)
        self.text_label =  QLabel('Initializing...', self)
        self.text_label.setObjectName('transparent')
        self.layout.addWidget(self.pixmap_label, 1, 1)
        self.layout.addWidget(self.text_label, 2, 1)
        self.pixmap_label.setFixedSize(
            self.pixmap.width(),
            self.pixmap.height(),
        )
        self.pixmap_label.setPixmap(self.pixmap)
        self.pixmap_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignBottom,
        )
        self.layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            0,
            1,
        )
        self.layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            1,
            2,
        )
        self.layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            3,
            1,
        )
        self.layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            1,
            0,
        )
        shared.APP.processEvents()
        SPLASHSCREEN = self

    def status_update(self, a_text):
        self.text_label.setText(a_text)
        shared.APP.processEvents()

