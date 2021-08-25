from sgui.sgqt import *
from sglib.models import theme

from sglib.log import LOG
from sglib.math import clip_value
from sgui import shared as glbl_shared
from sglib.lib import util
from sglib.lib.translate import _
from sgui.util import svg_to_pixmap
from enum import Enum
import os


# This is for plugins to consume, it's not a default value anywhere
DEFAULT_KNOB_SIZE = 48

class PixmapKnobCache:
    def __init__(self, a_path):
        self.cache = {}
        self.path = a_path

    def get_scaled_pixmap_knob(self, a_size):
        if a_size not in self.cache:
            self.cache[a_size] = svg_to_pixmap(
                self.path,
                a_size,
                a_size,
            )
        return self.cache[a_size]

def knob_setup():
    global \
        DEFAULT_KNOB_FG_PIXMAP_CACHE, \
        DEFAULT_KNOB_BG_PIXMAP_CACHE
    DEFAULT_KNOB_FG_PIXMAP_CACHE = PixmapKnobCache(
        os.path.join(
            theme.ASSETS_DIR,
            theme.SYSTEM_COLORS.widgets.knob_fg_image,
        ),
    )
    DEFAULT_KNOB_BG_PIXMAP_CACHE = PixmapKnobCache(
        os.path.join(
            theme.ASSETS_DIR,
            theme.SYSTEM_COLORS.widgets.knob_bg_image,
        ),
    )

class ArcType(Enum):
    UP = 0
    BIDIRECTIONAL = 1

class pixmap_knob(QDial):
    def __init__(
        self,
        a_size,
        a_min_val,
        a_max_val,
        a_pixmap_fg_cache=None,
        a_pixmap_bg_cache=None,
        arc_width_pct=12.0,  # 0.0 to disable
        arc_type=ArcType.UP,
        arc_pen_kwargs={},
    ):
        self.size = a_size
        self.arc_width_pct = arc_width_pct
        self.arc_type = arc_type
        self.arc_pen_kwargs = arc_pen_kwargs
        QDial.__init__(self)
        self.pixmap_fg_cache = \
            a_pixmap_fg_cache if a_pixmap_fg_cache \
            else  DEFAULT_KNOB_FG_PIXMAP_CACHE
        self.pixmap_bg_cache = \
            a_pixmap_bg_cache if a_pixmap_bg_cache \
            else DEFAULT_KNOB_BG_PIXMAP_CACHE
        self.setRange(a_min_val, a_max_val)
        self.val_step = float(a_max_val - a_min_val) * 0.005  # / 200.0
        self.val_step_small = self.val_step * 0.1
        self.setGeometry(0, 0, a_size, a_size)
        self.pixmap_size = a_size - 12
        self.pixmap_fg = self.pixmap_fg_cache.get_scaled_pixmap_knob(
            self.pixmap_size)
        self.pixmap_bg = self.pixmap_bg_cache.get_scaled_pixmap_knob(
            self.pixmap_size)
        self.setFixedSize(a_size, a_size)
        self._button = QtCore.Qt.MouseButton.NoButton

    def keyPressEvent(self, a_event):
        QDial.keyPressEvent(self, a_event)
        if a_event.key() == QtCore.Qt.Key.Key_Space:
            glbl_shared.TRANSPORT.on_spacebar()

    def paintEvent(self, a_event):
        p = QPainter(self)
        p.setRenderHints(
            QPainter.RenderHint.Antialiasing
            |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        f_frac_val = (
            (float(self.value() - self.minimum()))
            /
            (float(self.maximum() - self.minimum()))
        )
        f_rotate_value = f_frac_val * 270.0
        f_rect = self.rect()
        arc_width = self.arc_width_pct * f_rect.width() * 0.01
        f_rect.setWidth(f_rect.width() - arc_width)
        f_rect.setHeight(f_rect.height() - arc_width)
        f_rect.setX(f_rect.x() + arc_width)
        f_rect.setY(f_rect.y() + arc_width)

        if self.arc_width_pct:
            knob_arc_pen = QPen(
                QColor(
                    theme.SYSTEM_COLORS.widgets.knob_arc_pen,
                ),
                arc_width,
                **self.arc_pen_kwargs
            )
            knob_arc_background_pen = QPen(
                QColor(
                    theme.SYSTEM_COLORS.widgets.knob_arc_background_pen,
                ),
                arc_width,
            )
            p.setPen(knob_arc_background_pen)
            p.drawArc(f_rect, -135 * 16, 135 * 2 * -16)
            p.setPen(knob_arc_pen)
            if self.arc_type == ArcType.UP:
                p.drawArc(
                    f_rect,
                    -135 * 16,
                    (f_rotate_value + 1.0) * -16,
                )
            elif self.arc_type == ArcType.BIDIRECTIONAL:
                if f_rotate_value < 135.:
                    span_angle = (135. - f_rotate_value) * 16
                else:
                    span_angle = (f_rotate_value - 135.) * -16
                p.drawArc(
                    f_rect,
                    90 * 16,
                    span_angle,
                )
            else:
                raise ValueError(f"Invalid arc_type: {self.arc_type}")

        if self.pixmap_bg:
            p.drawPixmap(6, 6, self.pixmap_bg)

        if self.pixmap_fg:
            # xc and yc are the center of the widget's rect.
            xc = self.width() * 0.5
            yc = self.height() * 0.5
            # translates the coordinate system by xc and yc
            p.translate(xc, yc)
            p.rotate(f_rotate_value)
            # we need to move the rectangle that we draw by
            # rx and ry so it's in the center.
            rx = -(self.pixmap_size * 0.5)
            ry = -(self.pixmap_size * 0.5)
            p.drawPixmap(rx, ry, self.pixmap_fg)

    def mousePressEvent(self, a_event):
        self._button = a_event.button()
        self.mouse_pos = QCursor.pos()
        if self._button == QtCore.Qt.MouseButton.RightButton:
            QDial.mousePressEvent(self, a_event)
            return
        f_pos = qt_event_pos(a_event)
        self.orig_x = f_pos.x()
        self.orig_y = f_pos.y()
        self.orig_value = self.value()
        self.fine_only = (
            a_event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        )
        QApplication.setOverrideCursor(QtCore.Qt.CursorShape.BlankCursor)

    def mouseMoveEvent(self, a_event):
        if self._button != QtCore.Qt.MouseButton.LeftButton:
            QDial.mouseMoveEvent(self, a_event)
            return
        f_pos = qt_event_pos(a_event)
        f_x = f_pos.x()
        f_diff_x = f_x - self.orig_x
        if self.fine_only:
            f_val = (f_diff_x * self.val_step_small) + self.orig_value
        else:
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = ((f_diff_y * self.val_step) +
                (f_diff_x * self.val_step_small)) + self.orig_value
        f_val = clip_value(
            f_val, self.minimum(), self.maximum())
        f_val = int(f_val)
        if f_val != self.value():
            self.setValue(f_val)
            self.valueChanged.emit(f_val)

    def mouseReleaseEvent(self, a_event):
        # Does not work on Wayland
        #QCursor.setPos(self.mouse_pos)
        self._button = QtCore.Qt.MouseButton.NoButton
        QApplication.restoreOverrideCursor()
        self.sliderReleased.emit()

