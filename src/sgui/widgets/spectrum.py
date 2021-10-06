from . import _shared
from sglib.math import clip_value, lin_to_db, pitch_to_hz
from sglib.lib import util
from sgui.sgqt import *


class spectrum(QGraphicsPathItem):
    def __init__(self, a_height, a_width):
        self.spectrum_height = float(a_height)
        self.spectrum_width = float(a_width)
        QGraphicsPathItem.__init__(self)
        self.setPen(QtCore.Qt.GlobalColor.white)

    def set_spectrum(self, a_message):
        self.painter_path = QPainterPath(QtCore.QPointF(0.0, 20.0))
        self.values = a_message.split("|")
        self.painter_path.moveTo(0.0, self.spectrum_height)
        f_low = _shared.EQ_LOW_PITCH
        f_high = _shared.EQ_HIGH_PITCH
        f_width_per_point = (self.spectrum_width / float(f_high - f_low))
        f_fft_low = float(util.SAMPLE_RATE) * 0.00024414 # / 4096.0
        f_nyquist = float(util.NYQUIST_FREQ)
        nyquist_recip = 1. / f_nyquist
        f_i = f_low
        while f_i < f_high:
            f_hz = pitch_to_hz(f_i) - f_fft_low
            f_pos = int((f_hz * nyquist_recip) * len(self.values))
            f_val = float(self.values[f_pos])
            f_db = lin_to_db(f_val) - 64.0
            f_db += ((f_i - f_low) * 0.08333333) * 3.0 # / 12.
            f_db = clip_value(f_db, -70.0, 0.0)
            f_val = 1.0 - ((f_db + 70.0) * 0.0142857142) # / 70.
            f_x = f_width_per_point * (f_i - f_low)
            f_y = f_val * self.spectrum_height
            self.painter_path.lineTo(f_x, f_y)
            f_i += 0.5
        self.setPath(self.painter_path)

