from sgui.main import main
from sgui.splash import SplashScreen
from sgui.sgqt import *
from sgui.widgets.hardware_dialog import hardware_dialog
from .project import (
    check_project_version,
    clone_project,
    get_history,
    new_project,
    open_project,
    open_project_dialog,
    set_project,
    StargateProjectVersionError,
)
from sgui import project as project_mod
from .project_recovery import project_recover_dialog
from sglib.constants import UI_PIDFILE
from sglib.lib import util
from sglib.log import LOG
import os
import sys


class Welcome:
    def __init__(self, app, scaler):
        self.app = app
        self.scaler = scaler
        self.loaded = False

        self.widget = QWidget()
        self.widget.closeEvent = self._closeEvent
        self.widget.setObjectName('welcome_screen')
        self.widget.setWindowTitle("Stargate")
        self.widget.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        hlayout = QHBoxLayout(self.widget)
        rp_vlayout = QVBoxLayout()
        hlayout.addLayout(rp_vlayout)
        rp_vlayout.addWidget(QLabel("Recent Projects"))
        self.rp_list = QListWidget()
        self.rp_list.doubleClicked.connect(
            self.rp_doubleclick,
        )
        rp_vlayout.addWidget(self.rp_list)
        self.load_rp()
        buttons_vlayout = QVBoxLayout()
        hlayout.addLayout(buttons_vlayout)
        buttons_vlayout.addItem(
            QSpacerItem(10, 10, vPolicy=QSizePolicy.Policy.Expanding),
        )
        buttons_hlayout = QHBoxLayout()
        buttons_vlayout.addLayout(buttons_hlayout)
        new_button = QPushButton("New")
        new_button.setObjectName("huge_button")
        new_button.pressed.connect(self.on_new)
        buttons_hlayout.addWidget(new_button)

        open_button = QPushButton("Open")
        open_button.setObjectName("huge_button")
        open_button.pressed.connect(self.on_open)
        buttons_hlayout.addWidget(open_button)

        clone_button = QPushButton("Clone")
        clone_button.setObjectName("huge_button")
        clone_button.pressed.connect(self.on_clone)
        buttons_hlayout.addWidget(clone_button)

        buttons_hlayout2 = QHBoxLayout()
        buttons_vlayout.addLayout(buttons_hlayout2)

        hardware_button = QPushButton("Hardware\nSettings")
        hardware_button.setObjectName("huge_button")
        hardware_button.pressed.connect(self.on_hardware_settings)
        buttons_hlayout2.addWidget(hardware_button)

        project_recovery_button = QPushButton("Project\nRecovery")
        project_recovery_button.setObjectName("huge_button")
        project_recovery_button.pressed.connect(self.on_project_recovery)
        buttons_hlayout2.addWidget(project_recovery_button)

        self.widget.show()

    def _closeEvent(self, event):
        if not self.loaded:
            os.remove(UI_PIDFILE)
            sys.exit(0)

    def rp_doubleclick(self, index):
        project = str(self.rp_list.item(index.row()).text())
        try:
            check_project_version(self.widget, project)
        except StargateProjectVersionError:
            return
        set_project(project)
        self.close()

    def load_rp(self):
        """ Load a list of recent projects """
        self.history = get_history()
        if util.IS_WINDOWS:
            self.history = [
                x.replace('/', '\\')
                for x in self.history
            ]
        LOG.info(f"Project history: {self.history}")
        if self.history:
            self.rp_list.addItems(self.history)

    def close(self):
        self.loaded = True
        splash_screen = SplashScreen(self.scaler.y_res)
        # Because closing it makes the entire application exit, for some
        # reason
        self.widget.hide()
        main(
            splash_screen,
            self.scaler,
            project_mod.PROJECT_DIR,
        )

    def on_new(self):
        if new_project(self.widget):
            self.close()

    def on_open(self):
        if open_project(self.widget):
            self.close()

    def on_clone(self):
        if clone_project(self.widget):
            self.close()

    def on_hardware_settings(self):
        hardware = hardware_dialog(True)
        hardware.show_hardware_dialog(
            notify_of_restart=False,
        )

    def on_project_recovery(self):
        path, _ = open_project_dialog(self.widget)
        if path:
            project_recover_dialog(path)

