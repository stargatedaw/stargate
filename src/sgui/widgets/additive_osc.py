from sglib.math import clip_value, db_to_lin, lin_to_db
from sglib.lib import util
from sglib.lib.translate import _
from sglib.log import LOG
from sgui.sgqt import *
import numpy


class abstract_custom_oscillator:
    def __init__(self):
        self.widget = QWidget()
        self.widget.setObjectName("plugin_ui")
        self.layout = QVBoxLayout(self.widget)

    def open_settings(self, a_settings):
        pass


ADDITIVE_OSC_HEIGHT = 310
ADDITIVE_OSC_MIN_AMP = -50
ADDITIVE_OSC_INC = 6 #int(ADDITIVE_OSC_HEIGHT / -ADDITIVE_OSC_MIN_AMP)
ADDITIVE_MAX_Y_POS = ADDITIVE_OSC_HEIGHT - ADDITIVE_OSC_INC
ADDITIVE_OSC_HARMONIC_COUNT = 32
ADDITIVE_OSC_BAR_WIDTH = 10
ADDITIVE_OSC_WIDTH = ADDITIVE_OSC_HARMONIC_COUNT * ADDITIVE_OSC_BAR_WIDTH
ADDITIVE_WAVETABLE_SIZE = 1024
#ADDITIVE_OSC_HEIGHT_div2 = ADDITIVE_OSC_HEIGHT * 0.5

ADD_OSC_FILL = QLinearGradient(0.0, 0.0, 0.0, ADDITIVE_OSC_HEIGHT)

ADD_OSC_FILL.setColorAt(0.0, QColor(255, 0, 0, 90)) #red
ADD_OSC_FILL.setColorAt(0.14285, QColor(255, 123, 0, 90)) #orange
ADD_OSC_FILL.setColorAt(0.2857, QColor(255, 255, 0, 90)) #yellow
ADD_OSC_FILL.setColorAt(0.42855, QColor(0, 255, 0, 90)) #green
ADD_OSC_FILL.setColorAt(0.5714, QColor(0, 123, 255, 90)) #blue
ADD_OSC_FILL.setColorAt(0.71425, QColor(0, 0, 255, 90)) #indigo
ADD_OSC_FILL.setColorAt(0.8571, QColor(255, 0, 255, 90)) #violet

ADD_OSC_BACKGROUND = QLinearGradient(0.0, 0.0, 10.0, ADDITIVE_OSC_HEIGHT)
ADD_OSC_BACKGROUND.setColorAt(0.0, QColor("#333333"))
ADD_OSC_BACKGROUND.setColorAt(0.2, QColor("#2c2c2c"))
ADD_OSC_BACKGROUND.setColorAt(0.7, QColor("#303030"))
ADD_OSC_BACKGROUND.setColorAt(1.0, QColor("#333333"))

ADD_OSC_SINE_CACHE = {}

def global_get_sine(a_size, a_phase):
    f_key = (a_size, a_phase)
    if f_key in ADD_OSC_SINE_CACHE:
        return numpy.copy(ADD_OSC_SINE_CACHE[f_key])
    else:
        f_phase = a_phase * numpy.pi * 2.0
        f_lin = numpy.linspace(f_phase, (2.0 * numpy.pi) + f_phase, a_size)
        f_sin = numpy.sin(f_lin)
        ADD_OSC_SINE_CACHE[f_key] = f_sin
        return numpy.copy(f_sin)


class additive_osc_amp_bar(QGraphicsRectItem):
    def __init__(self, a_x_pos):
        QGraphicsRectItem.__init__(self)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges,
        )
        self.setBrush(ADD_OSC_FILL)
        self.setPen(QPen(QtCore.Qt.GlobalColor.white))
        self.x_pos = a_x_pos
        self.setPos(a_x_pos, ADDITIVE_OSC_HEIGHT - ADDITIVE_OSC_INC)
        self.setRect(
            0.0,
            0.0,
            float(ADDITIVE_OSC_BAR_WIDTH),
            float(ADDITIVE_OSC_INC),
        )
        self.value = ADDITIVE_OSC_MIN_AMP
        self.extend_to_bottom()

    def set_value(self, a_value):
        if self.value != a_value:
            self.value = round(a_value, 2)
            f_y_pos = (a_value * ADDITIVE_OSC_INC * -1.0)
            self.setPos(self.x_pos, f_y_pos)
            self.extend_to_bottom()
            return True
        else:
            return False

    def get_value(self):
        return round(self.value, 2)

    def extend_to_bottom(self):
        f_pos_y = clip_value(
            round(self.pos().y(), -1),
            ADDITIVE_OSC_INC,
            ADDITIVE_MAX_Y_POS,
        )
        self.setPos(self.x_pos, f_pos_y)
        self.setRect(
            0.0,
            0.0,
            float(ADDITIVE_OSC_BAR_WIDTH),
            float(ADDITIVE_OSC_HEIGHT - f_pos_y - 1.0),
        )

class additive_wav_viewer(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)
        self.setToolTip("The resulting waveform of the harmonics")
        self.setMaximumWidth(600)
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(ADD_OSC_BACKGROUND)
        self.setSceneRect(
            0.0,
            0.0,
            float(ADDITIVE_WAVETABLE_SIZE),
            float(ADDITIVE_OSC_HEIGHT),
        )
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def draw_array(self, a_np_array):
        self.setUpdatesEnabled(False)
        f_path = QPainterPath(
            QtCore.QPointF(
                0.0,
                ADDITIVE_OSC_HEIGHT * 0.5,
            )
        )
        f_x = 1.0
        f_half = ADDITIVE_OSC_HEIGHT * 0.5
        for f_point in a_np_array:
            f_path.lineTo(f_x, (f_point * f_half) + f_half)
            f_x += 1.0
        self.scene.clear()
        f_path_item = self.scene.addPath(
            f_path, QPen(QtCore.Qt.GlobalColor.white, 1.0))
        f_path_item.setBrush(ADD_OSC_FILL)
        self.setUpdatesEnabled(True)
        self.update()

    def resizeEvent(self, a_resize_event):
        QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / ADDITIVE_WAVETABLE_SIZE
        self.last_y_scale = f_rect.height() / ADDITIVE_OSC_HEIGHT
        self.scale(self.last_x_scale, self.last_y_scale)


class additive_osc_viewer(QGraphicsView):
    def __init__(
        self,
        a_draw_callback,
        a_configure_callback,
        a_get_wav,
        tooltip,
    ):
        QGraphicsView.__init__(self)
        self.setToolTip(tooltip)
        self.setMaximumWidth(600)
        self.configure_callback = a_configure_callback
        self.get_wav = a_get_wav
        self.draw_callback = a_draw_callback
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.is_drawing = False
        self.edit_mode = 0
        self.setMinimumSize(
            ADDITIVE_OSC_WIDTH, ADDITIVE_OSC_HEIGHT)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.mousePressEvent = self.scene_mousePressEvent
        self.scene.mouseReleaseEvent = self.scene_mouseReleaseEvent
        self.scene.mouseMoveEvent = self.scene_mouseMoveEvent
        self.scene.setBackgroundBrush(ADD_OSC_BACKGROUND)
        self.setSceneRect(
            0.0,
            0.0,
            float(ADDITIVE_OSC_WIDTH),
            float(ADDITIVE_OSC_HEIGHT),
        )
        self.bars = []
        for f_i in range(
        0, ADDITIVE_OSC_WIDTH, int(ADDITIVE_OSC_BAR_WIDTH)):
            f_bar = additive_osc_amp_bar(f_i)
            self.bars.append(f_bar)
            self.scene.addItem(f_bar)

    def set_edit_mode(self, a_mode):
        self.edit_mode = a_mode

    def resizeEvent(self, a_resize_event):
        QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / ADDITIVE_OSC_WIDTH
        self.last_y_scale = f_rect.height() / ADDITIVE_OSC_HEIGHT
        self.scale(self.last_x_scale, self.last_y_scale)

    def scene_mousePressEvent(self, a_event):
        QGraphicsScene.mousePressEvent(self.scene, a_event)
        self.is_drawing = True
        self.draw_harmonics(a_event.scenePos())

    def scene_mouseReleaseEvent(self, a_event):
        QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.is_drawing = False
        self.get_wav(True)

    def scene_mouseMoveEvent(self, a_event):
        if self.is_drawing:
            QGraphicsScene.mouseMoveEvent(self.scene, a_event)
            self.draw_harmonics(a_event.scenePos())

    def clear_osc(self):
        for f_point in self.bars:
            f_point.set_value(ADDITIVE_OSC_MIN_AMP)
        self.get_wav()

    def open_osc(self, a_arr):
        for f_val, f_point in zip(a_arr, self.bars):
            f_point.set_value(float(f_val))
        self.get_wav()

    def draw_harmonics(self, a_pos):
        f_pos = a_pos
        f_pos_x = f_pos.x()
        f_pos_y = f_pos.y()
        f_db = round((f_pos_y / ADDITIVE_OSC_HEIGHT) * ADDITIVE_OSC_MIN_AMP, 2)
        f_harmonic = int((f_pos_x / ADDITIVE_OSC_WIDTH) *
            ADDITIVE_OSC_HARMONIC_COUNT)
        if f_harmonic < 0:
            f_harmonic = 0
        elif f_harmonic >= ADDITIVE_OSC_HARMONIC_COUNT:
            f_harmonic = ADDITIVE_OSC_HARMONIC_COUNT - 1
        if self.edit_mode == 1 and (f_harmonic % 2) != 0:
            return
        if f_db > 0:
            f_db = 0
        elif f_db < ADDITIVE_OSC_MIN_AMP:
            f_db = ADDITIVE_OSC_MIN_AMP
        if self.bars[int(f_harmonic)].set_value(f_db):
            self.get_wav()


class custom_additive_oscillator(abstract_custom_oscillator):
    def __init__(self, a_configure_callback=None, a_osc_count=3):
        abstract_custom_oscillator.__init__(self)
        self.configure_callback = a_configure_callback
        self.hlayout = QHBoxLayout()
        self.layout.addLayout(self.hlayout)
        self.osc_num = 0
        self.hlayout.addWidget(QLabel(_("Oscillator#:")))
        self.osc_num_combobox = QComboBox()
        self.osc_num_combobox.setToolTip(
            'The oscillator number to view or modify.  There are 3 additive '
            'oscillators to choose from in the oscillator dropdown menu for '
            'each oscillator'
        )
        self.osc_num_combobox.setMinimumWidth(66)
        self.hlayout.addWidget(self.osc_num_combobox)
        for f_i in range(1, a_osc_count + 1):
            self.osc_num_combobox.addItem(str(f_i))
        self.osc_num_combobox.currentIndexChanged.connect(
            self.osc_index_changed)
        self.hlayout.addWidget(QLabel(_("Edit Mode:")))
        self.edit_mode_combobox = QComboBox()
        self.edit_mode_combobox.setToolTip(
            'Changes whether editing harmonics with the mouse affects all '
            'harmonics or only odd harmonics.  Choose odd harmonics for '
            'creating square-wave-like sounds, all harmonics for saw-wave-like'
        )
        self.edit_mode_combobox.setMinimumWidth(90)
        self.hlayout.addWidget(self.edit_mode_combobox)
        self.edit_mode_combobox.addItems([_("All"), _("Odd")])
        self.edit_mode_combobox.currentIndexChanged.connect(
            self.edit_mode_combobox_changed)
        self.tools_button = QPushButton(_("Tools"))
        self.hlayout.addWidget(self.tools_button)
        self.tools_menu = QMenu(self.tools_button)
        self.tools_button.setMenu(self.tools_menu)

        self.hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.hlayout.addWidget(
            QLabel(_("Select (Additive [n]) as your osc type to use")))
        self.wav_viewer = additive_wav_viewer()
        self.draw_callback = self.wav_viewer.draw_array
        self.viewer = additive_osc_viewer(
            self.wav_viewer.draw_array,
            self.configure_wrapper,
            self.get_wav,
            tooltip=(
                "The amplitudes of the harmonics.  Harmonics are frequency "
                "multiples of the MIDI note.  If the note is 300hz, the 10th "
                "harmonic is 3000hz"
            )
        )
        self.phase_viewer = additive_osc_viewer(
            self.wav_viewer.draw_array,
            self.configure_wrapper,
            self.get_wav,
            tooltip=(
                "The phases of the harmonics.  Harmonics are frequency "
                "multiples of the MIDI note.  If the note is 300hz, the 10th "
                "harmonic is 3000hz"
            )
        )
        self.view_widget = QWidget()
        self.view_widget.setMaximumSize(900, 540)
        self.vlayout2 = QVBoxLayout()
        self.hlayout2 = QHBoxLayout(self.view_widget)
        self.layout.addWidget(self.view_widget)
        self.hlayout2.addLayout(self.vlayout2)
        self.vlayout2.addWidget(self.viewer)
        self.vlayout2.addWidget(self.phase_viewer)
        self.hlayout2.addWidget(self.wav_viewer)

        f_saw_action = self.tools_menu.addAction(_("Set Saw"))
        f_saw_action.triggered.connect(self.set_saw)
        f_square_action = self.tools_menu.addAction(_("Set Square"))
        f_square_action.triggered.connect(self.set_square)
        f_tri_action = self.tools_menu.addAction(_("Set Triangle"))
        f_tri_action.triggered.connect(self.set_triangle)
        f_sine_action = self.tools_menu.addAction(_("Set Sine"))
        f_sine_action.triggered.connect(self.set_sine)
        self.osc_values = {0 : None, 1 : None, 2 : None}
        self.phase_values = {0 : None, 1 : None, 2 : None}

    def configure_wrapper(self, a_key, a_val):
        if self.configure_callback is not None:
            self.configure_callback(a_key, a_val)
        f_index = int(a_key[-1])
        if a_key.startswith("fm1_add_ui"):
            self.osc_values[f_index] = a_val.split("|")
        elif a_key.startswith("fm1_add_phase"):
            self.phase_values[f_index] = a_val.split("|")

    def osc_index_changed(self, a_event):
        self.osc_num = self.osc_num_combobox.currentIndex()
        if self.osc_values[self.osc_num] is None:
            self.viewer.clear_osc()
        else:
            self.viewer.open_osc(self.osc_values[self.osc_num])
        if self.phase_values[self.osc_num] is None:
            self.phase_viewer.clear_osc()
        else:
            self.phase_viewer.open_osc(self.phase_values[self.osc_num])

    def edit_mode_combobox_changed(self, a_event):
        self.viewer.set_edit_mode(self.edit_mode_combobox.currentIndex())

    def set_values(self, a_num, a_val):
        self.osc_values[int(a_num)] = a_val
        if self.osc_num_combobox.currentIndex() == int(a_num):
            self.osc_index_changed(None)

    def set_phases(self, a_num, a_val):
        self.phase_values[int(a_num)] = a_val
        if self.osc_num_combobox.currentIndex() == int(a_num):
            self.osc_index_changed(None)

    def get_wav(self, a_configure=False):
        f_result = numpy.zeros(ADDITIVE_WAVETABLE_SIZE)
        f_recall_list = []
        f_phase_list = []
        for f_i in range(1, ADDITIVE_OSC_HARMONIC_COUNT + 1):
            f_size = int(ADDITIVE_WAVETABLE_SIZE / f_i)
            f_db = self.viewer.bars[f_i - 1].get_value()
            f_phase = self.phase_viewer.bars[f_i - 1].get_value()
            if a_configure:
                f_recall_list.append("{}".format(f_db))
                f_phase_list.append("{}".format(f_phase))
            f_phase = (f_phase + (ADDITIVE_OSC_MIN_AMP * -1.0)) / (
                ADDITIVE_OSC_MIN_AMP / 2)
            if f_db > (ADDITIVE_OSC_MIN_AMP + 1):
                f_sin = global_get_sine(
                    f_size, f_phase) * db_to_lin(f_db)
                for f_i2 in range(
                int(ADDITIVE_WAVETABLE_SIZE / f_size)):
                    f_start = (f_i2) * f_size
                    f_end = f_start + f_size
                    f_result[f_start:f_end] += f_sin
        f_max = numpy.max(numpy.abs(f_result), axis=0)
        if f_max > 0.0:
            f_normalize = 0.99 / f_max
            f_result *= f_normalize
        self.draw_callback(f_result)
        if a_configure and self.configure_callback is not None:
            f_engine_list = [str(ADDITIVE_WAVETABLE_SIZE)]
            for f_float in f_result:
                f_engine_list.append(
                    str(round(f_float, 6)),
                )
            assert len(f_engine_list) == ADDITIVE_WAVETABLE_SIZE + 1, \
                (len(f_engine_list), ADDITIVE_WAVETABLE_SIZE)
            f_engine_str = "|".join(f_engine_list)
            engine_str_len = len(f_engine_str)
            LOG.info(f"Sending additive osc str of length {engine_str_len}")
            self.configure_wrapper(
                "fm1_add_eng{}".format(self.osc_num),
                f_engine_str,
            )
            self.configure_wrapper(
                "fm1_add_ui{}".format(self.osc_num),
                "|".join(f_recall_list),
            )
            self.configure_wrapper(
                "fm1_add_phase{}".format(self.osc_num),
                "|".join(f_phase_list),
            )

    def set_saw(self):
        for f_i in range(len(self.viewer.bars)):
            f_db = round(lin_to_db(1.0 / (f_i + 1)), 2)
            self.viewer.bars[f_i].set_value(f_db)
        for f_i in range(len(self.phase_viewer.bars)):
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        for f_i in range(1, len(self.phase_viewer.bars), 2):
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP / 2)
        self.get_wav(True)

    def set_square(self):
        f_odd = True
        for f_i in range(len(self.viewer.bars)):
            f_point = self.viewer.bars[f_i]
            if f_odd:
                f_db = round(lin_to_db(1.0 / (f_i + 1)), 2)
                f_odd = False
                f_point.set_value(f_db)
            else:
                f_odd = True
                f_point.set_value(ADDITIVE_OSC_MIN_AMP)
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        self.get_wav(True)

    def set_triangle(self):
        f_odd = True
        for f_i in range(len(self.viewer.bars)):
            f_point = self.viewer.bars[f_i]
            if f_odd:
                f_num = f_i + 1
                f_db = round(
                    lin_to_db(1.0 / (f_num * f_num)), 2)
                f_odd = False
                f_point.set_value(f_db)
            else:
                f_odd = True
                f_point.set_value(ADDITIVE_OSC_MIN_AMP)
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        self.phase_viewer.bars[2].set_value(ADDITIVE_OSC_MIN_AMP / 2.0)
        self.get_wav(True)

    def set_sine(self):
        self.viewer.bars[0].set_value(0)
        for f_point in self.viewer.bars[1:]:
            f_point.set_value(ADDITIVE_OSC_MIN_AMP)
        for f_i in range(len(self.phase_viewer.bars)):
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        self.get_wav(True)

