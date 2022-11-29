import os
from xml.etree import ElementTree as xmltree

from sgui.sgqt import *
from sglib.lib.translate import _
from sglib.lib.util import (
    clear_file_setting,
    FONTS_DIR,
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
        glbl_shared.MAIN_WINDOW,
        _("Error"),
        _(f"The following error happened:\n{ex}\n\n{extra}"),
    )

def check_for_rw_perms(a_file):
    if not os.access(
        os.path.dirname(str(a_file)),
        os.W_OK,
    ):
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW,
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
            glbl_shared.MAIN_WINDOW,
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
            width = round(svg_width)
            height = round(svg_height)
        elif not width:  # scale to height, preserve aspect ratio
            width = int(svg_width * (height / svg_height))
        elif not height:  # scale to width, preserve aspect ratio
            height = int(svg_height * (width / svg_width))
    svg_renderer = QSvgRenderer(path)
    pixmap = QPixmap(int(width), int(height))
    painter = QPainter()
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter.begin(pixmap)
    painter.setRenderHints(
        (
            QPainter.RenderHint.Antialiasing
            |
            QPainter.RenderHint.SmoothPixmapTransform
        ),
        True
    )
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

def log_screen_info():
    try:
        screens = QGuiApplication.screens()
        for screen, i in zip(screens, range(len(screens))):
            LOG.info(
                f"Screen {i} screen.logicalDotsPerInch: "
                f"{screen.logicalDotsPerInch()}"
            )
            LOG.info(
                f"Screen {i} screen.physicalDotsPerInch: "
                f"{screen.physicalDotsPerInch()}"
            )
            LOG.info(
                f"Screen {i} screen.devicePixelRatio: "
                f"{screen.devicePixelRatio()}"
            )
            LOG.info(
                f"Screen {i} screen.physicalSize: {screen.physicalSize()}"
            )
            LOG.info(
                f"Screen {i} screen.manufacturer: {screen.manufacturer()}"
            )
            LOG.info(f"Screen {i} screen.model: {screen.model()}")
            LOG.info(f"Screen {i} screen.refreshRate: {screen.refreshRate()}")
    except Exception as ex:
        LOG.exception(ex)

class FontManager:
    def __init__(self, font):
        self.font = font

    def get_font_size(self):
        return self._font_size(self.font)

    @staticmethod
    def _font_size(font):
        px_size = font.pixelSize()
        pt_size = font.pointSize()
        if px_size != -1 and pt_size == -1:
            return px_size, 'px'
        elif px_size == -1 and pt_size != -1:
            return pt_size, 'pt'
        else:
            raise ValueError(f"{px_size}, {pt_size}")

    def clear_font(self):
        clear_file_setting('font')
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW,
            "Info",
            _("Restart Stargate to update the UI"),
        )

    def choose_font(self):
        font, ok = QFontDialog.getFont(
            self.font,
            glbl_shared.MAIN_WINDOW,
        )
        if ok:
            set_file_setting(
                'font',
                font.toString(),
            )
            QMessageBox.warning(
                glbl_shared.MAIN_WINDOW,
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
                font = FontManager._default_font()
        else:
            font = FontManager._default_font()
        return FontManager(font)

    @staticmethod
    def _default_font():
        default_font = QApplication.font()
        size, unit = FontManager._font_size(default_font)
        font_file = os.path.join(
            FONTS_DIR,
            'RobotoCondensed-Regular.ttf',
        )
        _id = QFontDatabase.addApplicationFont(font_file)
        family = QFontDatabase.applicationFontFamilies(_id)[0]
        font = QFont(family)
        if unit == 'px':
            font.setPixelSize(int(size))
        elif unit == 'pt':
            font.setPointSizeF(float(size))
        else:
            raise ValueError(unit)

        return font

def pt_to_px(pt):
    dpi = QGuiApplication.primaryScreen().physicalDotsPerInch()
    return round(
        (pt / 72.) * dpi
    )

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
        if theme.ICON_PATH:
            LOG.info(f"Setting icon to '{theme.ICON_PATH}'")
            glbl_shared.APP.setWindowIcon(
                QIcon(theme.ICON_PATH),
            )
    except Exception as ex:
        LOG.exception(ex)
        f_answer = orig_QMessageBox.question(
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
        return 20
    screen = QGuiApplication.primaryScreen()
    is_gt_hd = screen.physicalSize().width() > 2000
    cpu_count = multiprocessing.cpu_count()
    if cpu_count >= 8:
        if is_gt_hd:
            return 36
        if screen.refreshRate() > 60:
            return 60
        return int(screen.refreshRate())
    elif cpu_count >= 6:
        return 30
    elif cpu_count >= 4:
        return 25
    else:
        return 20

def Separator(
    orientation='v',
    parent=None,
):
    """ Return a separator line suitable for adding to a QLayout
        Style using stylesheets with #separator_h/v
    """
    assert orientation in ('h', 'v'), orientation
    line = QFrame(parent)
    line.setFrameShape(
        QFrame.Shape.HLine if orientation == 'h' else QFrame.Shape.VLine
    )
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setObjectName(f'separator_{orientation}')
    #line.setLineWidth(1)
    return line

