from sgui.sgqt import *
from sglib.models import theme


KC_INTEGER = 0
KC_DECIMAL = 1
KC_PITCH = 2
KC_NONE = 3
KC_127_PITCH = 4
KC_127_ZERO_TO_X = 5
KC_LOG_TIME = 6
KC_127_ZERO_TO_X_INT = 7
KC_TIME_DECIMAL = 8
KC_HZ_DECIMAL = 9
KC_INT_PITCH = 10
KC_TENTH = 11
KC_MILLISECOND = 12
KC_127_PITCH_MIN_MAX = 13
KC_TEXT = 14

TEMPO = 128.0

ADSR_CLIPBOARD = {}

def set_global_tempo(a_tempo):
    global TEMPO
    TEMPO = a_tempo

EQ_POINT_DIAMETER = 12.0
EQ_POINT_RADIUS = EQ_POINT_DIAMETER * 0.5
EQ_WIDTH = 600
EQ_HEIGHT = 300
EQ_OCTAVE_PX = (EQ_WIDTH / (100.0 / 12.0))

EQ_LOW_PITCH = 4
EQ_HIGH_PITCH = 123

EQ_POINT_BRUSH = QColor("#ffffff")

EQ_FILL = QLinearGradient(0.0, 0.0, 0.0, EQ_HEIGHT)

EQ_FILL.setColorAt(0.0, QColor(255, 0, 0, 90)) #red
EQ_FILL.setColorAt(0.14285, QColor(255, 123, 0, 90)) #orange
EQ_FILL.setColorAt(0.2857, QColor(255, 255, 0, 90)) #yellow
EQ_FILL.setColorAt(0.42855, QColor(0, 255, 0, 90)) #green
EQ_FILL.setColorAt(0.5714, QColor(0, 123, 255, 90)) #blue
EQ_FILL.setColorAt(0.71425, QColor(0, 0, 255, 90)) #indigo
EQ_FILL.setColorAt(0.8571, QColor(255, 0, 255, 90)) #violet

EQ_BACKGROUND = QColor("#0f0f0f")

