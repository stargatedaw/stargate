from sglib.math import clip_min, lin_to_db
from sglib.lib import util
from sglib.lib.translate import _
from sgui.sgqt import *


PEAK_GRADIENT_CACHE = {}

def peak_meter_gradient(a_height):
    if a_height not in PEAK_GRADIENT_CACHE:
        f_gradient = QLinearGradient(0.0, 0.0, 0.0, a_height)
        f_gradient.setColorAt(0.0, QColor.fromRgb(255, 0, 0))
        f_gradient.setColorAt(0.0333, QColor.fromRgb(255, 0, 0))
        f_gradient.setColorAt(0.05, QColor.fromRgb(150, 255, 0))
        f_gradient.setColorAt(0.2, QColor.fromRgb(90, 255, 0))
        f_gradient.setColorAt(0.4, QColor.fromRgb(0, 255, 0))
        f_gradient.setColorAt(0.7, QColor.fromRgb(0, 255, 0))
        f_gradient.setColorAt(1.0, QColor.fromRgb(0, 210, 180))
        PEAK_GRADIENT_CACHE[a_height] = f_gradient
    return PEAK_GRADIENT_CACHE[a_height]

class peak_meter:
    def __init__(self, a_width=14, a_text=False):
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
        p.setBrush(peak_meter_gradient(f_height))
        f_rect_width = self.widget.width() * 0.5

        for f_val, f_i in zip(self.values, range(2)):
            if f_val == 0.0:
                continue
            elif f_val > 1.0:
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
                f_rect_x, f_rect_y, f_rect_width, f_rect_height)
            p.drawRect(f_rect)

        if self.text:
            p.setPen(self.white_pen)
            for f_y, f_db in zip(
            range(0, int(f_height), int(f_height * 0.2)), # / 5.0
            range(0, -30, -6)):
                p.drawText(3, f_y, str(-f_db))

