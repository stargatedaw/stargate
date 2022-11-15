from .updates import ui_check_updates
from sgui.main import main
from sgui.sgqt import *
from sgui.widgets.hardware_dialog import HardwareDialog
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
from sgui import shared as glbl_shared
from sgui.util import ui_scaler_factory
from .project_recovery import project_recover_dialog
from sglib.constants import UI_PIDFILE
from sglib.lib import util
from sglib.log import LOG
import os
import sys


class Welcome(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.scaler = ui_scaler_factory()
        self.loaded = False

        self.widget = QWidget()
        self.widget.setObjectName('welcome_screen')
        self.widget.setWindowTitle("Stargate")
        self.widget.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        hlayout = QHBoxLayout(self.widget)
        rp_vlayout = QVBoxLayout()
        hlayout.addLayout(rp_vlayout)
        rp_label = QLabel("Recent Projects")
        rp_label.setObjectName('welcome_screen')
        rp_vlayout.addWidget(rp_label)
        self.rp_list = QListWidget()
        self.rp_list.doubleClicked.connect(
            lambda x: self.rp_doubleclick(x.row()),
        )
        rp_vlayout.addWidget(self.rp_list)
        self.rp_list.installEventFilter(self)
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

        updates_button = QPushButton('Check for updates')
        updates_button.setObjectName("huge_button")
        updates_button.pressed.connect(ui_check_updates)
        buttons_vlayout.addWidget(updates_button)

    def rp_doubleclick(self, index):
        project = str(self.rp_list.item(index).text())
        try:
            check_project_version(self.widget, project)
        except StargateProjectVersionError:
            return
        set_project(project)
        self.close()

    def eventFilter(self, watched, event):
        if (
            event.type() == QtCore.QEvent.Type.KeyPress
            and
            event.matches(QKeySequence.StandardKey.InsertParagraphSeparator)
        ):
            i = self.rp_list.currentRow()
            self.rp_doubleclick(i)
            return True
        return False

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
            self.rp_list.setCurrentRow(0)

    def close(self):
        self.loaded = True
        if glbl_shared.MAIN_STACKED_WIDGET.show_splash():
            glbl_shared.MAIN_STACKED_WIDGET.show_main()

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
        _main = glbl_shared.MAIN_STACKED_WIDGET
        _main.show_hardware_dialog(
            _main.show_welcome,
            _main.show_welcome,
        )

    def on_project_recovery(self):
        path, _ = open_project_dialog(self.widget)
        if path:
            project_recover_dialog(path)

