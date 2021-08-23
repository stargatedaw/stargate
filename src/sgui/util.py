import os
from xml.etree import ElementTree as xmltree

from sgui.sgqt import *
from sglib.lib.translate import _
from sglib.log import LOG
from sglib.models import theme
from sgui import shared as glbl_shared

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

