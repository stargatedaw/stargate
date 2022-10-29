import os
import sys
import time

from sgui import shared as glbl_shared


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
    global LOG, QtCore, QApplication
    from sglib.log import LOG, setup_logging
    setup_logging()
    LOG.info(f"sys.argv == {sys.argv}")
    from sgui.sgqt import QApplication, QGuiApplication, QtCore
    QtCore.qInstallMessageHandler(qt_message_handler)
    from sgui.util import setup_theme
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
    scaler = setup_theme(app)
    return app, scaler

def main(args):
    global QAPP, WELCOME
    QAPP, scaler = _setup()
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
    from sgui.sgqt import QStackedWidget
    glbl_shared.MAIN_STACKED_WIDGET = QStackedWidget()
    glbl_shared.MAIN_STACKED_WIDGET.setMinimumSize(900, 700)
    glbl_shared.MAIN_STACKED_WIDGET.showMaximized()
    if args.project_file:
        from sgui.splash import SplashScreen
        splash_screen = SplashScreen(scaler.y_res)
        glbl_shared.MAIN_STACKED_WIDGET.addWidget(splash_screen)
        from sgui.main import main
        main(
            splash_screen,
            scaler,
            args.project_file,
        )
    else:
        from sgui.welcome import Welcome
        WELCOME = Welcome(QAPP, scaler)
        glbl_shared.MAIN_STACKED_WIDGET.addWidget(WELCOME.widget)
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

