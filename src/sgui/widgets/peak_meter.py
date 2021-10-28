from sgui.sgqt import *
from sglib.math import clip_min, lin_to_db
from sglib.lib import util
from sglib.lib.translate import _
from sglib.models import theme


PEAK_GRADIENT_CACHE = {}

def peak_meter_gradient(a_height):
    if a_height not in PEAK_GRADIENT_CACHE:
        f_gradient = QLinearGradient(0.0, 0.0, 0.0, a_height)
        for stop in theme.SYSTEM_COLORS.widgets.peak_meter.stops:
            f_gradient.setColorAt(stop.pos, QColor(stop.color))
        PEAK_GRADIENT_CACHE[a_height] = f_gradient
    return PEAK_GRADIENT_CACHE[a_height]

class peak_meter:
    def __init__(
        self,
        a_width=14,
        a_text=False,
        invert=False,
        brush=None,
    ):
        self.text = a_text
        self.widget = QWidget()
        self.widget.setFixedWidth(a_width)
        self.values = None
        self.set_value([0.0, 0.0])
        self.widget.paintEvent = self.paint_event
        self.high = 0.0
        self.set_tooltip()
        self.widget.mousePressEvent = self.reset_high
        self.white_pen = QPen(QtCore.Qt.GlobalColor.white, 1.0)
        self.invert = invert
        self.brush = brush

    def set_value(self, a_vals):
        f_vals = [float(x) for x in a_vals]
        if f_vals != self.values:
            self.values = f_vals
            self.widget.update()

    def reset_high(self, a_val=None):
        self.high = 0.0
        self.set_tooltip()

    def set_tooltip(self):
        if self.high == 0:
            f_val = -100.0
        else:
            f_val = round(lin_to_db(self.high), 1)
        self.widget.setToolTip(
            _("Peak {}dB\nClick with mouse to reset").format(f_val))

    def paint_event(self, a_ev):
        p = QPainter(self.widget)
        p.fillRect(self.widget.rect(), QtCore.Qt.GlobalColor.black)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        f_height = self.widget.height()
        brush = self.brush if self.brush else peak_meter_gradient(f_height)
        p.setBrush(brush)
        f_rect_width = self.widget.width() * 0.5

        for f_val, f_i in zip(self.values, range(2)):
            if self.invert:
                f_val = 1.0 - f_val
            if f_val == 0.0:
                continue
            elif f_val >= 1.0:
                f_rect_y = 0.0
                f_rect_height = f_height
            else:
                f_db = lin_to_db(f_val)
                f_db = clip_min(f_db, -29.0)
                f_rect_y = f_height * f_db * -0.033333333 # / -30.0
                f_rect_height = f_height - f_rect_y
            if f_val > self.high:
                self.high = f_val
                self.set_tooltip()
            f_rect_x = f_i * f_rect_width
            f_rect = QtCore.QRectF(
                float(f_rect_x),
                float(f_rect_y),
                float(f_rect_width),
                float(f_rect_height),
            )
            p.drawRect(f_rect)

        if self.text:
            p.setPen(self.white_pen)
            for f_y, f_db in zip(
            range(0, int(f_height), int(f_height * 0.2)), # / 5.0
            range(0, -30, -6)):
                p.drawText(3, f_y, str(-f_db))

