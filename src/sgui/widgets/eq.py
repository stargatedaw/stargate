from . import _shared
from .control import *
from .spectrum import spectrum
from sglib.math import clip_value, pitch_to_hz, hz_to_pitch
from sglib.lib import util
from sglib.lib.translate import _
from sgui.sgqt import *
from sgui.util import get_font


class eq_item(QGraphicsEllipseItem):
    def __init__(self, a_eq, a_num, a_val_callback):
        QGraphicsEllipseItem.__init__(
            self, 0, 0, _shared.EQ_POINT_DIAMETER, _shared.EQ_POINT_DIAMETER)
        self.val_callback = a_val_callback
        self.eq = a_eq
        self.num = a_num
        self.setToolTip("EQ{}".format(self.num))
        self.setBrush(_shared.EQ_POINT_BRUSH)
        self.mapToScene(0.0, 0.0)
        self.path_item = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def mouseMoveEvent(self, a_event):
        QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        f_pos = self.pos()
        f_pos_x = clip_value(
            f_pos.x(), -_shared.EQ_POINT_RADIUS, _shared.EQ_WIDTH)
        f_pos_y = clip_value(
            f_pos.y(), -_shared.EQ_POINT_RADIUS, _shared.EQ_HEIGHT)

        if f_pos_x != f_pos.x() or f_pos_y != f_pos.y():
            self.setPos(f_pos_x, f_pos_y)

        f_freq, f_gain = self.get_value()
        self.val_callback(self.eq.freq_knob.port_num, f_freq)
        self.val_callback(self.eq.gain_knob.port_num, f_gain)
        self.eq.freq_knob.set_value(f_freq)
        self.eq.gain_knob.set_value(f_gain)
        self.draw_path_item()

    def mouseReleaseEvent(self, a_event):
        QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        self.eq.freq_knob.control_value_changed(self.eq.freq_knob.get_value())
        self.eq.gain_knob.control_value_changed(self.eq.gain_knob.get_value())

    def set_pos(self):
        f_freq = self.eq.freq_knob.get_value()
        f_gain = self.eq.gain_knob.get_value()
        f_x = (((f_freq - _shared.EQ_LOW_PITCH) / _shared.EQ_HIGH_PITCH) *
            _shared.EQ_WIDTH) - _shared.EQ_POINT_RADIUS
        f_y = ((1.0 - ((f_gain + 240.0) / 480.0)) *
            _shared.EQ_HEIGHT) - _shared.EQ_POINT_RADIUS
        self.setPos(f_x, f_y)
        self.draw_path_item()

    def get_value(self):
        f_pos = self.pos()
        f_freq = (
            (
                (f_pos.x() + _shared.EQ_POINT_RADIUS) / _shared.EQ_WIDTH
            ) * _shared.EQ_HIGH_PITCH) + _shared.EQ_LOW_PITCH
        f_freq = clip_value(
            f_freq, _shared.EQ_LOW_PITCH, _shared.EQ_HIGH_PITCH)
        f_gain = ((1.0 - ((f_pos.y() + _shared.EQ_POINT_RADIUS) /
            _shared.EQ_HEIGHT)) * 480.0) - 240.0
        f_gain = clip_value(f_gain, -240.0, 240.0)
        return round(f_freq, 2), round(f_gain, 1)

    def __lt__(self, other):
        return self.pos().x() < other.pos().x()

    def draw_path_item(self):
        f_res = self.eq.res_knob.get_value()

        if self.path_item is not None:
            self.scene().removeItem(self.path_item)

        f_line_pen = QPen(QColor(255, 255, 255, 210), 2.0)
        f_path = QPainterPath()

        f_pos = self.pos()
        f_bw = (f_res * 0.01)
        f_point_x = f_pos.x() + _shared.EQ_POINT_RADIUS
        f_point_y = f_pos.y() + _shared.EQ_POINT_RADIUS
        f_start_x = f_point_x - ((f_bw * 0.5 * _shared.EQ_OCTAVE_PX))
        f_end_x = f_point_x + ((f_bw * 0.5 * _shared.EQ_OCTAVE_PX))

        f_path.moveTo(f_start_x, _shared.EQ_HEIGHT * 0.5)

        f_path.lineTo(f_point_x, f_point_y)

        f_path.lineTo(f_end_x, _shared.EQ_HEIGHT * 0.5)

        self.path_item = QGraphicsPathItem(f_path)
        self.path_item.setPen(f_line_pen)
        self.path_item.setBrush(_shared.EQ_FILL)
        self.scene().addItem(self.path_item)


class eq_viewer(QGraphicsView):
    def __init__(self, a_val_callback):
        QGraphicsView.__init__(self)
        self.val_callback = a_val_callback
        self.eq_points = []
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(_shared.EQ_BACKGROUND)
        self.setScene(self.scene)
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorViewCenter,
        )
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.eq_points = []
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setSceneRect(
            float(-_shared.EQ_POINT_RADIUS),
            float(-_shared.EQ_POINT_RADIUS),
            float(_shared.EQ_WIDTH + _shared.EQ_POINT_RADIUS),
            float(_shared.EQ_HEIGHT + _shared.EQ_POINT_DIAMETER),
        )

    def set_spectrum(self, a_message):
        self.spectrum.set_spectrum(a_message)

    def draw_eq(self, a_eq_list=[]):
        f_hline_pen = QPen(QColor(255, 255, 255, 90), 1.0)
        f_vline_pen = QPen(QColor(255, 255, 255, 150), 2.0)

        f_label_pos = 0.0

        self.scene.clear()
        self.spectrum = spectrum(_shared.EQ_HEIGHT, _shared.EQ_WIDTH)
        self.scene.addItem(self.spectrum)

        f_y_pos = 0.0
        f_db = 24.0
        f_inc = (_shared.EQ_HEIGHT * 0.5) * 0.25

        for i in range(4):
            self.scene.addLine(
                0.0,
                f_y_pos,
                _shared.EQ_WIDTH,
                f_y_pos,
                f_hline_pen,
            )
            f_label = get_font().QGraphicsSimpleTextItem(str(f_db))
            f_label.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            )
            self.scene.addItem(f_label)
            f_label.setPos(_shared.EQ_WIDTH - 36.0, f_y_pos + 3.0)
            f_label.setBrush(QtCore.Qt.GlobalColor.white)
            f_db -= 6.0
            f_y_pos += f_inc

        self.scene.addLine(
            0.0,
            _shared.EQ_HEIGHT * 0.5,
            _shared.EQ_WIDTH,
            _shared.EQ_HEIGHT * 0.5,
            QPen(
                QColor(255, 255, 255, 210),
                2.0,
            ),
        )

        f_y_pos = _shared.EQ_HEIGHT
        f_db = -24.0

        for i in range(4):
            self.scene.addLine(
                0.0,
                f_y_pos,
                _shared.EQ_WIDTH,
                f_y_pos,
                f_hline_pen,
            )
            f_label = get_font().QGraphicsSimpleTextItem(str(f_db))
            f_label.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            )
            self.scene.addItem(f_label)
            f_label.setPos(_shared.EQ_WIDTH - 36.0, f_y_pos - 24.0)
            f_label.setBrush(QtCore.Qt.GlobalColor.white)
            f_db += 6.0
            f_y_pos -= f_inc

        f_label_pos = 0.0
        f_pitch = _shared.EQ_LOW_PITCH
        f_pitch_inc = 17.0
        f_label_inc = _shared.EQ_WIDTH / (_shared.EQ_HIGH_PITCH / f_pitch_inc)

        for i in range(7):
            f_hz = int(pitch_to_hz(f_pitch))
            if f_hz > 950:
                f_hz = round(f_hz, -1)
                f_hz = "{}khz".format(round(f_hz / 1000, 1))
            f_label = get_font().QGraphicsSimpleTextItem(str(f_hz))
            f_label.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            )
            self.scene.addItem(f_label)
            f_label.setPos(
                f_label_pos + 4.0,
                _shared.EQ_HEIGHT - 30.0,
            )
            self.scene.addLine(
                f_label_pos,
                0.0,
                f_label_pos,
                _shared.EQ_HEIGHT,
                f_vline_pen,
            )
            f_label.setBrush(QtCore.Qt.GlobalColor.white)
            f_label_pos += f_label_inc
            f_pitch += f_pitch_inc

        self.eq_points = []

        for f_eq, f_num in zip(a_eq_list, range(1, len(a_eq_list) + 1)):
            f_eq_point = eq_item(f_eq, f_num, self.val_callback)
            self.eq_points.append(f_eq_point)
            self.scene.addItem(f_eq_point)
            f_eq_point.set_pos()


    def resizeEvent(self, a_resize_event):
        QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(
            1.0 / self.last_x_scale if self.last_x_scale else 1.0,
            1.0 / self.last_y_scale if self.last_y_scale else 1.0,
        )
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / (
            _shared.EQ_WIDTH + _shared.EQ_POINT_DIAMETER + 3.0
        )
        self.last_y_scale = f_rect.height() / (
            _shared.EQ_HEIGHT + _shared.EQ_POINT_DIAMETER + 3.0
        )
        self.scale(self.last_x_scale, self.last_y_scale)



class eq_widget:
    def __init__(
        self,
        a_number,
        a_freq_port,
        a_res_port,
        a_gain_port,
        a_rel_callback,
        a_val_callback,
        a_default_value,
        a_port_dict=None,
        a_preset_mgr=None,
        a_size=48,
        knob_kwargs={},
    ):
        self.groupbox = QGroupBox("EQ{}".format(a_number))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)

        self.freq_knob = knob_control(
            a_size,
            "Freq",
            a_freq_port,
            a_rel_callback,
            a_val_callback,
            _shared.EQ_LOW_PITCH,
            _shared.EQ_HIGH_PITCH,
            a_default_value,
            _shared.KC_PITCH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip='The frequency to adjust gain at',
        )
        self.freq_knob.add_to_grid_layout(self.layout, 0)

        self.res_knob = knob_control(
            a_size,
            "BW",
            a_res_port,
            a_rel_callback,
            a_val_callback,
            100.0,
            600.0,
            300.0,
            _shared.KC_DECIMAL,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Resonance, bandwidth or "Q". Higher values result in a wider '
                'frequency band, lower values result i a narrower frequency '
                'band'
            ),
        )
        self.res_knob.add_to_grid_layout(self.layout, 1)

        self.gain_knob = knob_control(
            a_size,
            _("Gain"),
            a_gain_port,
            a_rel_callback,
            a_val_callback,
            -240.0,
            240.0,
            0.0,
            _shared.KC_TENTH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'EQ gain, in decibels.  0 means no change, values greater '
                'than 0 increase volume at this frequency, values less than '
                '0 decrease volume at this frequency'
            ),
        )
        self.gain_knob.add_to_grid_layout(self.layout, 2)

EQ6_CLIPBOARD = None

EQ6_FORMANTS = {
    "soprano a":((800, 1150, 2900, 3900, 4950), (0, -6, -32, -20, -50),
                 (80, 90, 120, 130, 140)),
    "soprano e":((350, 2000, 2800, 3600, 4950), (0, -20, -15, -40, -56),
                 (60, 100, 120, 150, 200)),
    "soprano i":((270, 2140, 2950, 3900, 4950), (0, -12, -26, -26, -44),
                 (60, 90, 100, 120, 120)),
    "soprano o":((450, 800, 2830, 3800, 4950), (0, -11, -22, -22, -50),
                 (70, 80, 100, 130, 135)),
    "soprano u":((325, 700, 2700, 3800, 4950), (0, -16, -35, -40, -60),
                 (50, 60, 170, 180, 200)),
    "alto a":((800, 1150, 2800, 3500, 4950), (0, -4, -20, -36, -60),
              (80, 90, 120, 130, 140)),
    "alto e":((400, 1600, 2700, 3300, 4950), (0, -24, -30, -35, -60),
              (60, 80, 120, 150, 200)),
    "alto i":((350, 1700, 2700, 3700, 4950), (0, -20, -30, -36, -60),
              (50, 100, 120, 150, 200)),
    "alto o":((450, 800, 2830, 3500, 4950), (0, -9, -16, -28, -55),
              (70, 80, 100, 130, 135)),
    "alto u":((325, 700, 2530, 3500, 4950), (0, -12, -30, -40, -64),
              (50, 60, 170, 180, 200)),
    "countertenor a":((660, 1120, 2750, 3000, 3350), (0, -6, -23, -24, -38),
                      (80, 90, 120, 130, 140)),
    "countertenor e":((440, 1800, 2700, 3000, 3300), (0, -14, -18, -20, -20),
                      (70, 80, 100, 120, 120)),
    "countertenor i":((270, 1850, 2900, 3350, 3590), (0, -24, -24, -36, -36),
                      (40, 90, 100, 120, 120)),
    "countertenor o":((430, 820, 2700, 3000, 3300), (0, -10, -26, -22, -34),
                      (40, 80, 100, 120, 120)),
    "countertenor u":((370, 630, 2750, 3000, 3400), (0, -20, -23, -30, -34),
                      (40, 60, 100, 120, 120)),
    "tenor a":((650, 1080, 2650, 2900, 3250), (0, -6, -7, -8, -22),
               (80, 90, 120, 130, 140)),
    "tenor e":((400, 1700, 2600, 3200, 3580), (0, -14, -12, -14, -20),
               (70, 80, 100, 120, 120)),
    "tenor i":((290, 1870, 2800, 3250, 3540), (0, -15, -18, -20, -30),
               (40, 90, 100, 120, 120)),
    "tenor o":((400, 800, 2600, 2800, 3000), (0, -10, -12, -12, -26),
               (40, 80, 100, 120, 120)),
    "tenor u":((350, 600, 2700, 2900, 3300), (0, -20, -17, -14, -26),
               (40, 60, 100, 120, 120)),
    "bass a":((600, 1040, 2250, 2450, 2750), (0, -7, -9, -9, -20),
              (60, 70, 110, 120, 130)),
    "bass e":((400, 1620, 2400, 2800, 3100), (0, -12, -9, -12, -18),
              (40, 80, 100, 120, 120)),
    "bass i":((250, 1750, 2600, 3050, 3340), (0, -30, -16, -22, -28),
              (60, 90, 100, 120, 120)),
    "bass o":((400, 750, 2400, 2600, 2900), (0, -11, -21, -20, -40),
              (40, 80, 100, 120, 120)),
    "bass u":((350, 600, 2400, 2675, 2950), (0, -20, -32, -28, -36),
              (40, 80, 100, 120, 120))
}


class eq6_widget:
    def __init__(
        self,
        a_first_port,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_preset_mgr=None,
        a_size=48,
        a_vlayout=True,
        knob_kwargs={},
    ):
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.widget = QWidget()
        self.widget.setObjectName("plugin_ui")
        self.eq_viewer = eq_viewer(a_val_callback)

        self.vlayout = QVBoxLayout()
        self.combobox_hlayout = QHBoxLayout()
        self.grid_layout = QGridLayout()

        self.vlayout.addLayout(self.combobox_hlayout)
        self.vlayout.addWidget(self.eq_viewer)
        if a_vlayout:
            f_col_width = 3
            self.widget.setLayout(self.vlayout)
            self.vlayout.addLayout(self.grid_layout)
        else:
            f_col_width = 2
            self.hlayout = QHBoxLayout(self.widget)
            self.hlayout.addLayout(self.vlayout)
            self.hlayout.addLayout(self.grid_layout)

        self.combobox_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        self.menu_button = QPushButton(_("Menu"))
        self.menu = QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)

        self.copy_action = QAction("Copy", self.menu)
        self.copy_action.setToolTip(
            'Copy all of the EQ settings to the clipboard.  You can then '
            'paste the settings to another instance of the EQ plugin'
        )
        self.menu.addAction(self.copy_action)
        self.copy_action.triggered.connect(self.on_copy)

        self.paste_action = QAction('Paste', self.menu)
        self.paste_action.setToolTip(
            'Paste EQ settings previously copied using the Copy action'
        )
        self.menu.addAction(self.paste_action)
        self.paste_action.triggered.connect(self.on_paste)

        self.menu.addSeparator()

        self.formant_menu = self.menu.addMenu(_("Set Formant"))
        self.formant_menu.triggered.connect(self.set_formant)
        for k in sorted(EQ6_FORMANTS):
            f_action = QAction(k, self.formant_menu)
            f_action.setToolTip(
                'Set the EQ parameters to resemble common vowel sounds, '
                'use for vocal-like effects'
            )
            self.formant_menu.addAction(f_action)
            f_action.formant_name = k
        self.menu.addSeparator()
        self.reset_action = self.menu.addAction(_("Reset"))
        self.reset_action.triggered.connect(self.reset_controls)
        self.combobox_hlayout.addWidget(self.menu_button)

        self.eqs = []

        f_port = a_first_port
        f_default_value = 24

        f_x = 0
        f_y = 0

        for f_i in range(1, 7):
            f_eq = eq_widget(
                f_i,
                f_port,
                f_port + 1,
                f_port + 2,
                a_rel_callback,
                self.knob_callback,
                f_default_value,
                a_port_dict,
                a_preset_mgr,
                a_size,
                knob_kwargs=knob_kwargs,
            )
            self.eqs.append(f_eq)
            self.grid_layout.addWidget(f_eq.groupbox, f_y, f_x)

            f_x += 1
            if f_x >= f_col_width:
                f_x = 0
                f_y += 1
            f_port += 3
            f_default_value += 18
        self.update_viewer()

    def set_formant(self, a_action):
        f_key = a_action.formant_name
        f_hz_list, f_db_list, f_bw_list = EQ6_FORMANTS[f_key]
        for f_eq, f_hz, f_db, f_bw in zip(
        self.eqs, f_hz_list, f_db_list, f_bw_list):
            f_pitch = hz_to_pitch(f_hz)
            f_eq.freq_knob.set_value(f_pitch, True)
            f_bw_adjusted = f_bw + 60
            f_eq.res_knob.set_value(f_bw_adjusted, True)
            f_db_adjusted = (f_db * 0.3) + 21.0
            f_eq.gain_knob.set_value(f_db_adjusted, True)

    def set_spectrum(self, a_message):
        self.eq_viewer.set_spectrum(a_message)

    def on_paste(self):
        global EQ6_CLIPBOARD
        if EQ6_CLIPBOARD is not None:
            for f_eq, f_tuple in zip(self.eqs, EQ6_CLIPBOARD):
                f_eq.freq_knob.set_value(f_tuple[0], True)
                f_eq.res_knob.set_value(f_tuple[1], True)
                f_eq.gain_knob.set_value(f_tuple[2], True)

    def on_copy(self):
        global EQ6_CLIPBOARD
        EQ6_CLIPBOARD = []
        for f_eq in self.eqs:
            EQ6_CLIPBOARD.append(
            (f_eq.freq_knob.get_value(),
            f_eq.res_knob.get_value(),
            f_eq.gain_knob.get_value())
            )

    def knob_callback(self, a_port, a_val):
        self.val_callback(a_port, a_val)
        self.update_viewer()

    def update_viewer(self):
        self.eq_viewer.draw_eq(self.eqs)

    def reset_controls(self):
        for f_eq in self.eqs:
            f_eq.freq_knob.reset_default_value()
            f_eq.res_knob.reset_default_value()
            f_eq.gain_knob.reset_default_value()

class morph_eq(eq6_widget):
    def __init__(self, a_first_port, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None, a_size=48,
                 a_vlayout=True):
        raise NotImplementedError()
        self.rel_callback_orig = a_rel_callback
        self.val_callback_orig = a_val_callback
        eq6_widget.__init__(
            self, a_first_port, self.rel_callback_wrapper, a_val_callback,
            a_port_dict, a_preset_mgr, a_size, a_vlayout)
        self.eq_num_spinbox = QSpinBox()
        self.eq_num_spinbox.setRange(1, 2)
        self.eq_num_spinbox.valueChanged.connect(self.eq_num_changed)
        self.eq_values = {}

    def eq_num_changed(self, a_val=None):
        self.eq_index = self.eq_num_spinbox.value() - 1

    def val_callback_wrapper(self):
        pass

    def rel_callback_wrapper(self):
        pass


