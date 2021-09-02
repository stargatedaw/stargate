import os
from xml.etree import ElementTree as xmltree

from sgui.sgqt import *
from sglib.lib.translate import _
from sglib.lib.util import (
    clear_file_setting,
    get_file_setting,
    set_file_setting,
)
from sglib.hardware.rpi import is_rpi
from sglib.log import LOG
from sglib.models import theme
from sgui import shared as glbl_shared
import multiprocessing
import sys


FONT = None
def get_font():
    assert FONT, FONT
    return FONT

def set_font():
    global FONT
    FONT = FontManager.factory()

def show_generic_exception(
    ex,
    extra="",
):
    LOG.exception(ex)
    QMessageBox.warning(
        glbl_shared.MAIN_WINDOW.widget,
        _("Error"),
        _(f"The following error happened:\n{ex}\n\n{extra}"),
    )

def check_for_rw_perms(a_file):
    if not os.access(
        os.path.dirname(str(a_file)),
        os.W_OK,
    ):
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW.widget,
            "Error",
            f"You do not have read+write permissions to {a_file}",
        )
        return False
    else:
        return True

def check_for_empty_directory(a_dir):
    """ Return true if directory is empty, show error message and
        return False if not
    """
    if os.listdir(a_dir):
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW.widget,
            "Error",
            "You must save the project file to an empty directory, use "
            "the 'Create Folder' button to create a new, empty directory.",
        )
        return False
    else:
        return True

def svg_to_pixmap(path: str, width=None, height=None):
    """ Convert an SVG file to a scaled QPixmap without pixelation
        If width or height is omitted, the image will be scaled maintaining
        aspect ratio
        If width and height are omitted, it will be rendered to the original
        size

        @path:   The path to an SVG file
        @width:  The desired width of the pixmap, or None
        @height: The desired height of the pixmap, or None
    """
    if not (width and height):
        tree = xmltree.parse(path)
        root = tree.getroot()
        svg_width = float(root.attrib['width'])
        svg_height = float(root.attrib['height'])
        if not width and not height:  # no scaling
            width = svg_width
            height = svg_height
        elif not width:  # scale to height, preserve aspect ratio
            width = int(svg_width * (height / svg_height))
        elif not height:  # scale to width, preserve aspect ratio
            height = int(svg_height * (width / svg_width))
    svg_renderer = QSvgRenderer(path)
    pixmap = QPixmap(width, height)
    painter = QPainter()
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter.begin(pixmap)
    svg_renderer.render(painter)
    painter.end()
    return pixmap

def ui_scaler_factory():
    screen = QGuiApplication.primaryScreen()
    phys_rect = screen.physicalSize()
    res_rect = screen.geometry()

    return theme.UIScaler(
        phys_rect.width(),
        phys_rect.height(),
        res_rect.width(),
        res_rect.height(),
    )

class FontManager:
    def __init__(self, font):
        self.font = font

    def get_font_size(self):
        px_size = self.font.pixelSize()
        pt_size = self.font.pointSize()
        if px_size != -1 and pt_size == -1:
            return px_size, 'px'
        elif px_size == -1 and pt_size != -1:
            return pt_size, 'pt'
        else:
            raise ValueError(f"{px_size}, {pt_size}")

    def clear_font(self):
        clear_file_setting('font')
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW.widget,
            "Info",
            _("Restart Stargate to update the UI"),
        )

    def choose_font(self):
        font, ok = QFontDialog.getFont(
            self.font,
            glbl_shared.MAIN_WINDOW.widget,
        )
        if ok:
            set_file_setting(
                'font',
                font.toString(),
            )
            QMessageBox.warning(
                glbl_shared.MAIN_WINDOW.widget,
                "Info",
                _("Restart Stargate to update the UI"),
            )

    def QGraphicsSimpleTextItem(self, *args, **kwargs):
        item = QtWidgets.QGraphicsSimpleTextItem(*args, **kwargs)
        item.setFont(self.font)
        return item

    @staticmethod
    def factory():
        font_str = get_file_setting('font', str, None)
        if font_str:
            try:
                font = QFont()
                assert font.fromString(font_str), font_str
            except Exception as ex:
                LOG.exception(ex)
                font = QApplication.font()
        else:
            font = QApplication.font()
        return FontManager(font)

def setup_theme(app):
    set_font()
    scaler = ui_scaler_factory()
    font = get_font()
    glbl_shared.APP = app
    app.setFont(font.font)
    font_size, font_unit = font.get_font_size()
    try:
        theme.load_theme(scaler, font_size, font_unit)
        glbl_shared.APP.setStyle(QStyleFactory.create("Fusion"))
        glbl_shared.APP.setStyleSheet(theme.QSS)
        return scaler
    except Exception as ex:
        LOG.exception(ex)
        f_answer = QMessageBox.warning(
            None,
            _("Warning"),
            _(
                "Encountered the following error loading the theme: \n\n"
                f"{ex}\n\n"
                "Click 'OK' to clear the current theme and quit, 'Cancel' to "
                "quit without clearing the current theme.\n\n"
                "You can check ~/stargate/{log,rendered_theme} for details"
            ),
            buttons=(
                QMessageBox.StandardButton.Ok
                |
                QMessageBox.StandardButton.Cancel
            ),
        )
        if f_answer == QMessageBox.StandardButton.Ok:
            clear_file_setting("default-style")
        sys.exit(1)

def get_fps() -> int:
    """ Get the frames-per-second that the engine should send messages to
        the UI
    """
    if is_rpi():
        return 10
    screen = QGuiApplication.primaryScreen()
    cpu_count = multiprocessing.cpu_count()
    if cpu_count >= 8:
        return int(screen.refreshRate())
    elif cpu_count >= 6:
        return 30
    elif cpu_count >= 4:
        return 25
    else:
        return 20

