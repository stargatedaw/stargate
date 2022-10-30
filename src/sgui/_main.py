import os
import sys
import time

from sglib.log import LOG, setup_logging
from sgui import shared as glbl_shared
from sgui.main import main as main_window_open
from sgui import project as project_mod
from sgui.sgqt import QApplication, QGuiApplication, QtCore, QStackedWidget
from sgui.splash import SplashScreen
from sgui.util import setup_theme, ui_scaler_factory
from sgui.welcome import Welcome

class MainStackedWidget(QStackedWidget):
    def __init__(self, *args, **kwargs):
        QStackedWidget.__init__(self, *args, **kwargs)
        self.main_window = None
        self.welcome_window = None
        self.splash_screen = None

    def show_main(self):
        assert self.splash_screen, 'No splash screen'
        idx, splash_screen = self.splash_screen
        self.setCurrentIndex(idx)
        main_window = main_window_open(
            splash_screen,
            project_mod.PROJECT_DIR,
        )
        self.addWidget(main_window)
        idx = self.count() - 1
        self.main_window = (idx, main_window)
        self.setCurrentIndex(idx)

    def show_welcome(self):
        if not self.welcome_window:
            welcome = Welcome(QAPP)
            self.addWidget(welcome.widget)
            self.welcome_window = (self.count() - 1, welcome)
        idx, welcome_window = self.welcome_window
        self.setCurrentIndex(idx)

    def show_splash(self):
        if not self.splash_screen:
            splash_screen = SplashScreen()
            self.addWidget(splash_screen)
            self.splash_screen = (self.count() - 1, splash_screen)

def qt_message_handler(mode, context, message):
    line = (
        f'qt_message_handler: {mode} '
        f'{context.file}:{context.line}:{context.function}'
        f' "{message}"'
    )
    if mode == QtCore.QtMsgType.QtWarningMsg:
        LOG.warning(line)
    elif mode in (
        QtCore.QtMsgType.QtCriticalMsg,
        QtCore.QtMsgType.QtFatalMsg,
    ):
        LOG.error(line)
    else:
        LOG.info(line)

def _setup():
    setup_logging()
    LOG.info(f"sys.argv == {sys.argv}")
    QtCore.qInstallMessageHandler(qt_message_handler)
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
        )
    except Exception as ex:
        LOG.warning(
            "Unable to set "
            "QGuiApplication.setHighDpiScaleFactorRoundingPolicy"
            f" {ex}"
        )
    app = QApplication(sys.argv)
    setup_theme(app)
    return app

def main(args):
    global QAPP
    QAPP = _setup()
    QAPP.restoreOverrideCursor()
    from sglib.constants import UI_PIDFILE
    from sglib.lib.pidfile import check_pidfile, create_pidfile
    pid = check_pidfile(UI_PIDFILE)
    if pid is not None:
        from sgui.sgqt import QMessageBox
        msg = (
            f"Detected Stargate is already running with pid {pid}, "
            "please close the other instance first"
        )
        QMessageBox.warning(None, "Error", msg)
        LOG.error(msg)
        sys.exit(0)
    create_pidfile(UI_PIDFILE)
    glbl_shared.MAIN_STACKED_WIDGET = MainStackedWidget()
    glbl_shared.MAIN_STACKED_WIDGET.setMinimumSize(900, 700)
    glbl_shared.MAIN_STACKED_WIDGET.showMaximized()
    if args.project_file:
        glbl_shared.MAIN_STACKED_WIDGET.show_splash()
        glbl_shared.MAIN_STACKED_WIDGET.show_main()
    else:
        glbl_shared.MAIN_STACKED_WIDGET.show_welcome()
    exit_code = QAPP.exec()
    time.sleep(0.3)
    from sgui import main
    main.flush_events()
    if getattr(main, 'RESPAWN', None):
        main.respawn()
    LOG.info("Calling os._exit()")
    os.remove(UI_PIDFILE)
    # Work around PyQt SEGFAULT-on-exit issues
    os._exit(exit_code)

