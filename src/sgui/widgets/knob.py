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


DEFAULT_THEME_KNOB = None
DEFAULT_THEME_KNOB_BG = None
# This is for plugins to consume, it's not a default value anywhere
DEFAULT_KNOB_SIZE = 48
DEFAULT_LARGE_KNOB_SIZE = 64

class PixmapKnobCache:
    def __init__(self):
        self.cache = {}

    def get_scaled_pixmap_knob(self, path, size):
        if not path:
            return None
        if path == 'default':
            path = DEFAULT_THEME_KNOB
        if path == 'default_bg':
            path = DEFAULT_THEME_KNOB_BG
        path = util.pi_path(path)
        key = (path, size)
        if key in self.cache:
            return self.cache[key]
        else:
            pixmap = svg_to_pixmap(
                path,
                size,
                size,
            )
            self.cache[key] = pixmap
            return pixmap

def knob_setup():
    global DEFAULT_THEME_KNOB, DEFAULT_THEME_KNOB_BG, KNOB_PIXMAP_CACHE
    DEFAULT_THEME_KNOB = os.path.join(
        theme.ASSETS_DIR,
        theme.SYSTEM_COLORS.widgets.knob_fg_image,
    )
    DEFAULT_THEME_KNOB_BG = os.path.join(
        theme.ASSETS_DIR,
        theme.SYSTEM_COLORS.widgets.knob_bg_image,
    )
    KNOB_PIXMAP_CACHE = PixmapKnobCache()

class ArcType(Enum):
    # Arc goes from minimal at -135 degrees to full at +135 degrees from top
    UP = 0
    # Arc is minimal at 0 degrees (top), half-full at -/+135 degrees from top
    BIDIRECTIONAL = 1

class PixmapKnob(QDial):
    def __init__(
        self,
        a_size,
        a_min_val,
        a_max_val,
        fg_svg="default",
        bg_svg=None,
        arc_width_pct=12.0,  # 0.0 to disable
        arc_type=ArcType.UP,
        arc_brush=None,
        arc_bg_brush=None,
        arc_pen_kwargs={},
        draw_line=False,
        arc_space=0.0,
    ):
        """
        @a_size:    The size of the knobs bounding square
        @a_min_val: THe minimum value of the knob
        @a_max_val: THe maximum value of the knob
        @fg_svg:
            The full path to an SVG image to draw as the foreground image, will
            be rotated with the knob value from -135 to +135 degrees from top
            center.  It is expected that the knob initially points to -135
            degrees from the top.
        @bg_svg: A static image drawn behind @fg_svg, will not be rotated
        @arc_width_pct:
            The 0-100 percentage of @a_size that the arc drawn around the knob
            should be.  0.0 to not draw an arc
        @arc_type:  See ArcType for details
        @arc_brush:
            The brush to use for the arc pen.  Use a QColor or QGradient
        @arc_bg_brush:
            The brush to use for the arc background pen.  This is the static
            arc drawn behind the main arc, always from -135 to +135 degrees
            from the top
        @arc_pen_kwargs:
            Additional keyword arguments to pass to the QPen for the
            foreground arc.
        @draw_line:
            True to draw a line from the center of the knob to the end of
            the arc.
        """
        self.arc_brush = arc_brush if arc_brush else QColor(
            theme.SYSTEM_COLORS.widgets.knob_arc_pen,
        )
        self.arc_bg_brush = arc_bg_brush if arc_bg_brush else QColor(
            theme.SYSTEM_COLORS.widgets.knob_arc_background_pen,
        )
        self.arc_width_pct = arc_width_pct
        self.arc_type = arc_type
        self.arc_space = arc_space
        self.arc_pen_kwargs = arc_pen_kwargs
        QDial.__init__(self)
        self.bg_svg = bg_svg
        self.fg_svg = fg_svg
        self.draw_line = draw_line
        self._size = a_size
        self.setRange(int(a_min_val), int(a_max_val))
        self.val_step = float(a_max_val - a_min_val) * 0.005  # / 200.0
        self.val_step_small = self.val_step * 0.1
        self.setGeometry(0, 0, a_size, a_size)
        self.pixmap_size = (
            a_size - (arc_width_pct * a_size * 0.02) - (arc_space * 2)
        )
        self.pixmap_fg = KNOB_PIXMAP_CACHE.get_scaled_pixmap_knob(
            self.fg_svg,
            self.pixmap_size,
        )
        self.pixmap_bg = KNOB_PIXMAP_CACHE.get_scaled_pixmap_knob(
            self.bg_svg,
            self.pixmap_size,
        )
        self.setFixedSize(a_size, a_size)
        self._button = QtCore.Qt.MouseButton.NoButton

    def wheelEvent(self, event):
        event.ignore()

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
        arc_width = int(self.arc_width_pct * f_rect.width() * 0.01)
        f_rect.setWidth(int(f_rect.width() - arc_width))
        f_rect.setHeight(int(f_rect.height() - arc_width))
        f_rect.setX(int(f_rect.x() + arc_width))
        f_rect.setY(int(f_rect.y() + arc_width))

        if self.arc_width_pct:
            knob_arc_pen = QPen(
                self.arc_brush,
                arc_width,
                **self.arc_pen_kwargs
            )
            knob_arc_background_pen = QPen(
                self.arc_bg_brush,
                arc_width,
            )
            p.setPen(knob_arc_background_pen)
            p.drawArc(f_rect, -135 * 16, 135 * 2 * -16)
            p.setPen(knob_arc_pen)
            if self.arc_type == ArcType.UP:
                p.drawArc(
                    f_rect,
                    -135 * 16,
                    int((f_rotate_value + 1.0) * -16),
                )
            elif self.arc_type == ArcType.BIDIRECTIONAL:
                if f_rotate_value < 135.:
                    span_angle = (135. - f_rotate_value) * 16
                else:
                    span_angle = (f_rotate_value - 135.) * -16
                p.drawArc(
                    f_rect,
                    90 * 16,
                    int(span_angle),
                )
            else:
                raise ValueError(f"Invalid arc_type: {self.arc_type}")

        if self.draw_line:
            rectf_width = float(self._size - (arc_width * 2.))
            rectf = QtCore.QRectF(
                arc_width,
                arc_width,
                rectf_width,
                rectf_width,
            )
            ppath = QPainterPath()
            ppath.arcMoveTo(rectf, -float(f_rotate_value) - 135.)
            center = self._size * 0.5
            ppath.lineTo(center, center)
            cap_style = knob_arc_pen.capStyle()
            knob_arc_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            p.setPen(knob_arc_pen)
            p.drawPath(ppath)
            knob_arc_pen.setCapStyle(cap_style)
            p.setPen(knob_arc_pen)

        if self.pixmap_bg:
            p.drawPixmap(
                int(arc_width + self.arc_space),
                int(arc_width + self.arc_space),
                self.pixmap_bg,
            )

        if self.pixmap_fg:
            # xc and yc are the center of the widget's rect.
            xc = self.width() * 0.5
            yc = self.height() * 0.5
            # translates the coordinate system by xc and yc
            p.translate(xc, yc)
            p.rotate(
                int(
                    round(f_rotate_value),
                ),
            )
            # we need to move the rectangle that we draw by
            # rx and ry so it's in the center.
            rx = -(self.pixmap_size * 0.5)
            ry = -(self.pixmap_size * 0.5)
            p.drawPixmap(int(rx), int(ry), self.pixmap_fg)

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

