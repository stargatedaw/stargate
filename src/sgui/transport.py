from sglib import constants
from sglib.lib import strings as sg_strings, util
from sglib.lib.translate import _
from sglib.log import LOG
from sglib.math import db_to_lin
from sglib.models import theme
from sgui import shared
from sgui.sgqt import *
from sgui import widgets
import time


class TransportWidget:
    def __init__(self, scaler):
        self.suppress_osc = True
        self.last_clock_text = None
        self.last_open_dir = util.HOME
        self.group_box = QWidget()
        self.group_box.setObjectName("transport_panel")
        self.vlayout = QVBoxLayout()
        self.vlayout.setContentsMargins(1, 1, 1, 1)
        self.vlayout.setSpacing(1)
        self.group_box.setLayout(self.vlayout)
        self.hlayout1 = QHBoxLayout()
        self.hlayout1.setContentsMargins(1, 1, 1, 1)
        self.hlayout1.setSpacing(1)
        self.menu_button = QPushButton()
        self.menu_button.setObjectName("menu")
        self.hlayout1.addWidget(self.menu_button)
        self.vlayout.addLayout(self.hlayout1)
        self.play_button = QRadioButton()
        self.play_button.setObjectName("play_button")
        self.play_button.toggled.connect(self.on_play)
        self.hlayout1.addWidget(self.play_button)
        self.stop_button = QRadioButton()
        self.stop_button.setChecked(True)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.toggled.connect(self.on_stop)
        self.hlayout1.addWidget(self.stop_button)
        self.rec_button = QRadioButton()
        self.rec_button.setObjectName("rec_button")
        self.rec_button.toggled.connect(self.on_rec)
        self.hlayout1.addWidget(self.rec_button)
        self.clock = QLCDNumber()
        self.clock.setObjectName("transport_clock")
        self.clock.setDigitCount(7)
        self.clock.setFixedHeight(42)
        self.clock.setFixedWidth(180)
        self.clock.display("0:00.0")
        self.hlayout1.addWidget(self.clock)

        self.panic_button = QPushButton()
        self.panic_button.setObjectName("panic")
        self.panic_menu = QMenu()
        self.panic_button.setMenu(self.panic_menu)
        self.all_notes_off_action = self.panic_menu.addAction("All notes off")
        self.all_notes_off_action.triggered.connect(self.on_panic)
        self.panic_menu.addSeparator()
        self.stop_engine_action = self.panic_menu.addAction(
            _("Stop Audio Engine"),
        )
        self.stop_engine_action.triggered.connect(self.on_stop_engine)
        self.hlayout1.addWidget(self.panic_button)

        self.host_layout = QVBoxLayout()
        self.host_layout.setContentsMargins(1, 1, 1, 1)
        self.host_layout.setSpacing(1)
        self.host_layout.addWidget(
            QLabel(_("Host")),
        )
        self.hlayout1.addLayout(
            self.host_layout,
        )
        self.host_combobox = QComboBox()
        self.host_layout.addWidget(self.host_combobox)
        self.host_combobox.setMinimumWidth(85)
        self.host_combobox.addItems(["DAW", "Wave Editor"])
        self.host_combobox.currentIndexChanged.connect(
            shared.MAIN_WINDOW.set_host,
        )
        knob_size = 40
        self.main_vol_knob = widgets.PixmapKnob(knob_size, -480, 0)
        self.load_main_vol()
        self.hlayout1.addWidget(self.main_vol_knob)
        self.main_vol_knob.valueChanged.connect(self.main_vol_changed)
        self.main_vol_knob.sliderReleased.connect(self.main_vol_released)
        self.suppress_osc = False

        self.controls_to_disable = (self.menu_button, self.host_combobox)

    def current_host(self) -> int:
        return self.host_combobox.currentIndex()

    def enable_controls(self, a_enabled):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(a_enabled)

    def on_stop_engine(self):
        constants.IPC.kill_engine()

    def main_vol_released(self):
        util.set_file_setting(
            "main_vol",
            self.main_vol_knob.value()
        )

    def load_main_vol(self):
        self.main_vol_knob.setValue(
            util.get_file_setting(
                "main_vol",
                int,
                0,
            ),
        )

    def main_vol_changed(self, a_val):
        if a_val == 0:
            f_result = 1.0
        else:
            f_result = db_to_lin(float(a_val) * 0.1)
        constants.IPC.main_vol(f_result)

    def set_time(self, a_text):
        if a_text == self.last_clock_text:
            return
        self.last_clock_text = a_text
        self.clock.display(a_text)

    def on_spacebar(self):
        if shared.IS_PLAYING:
            self.stop_button.click()
        else:
            self.play_button.click()

    def on_play(self):
        if not self.play_button.isChecked():
            return
        if shared.IS_RECORDING:
            self.rec_button.setChecked(True)
            return
        if shared.MAIN_WINDOW.current_module.TRANSPORT.on_play():
            shared.IS_PLAYING = True
            self.enable_controls(False)
        else:
            self.stop_button.setChecked(True)

    def on_stop(self):
        if not self.stop_button.isChecked():
            return
        if not shared.IS_PLAYING and not shared.IS_RECORDING:
            return
        shared.MAIN_WINDOW.current_module.TRANSPORT.on_stop()
        shared.IS_PLAYING = False
        shared.IS_RECORDING = False
        self.enable_controls(True)
        time.sleep(0.1)

    def on_rec(self):
        if not self.rec_button.isChecked():
            return
        if shared.IS_RECORDING:
            return
        if shared.IS_PLAYING:
            self.play_button.setChecked(True)
            return
        if shared.MAIN_WINDOW.current_module.TRANSPORT.on_rec():
            shared.IS_PLAYING = True
            shared.IS_RECORDING = True
            self.enable_controls(False)
        else:
            self.stop_button.setChecked(True)

    def on_panic(self):
        LOG.info("Sending panic message to engine")
        shared.MAIN_WINDOW.current_module.TRANSPORT.on_panic()

    def set_tooltips(self, a_enabled):
        if a_enabled:
            self.panic_button.setToolTip(
                _(
                    "Panic button:   Sends a note-off signal on every "
                    "note to every instrument\nYou can also use CTRL+P"
                )
            )
            self.group_box.setToolTip(sg_strings.transport)
        else:
            self.panic_button.setToolTip("")
            self.group_box.setToolTip("")

