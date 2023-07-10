from sglib import constants
from sglib.lib import strings as sg_strings, util
from sglib.lib.translate import _
from sglib.log import LOG
from sglib.math import db_to_lin
from sglib.models.theme import get_asset_path
from sgui import shared
from sgui.sgqt import *
from sgui import widgets
import time


class TransportWidget:
    def __init__(self, scaler):
        self.suppress_osc = True
        self.last_clock_text = None
        self.last_open_dir = util.HOME

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(36, 36))
        self.toolbar.setObjectName('transport_panel')
        self.group_box = self.toolbar

        self.menu_button = QToolButton(self.toolbar)
        self.menu_button.setIcon(
            QIcon(
                get_asset_path('menu.svg'),
            ),
        )
        self.menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.toolbar.addWidget(self.menu_button)

        self.toolbar.addSeparator()

        self.play_group = QActionGroup(self.toolbar)

        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('play-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('play-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.play_button = QAction(icon, '', self.play_group)
        self.play_button.setToolTip(
            'Begin playback.  Press spacebar to toggle',
        )
        self.play_button.setCheckable(True)
        self.play_button.triggered.connect(self.on_play)
        self.toolbar.addAction(self.play_button)

        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('stop-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('stop-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.stop_button = QAction(icon, '', self.play_group)
        self.stop_button.setToolTip(
            'Stop playback or recording.  Press spacebar to toggle',
        )
        self.stop_button.setCheckable(True)
        self.stop_button.setChecked(True)
        self.stop_button.triggered.connect(self.on_stop)
        self.toolbar.addAction(self.stop_button)

        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('rec-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('rec-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.rec_button = QAction(icon, '', self.play_group)
        self.rec_button.setToolTip(
            'Stop playback or recording.  Press spacebar to toggle',
        )
        self.rec_button.setCheckable(True)
        self.rec_button.triggered.connect(self.on_rec)
        self.toolbar.addAction(self.rec_button)

        self.clock = QLCDNumber()
        self.clock.setToolTip(
            'The real time of the project, in minutes:seconds.1/10s.  '
            'For musical time, see the sequencer timeline'
        )
        self.clock.setObjectName("transport_clock")
        self.clock.setDigitCount(7)
        self.clock.setFixedHeight(42)
        self.clock.setFixedWidth(180)
        self.clock.display("0:00.0")
        self.toolbar.addWidget(self.clock)

        self.panic_button = QToolButton(self.toolbar)
        self.panic_button.setIcon(
            QIcon(
                get_asset_path('panic.svg'),
            ),
        )
        self.panic_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.panic_menu = QMenu()
        self.panic_button.setMenu(self.panic_menu)
        self.all_notes_off_action = QAction("All notes off")
        self.all_notes_off_action.setToolTip(
            'Send a note off MIDI event on every note, to every plugin.  '
            'Use this if you have hung notes'
        )
        self.panic_menu.addAction(self.all_notes_off_action)
        self.all_notes_off_action.triggered.connect(self.on_panic)

        self.panic_menu.addSeparator()

        self.stop_engine_action = QAction(_("Stop Audio Engine"))
        self.stop_engine_action.setToolTip(
            'Stop the audio engine.  You will need to restart the '
            'application.  Use this in the event of loud unexpected noises '
            'coming out of the audio engine'
        )
        self.panic_menu.addAction(self.stop_engine_action)
        self.stop_engine_action.triggered.connect(self.on_stop_engine)

        self.toolbar.addWidget(self.panic_button)

        self.host_widget = QWidget(self.toolbar)
        self.host_widget.setObjectName('transport_widget')
        self.host_layout = QVBoxLayout(self.host_widget)
        self.host_layout.setContentsMargins(1, 1, 1, 1)
        self.host_layout.setSpacing(1)
        host_label = QLabel("Host")
        host_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        host_label.setObjectName('transport_widget')
        self.host_layout.addWidget(host_label)
        self.toolbar.addWidget(
            self.host_widget,
        )
        self.host_combobox = QComboBox()
        self.host_layout.addWidget(self.host_combobox)
        self.host_combobox.setMinimumWidth(85)
        self.host_combobox.addItems(["DAW", "Wave Editor"])
        self.host_combobox.currentIndexChanged.connect(
            shared.MAIN_WINDOW.set_host,
        )
        self.host_combobox.setToolTip(
            'The host to use.  DAW is a full digital audio workstation '
            'optimized for producing electronic music.  Wave Editor '
            'is a basic wave editor for simple editing tasks'
        )
        knob_size = 40
        self.main_vol_knob = widgets.PixmapKnob(
            knob_size,
            -480,
            0,
            arc_width_pct=0.0,
            arc_space=0.0,
            fg_svg='default',
            bg_svg='default_bg',
        )
        self.load_main_vol()
        self.toolbar.addWidget(self.main_vol_knob)
        self.main_vol_knob.valueChanged.connect(self.main_vol_changed)
        self.main_vol_knob.sliderReleased.connect(self.main_vol_released)
        self.main_vol_knob.setToolTip(
            'Master volume.  Only affects your monitor speakers, not renders.'
        )
        self.suppress_osc = False

        self.controls_to_disable = (self.menu_button, self.host_combobox)

    def current_host(self) -> int:
        return self.host_combobox.currentIndex()

    def enable_controls(self, a_enabled):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(a_enabled)

    def on_stop_engine(self):
        constants.IPC.kill_engine()
        QMessageBox.warning(
            None,
            None,
            (
                'Audio engine has been requested to stop immediately.  '
                'You will need to close and re-open Stargate DAW to '
                'continue using'
            ),
        )
        if shared.IS_PLAYING:
            self.stop_button.trigger()

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
            self.stop_button.trigger()
        else:
            self.play_button.trigger()

    def on_play(self):
        if not self.play_button.isChecked():
            return
        if shared.IS_PLAYING:
            self.play_button.setChecked(True)
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

