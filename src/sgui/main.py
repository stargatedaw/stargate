#!/usr/bin/python3
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""
from . import shared
from .updates import ui_check_updates
from sglib.models import stargate as sg_project
from sglib.models import theme
from sglib.ipc import *
from sglib.lib import util
from sglib.lib.process import run_process
from sglib.lib.util import *
from sglib.lib.translate import _
from sglib.lib.appimage import *
from sglib.log import LOG
from sglib.lib.pidfile import create_pidfile
from sglib import constants
from sglib.math import clip_value, db_to_lin
from sgui import widgets
from sgui.daw import entrypoint as daw
from sgui.daw.item_editor.audio._shared import (
    remove_path_from_painter_path_cache,
)
from sgui.ipc.socket import SocketIPCServer, SocketIPCTransport
from sgui.plugins import SgPluginUiDict
from sgui.transport import TransportWidget
from sglib.lib import engine
from sglib.lib.engine import *
from sglib.lib import strings as sg_strings
from sgui.project import (
    check_project_version,
    new_project,
    open_project,
    set_project,
    StargateProjectVersionError,
)
from sgui.util import (
    check_for_empty_directory,
    check_for_rw_perms,
    get_font,
    get_fps,
    log_screen_info,
    set_font,
    show_generic_exception,
    svg_to_pixmap,
    ui_scaler_factory,
)
from sgui import sgqt
from sgui.sgqt import *
from sgui.widgets.file_browser import open_bookmarks
import gc
import os
import subprocess
import sys
import time


HOST_INDEX_DAW = 0
HOST_INDEX_WAVE_EDIT = 1

PROJECT_FILE = None


def handle_engine_error(exit_code):
    if exit_code == 0:
        LOG.info("Audio engine stopped with exit code 0, no errors.")
        return

    if exit_code == 1000:
        msg = "Audio device not found"
    elif exit_code == 1001:
        msg = "Device config not found"
    elif exit_code == 1002:
        msg = "Unknown error opening audio device"
    if exit_code == 1003:
        msg = (
            "The audio device was busy, make sure that no other applications "
            "are using the device and try restarting Stargate"
        )
    else:
        msg = (
            f"The audio engine stopped with exit code {exit_code}, "
             "please try restarting Stargate"
        )
        shared.TRANSPORT.stop_button.setChecked(True)

    LOG.error(msg)
    QMessageBox.warning(
        shared.MAIN_WINDOW,
        "Error",
        msg,
    )
    if exit_code >= 1000 and exit_code <= 1002:
        shared.MAIN_WINDOW.on_change_audio_settings()

def engine_lib_callback(a_path, a_msg):
    MAIN_WINDOW.engine_lib_callback(a_path, a_msg)


class SgMainWindow(QWidget):
    MIDI_NOTES = {
        "q": 0,
        "w": 1,
        "e": 2,
        "r": 3,
        "t": 4,
        "y": 5,
        "u": 6,
        "i": 7,
        "o": 8,
        "p": 9,
        "[": 10,
        "]": 11,
    }
    daw_callback = Signal(str)
    wave_edit_callback = Signal(str)
    engine_mon_callback = Signal(str)

    def __init__(self):
        super().__init__()

    def setup(self, scaler):
        self.suppress_resize_events = False
        shared.MAIN_WINDOW = self
        constants.IPC_TRANSPORT = SocketIPCTransport()
        with_audio = constants.IPC_TRANSPORT is not None
        constants.IPC = StargateIPC(
            constants.IPC_TRANSPORT,
            with_audio,
        )
        constants.DAW_IPC = DawIPC(
            constants.IPC_TRANSPORT,
            with_audio,
        )
        constants.WAVE_EDIT_IPC = WaveEditIPC(
            constants.IPC_TRANSPORT,
            with_audio,
        )
        shared.TRANSPORT = TransportWidget(scaler)
        self.setObjectName("plugin_ui")
        self.setMinimumSize(900, 600)
        self.last_ac_dir = util.HOME
        self.setObjectName("plugin_ui")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.transport_splitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.transport_splitter)

        self.transport_widget = QWidget()
        self.transport_widget.setMaximumHeight(51)
        self.transport_widget.setObjectName('transport_panel')
        self.transport_hlayout = QHBoxLayout(self.transport_widget)
        self.transport_hlayout.setContentsMargins(2, 2, 2, 2)
        self.transport_splitter.addWidget(self.transport_widget)
        self.transport_widget.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum,
        )

        self.transport_hlayout.addWidget(
            shared.TRANSPORT.group_box,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft,
        )
        self.transport_stack = QStackedWidget()
        self.transport_hlayout.addWidget(
            self.transport_stack,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft,
        )
        self.transport_hlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
            ),
        )
        if shared.HIDE_HINT_BOX:
            sgqt.HINT_BOX.hide()
        self.transport_hlayout.addWidget(sgqt.HINT_BOX)
        sgqt.HINT_BOX.setFixedHeight(50)
        sgqt.HINT_BOX.setFixedWidth(510)

        self.main_stack = QStackedWidget()
        self.transport_splitter.addWidget(self.main_stack)

        SPLASH_SCREEN.status_update(_("Loading DAW"))
        daw.init()
        SPLASH_SCREEN.status_update(_("Loading Wave Editor"))
        from sgui import wave_edit
        wave_edit.init()

        self.wave_editor_module = wave_edit

        shared.HOST_MODULES = (daw, wave_edit)
        self.host_windows = tuple(x.MAIN_WINDOW for x in shared.HOST_MODULES)

        self.current_module = daw
        self.current_window = daw.MAIN_WINDOW

        self.engine_mon_callback.connect(
            daw.MAIN_WINDOW.engine_mon_label.setText
        )
        self.engine_mon_callback.connect(
            wave_edit.MAIN_WINDOW.engine_mon_label.setText
        )

        for f_module in shared.HOST_MODULES:
            self.transport_stack.addWidget(f_module.TRANSPORT.group_box)

        for f_window in self.host_windows:
            self.main_stack.addWidget(f_window)

        shared.IGNORE_CLOSE_EVENT = True

        self.menu_bar = QMenu(shared.TRANSPORT.menu_button)

        shared.TRANSPORT.menu_button.setMenu(self.menu_bar)
        self.menu_file = self.menu_bar.addMenu(_("File"))

        self.new_action = QAction(_("New..."), self.menu_file)
        self.menu_file.addAction(self.new_action)
        self.new_action.setToolTip(
            'Create a new project and open it'
        )
        self.new_action.triggered.connect(self.on_new)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)

        self.open_action = QAction(_("Open..."), self.menu_file)
        self.menu_file.addAction(self.open_action)
        self.open_action.setToolTip(
            'Open another project, closing this project'
        )
        self.open_action.triggered.connect(self.on_open)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)

        self.close_action = QAction(_("Close Project..."), self.menu_file)
        self.menu_file.addAction(self.close_action)
        self.close_action.setToolTip(
            'Close this project, return to the welcome screen to configure '
            'hardware settings, recover projects or create/open another '
            'project'
        )
        self.close_action.triggered.connect(self.on_close)

        self.save_action = QAction("Save", self.menu_file)
        self.menu_file.addAction(self.save_action)
        self.save_action.setToolTip(
            "Projects are automatically saved everytime you change anything, "
            "this creates a timestamped backup that you can revert to later"
        )
        self.save_action.triggered.connect(self.on_save)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)

        self.save_as_action = QAction("Save As...", self.menu_file)
        self.menu_file.addAction(self.save_as_action)
        self.save_as_action.setToolTip(
            "Projects are automatically saved everytime you change anything, "
            "this creates a named backup that you can revert to later"
        )
        self.save_as_action.triggered.connect(self.on_save_as)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)

        self.menu_file.addSeparator()

        self.offline_render_action = QAction("Render...", self.menu_file)
        self.menu_file.addAction(self.offline_render_action)
        self.offline_render_action.setToolTip(
            'Convert this project to an audio file.  Set the region markers '
            'by right clicking on the sequencer timeline, or set the '
            'start/end markers in the wave editor'
        )
        self.offline_render_action.triggered.connect(self.on_offline_render)

        self.audio_device_action = QAction(
            "Hardware Settings...",
            self.menu_file,
        )
        self.menu_file.addAction(self.audio_device_action)
        self.audio_device_action.setToolTip(
            'Open the hardware settings dialog to change audio or MIDI '
            'device settings'
        )
        self.audio_device_action.triggered.connect(
            self.on_change_audio_settings)
        self.menu_file.addSeparator()

        self.quit_action = QAction("Quit", self.menu_file)
        self.menu_file.addAction(self.quit_action)
        self.quit_action.setToolTip('Exit the application')
        self.quit_action.triggered.connect(shared.MAIN_STACKED_WIDGET.close)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)

        #self.menu_edit = self.menu_bar.addMenu(_("Edit"))

        #self.undo_action = self.menu_edit.addAction(_("Undo"))
        #self.undo_action.triggered.connect(self.on_undo)
        #self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)

        #self.redo_action = self.menu_edit.addAction(_("Redo"))
        #self.redo_action.triggered.connect(self.on_redo)
        #self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)

        self.menu_appearance = self.menu_bar.addMenu(_("Appearance"))

        self.collapse_splitters_action = QAction(
            _("Toggle Collapse Transport"),
            self.menu_appearance,
        )
        self.menu_appearance.addAction(self.collapse_splitters_action)
        self.collapse_splitters_action.setToolTip(
            'Toggle collapsing the transport, create more room for the '
            'sequencer or wave editor'
        )
        self.collapse_splitters_action.triggered.connect(
            self.on_collapse_splitters,
        )
        self.collapse_splitters_action.setShortcut(QKeySequence("CTRL+Up"))

        self.menu_appearance.addSeparator()

        self.full_screen_action = QAction(
            'Toggle Full Screen',
            self.menu_appearance,
        )
        self.menu_appearance.addAction(self.full_screen_action)
        self.full_screen_action.setToolTip(
            'Toggle between full screen mode and normal mode'
        )
        self.full_screen_action.triggered.connect(
            shared.MAIN_STACKED_WIDGET.toggle_full_screen
        )
        self.full_screen_action.setShortcut(QKeySequence("ALT+F12"))

        self.menu_appearance.addSeparator()

        self.open_theme_action = QAction("Open Theme...", self.menu_appearance)
        self.menu_appearance.addAction(self.open_theme_action)
        self.open_theme_action.setToolTip(
            'Open a new sgtheme file to change the appearance of Stargate.  '
            'There are several factory themes, or create your own'
        )
        self.open_theme_action.triggered.connect(self.on_open_theme)

        self.default_theme_action = QAction(
            "Use Default Theme",
            self.menu_appearance,
        )
        self.menu_appearance.addAction(self.default_theme_action)
        self.default_theme_action.setToolTip(
            'Use the default theme, replacing any other theme you have used'
        )
        self.default_theme_action.triggered.connect(
            self.on_use_default_theme,
        )

        self.copy_theme_action = QAction(
            _("Copy Theme to New Theme..."),
            self.menu_appearance,
        )
        self.menu_appearance.addAction(self.copy_theme_action)
        self.copy_theme_action.setToolTip(
            'Create a copy of the current theme that you can customize and '
            'create your own theme from'
        )
        self.copy_theme_action.triggered.connect(self.on_copy_theme)

        self.menu_appearance.addSeparator()

        self.custom_font_action = QAction(
            _("Choose custom font..."),
            self.menu_appearance,
        )
        self.menu_appearance.addAction(self.custom_font_action)
        self.custom_font_action.setToolTip(
            'Choose a custom font for Stargate'
        )
        self.custom_font_action.triggered.connect(self.on_custom_font)

        self.clear_custom_font_action = QAction(
            _("Use default font"),
            self.menu_appearance,
        )
        self.menu_appearance.addAction(self.clear_custom_font_action)
        self.clear_custom_font_action.setToolTip(
            'Use the default font included with Stargate'
        )
        self.clear_custom_font_action.triggered.connect(
            self.on_clear_custom_font,
        )

        if not util.IS_WINDOWS:
            self.menu_tools = self.menu_bar.addMenu(_("Tools"))

            self.mp3_action = QAction(_("MP3 Converter..."), self.menu_tools)
            self.menu_tools.addAction(self.mp3_action)
            self.mp3_action.setToolTip(
                'Open a dialog to convert MP3 files to and from .wav files'
            )
            self.mp3_action.triggered.connect(self.mp3_converter_dialog)

            self.ogg_action = QAction(_("Ogg Converter..."), self.menu_tools)
            self.menu_tools.addAction(self.ogg_action)
            self.ogg_action.setToolTip(
                'Open a dialog to convert OGG files to and from .wav files'
            )
            self.ogg_action.triggered.connect(self.ogg_converter_dialog)

        self.menu_help = self.menu_bar.addMenu(_("Help"))

        self.youtube_action = self.menu_help.addAction(
            _("Watch Tutorial Videos on Youtube..."),
        )
        self.youtube_action.triggered.connect(self.on_youtube)
        self.manual_action = self.menu_help.addAction(
            _("View User Manual on Github..."),
        )
        self.manual_action.triggered.connect(self.on_manual)

        self.sfzinstruments_action = self.menu_help.addAction(
            _("Download SFZ instruments for Sampler1"),
        )
        self.sfzinstruments_action.triggered.connect(self.on_sfzinstruments)
        self.samplepack_action = self.menu_help.addAction(
            _("Download the official Stargate DAW sample pack"),
        )
        self.samplepack_action.triggered.connect(self.on_samplepack)

        self.version_action = self.menu_help.addAction(_("Version Info..."))
        self.version_action.triggered.connect(self.on_version)

        self.menu_bar.addSeparator()
        self.menu_devel = self.menu_bar.addMenu(_("Developer"))
        self.menu_devel_copy = self.menu_devel.addMenu(
            _("Copy to clipboard..."),
        )
        self.copy_gdb_cmd_action = self.menu_devel_copy.addAction(
            _("GDB run command"),
        )
        self.copy_gdb_cmd_action.triggered.connect(self.copy_gdb_run_cmd)
        self.copy_valgrind_cmd_action = self.menu_devel_copy.addAction(
            _("Valgrind command"),
        )
        self.copy_valgrind_cmd_action.triggered.connect(
            self.copy_valgrind_cmd,
        )

        self.menu_bar.addSeparator()

        self.check_updates_action = QAction(
            'Check for updates...',
            self.menu_bar,
        )
        self.menu_bar.addAction(self.check_updates_action)
        self.check_updates_action.setToolTip(
            'Check to see if you are running the latest version of '
            'Stargate DAW'
        )
        self.check_updates_action.triggered.connect(ui_check_updates)

        self.tooltips_action = QAction(_("Hide Hint Box"), self.menu_bar)
        self.tooltips_action.setToolTip(
            'Toggle hiding the hint box in the upper right corner of the '
            'screen'
        )
        self.menu_bar.addAction(self.tooltips_action)
        self.tooltips_action.setCheckable(True)
        self.tooltips_action.setChecked(shared.HIDE_HINT_BOX)
        self.tooltips_action.triggered.connect(self.set_tooltips_enabled)

        if all(x in os.environ for x in ('APPIMAGE', 'APPDIR')):
            self.appimage_install_action = QAction(
                "Install AppImage to start menu",
                self.menu_bar,
            )
            self.appimage_install_action.setToolTip(
                'Install a start menu shortcut for your user account. You '
                'must run this again if you move the AppImage, and again '
                'every time you download a new version of the AppImage'
            )
            self.appimage_install_action.triggered.connect(
                self.appimage_install,
            )

            self.appimage_uninstall_action = QAction(
                "Uninstall AppImage from the start menu",
                self.menu_bar,
            )
            self.appimage_uninstall_action.setToolTip(
                'Uninstall Stargate DAW AppImage from the start menu.  '
                'This will not uninstall a start menu shortcut installed '
                'by other packages'
            )
            self.appimage_uninstall_action.triggered.connect(
                self.appimage_uninstall,
            )

            desktop_dir, desktop_path = appimage_start_menu_path()
            if os.path.exists(desktop_path):
                self.menu_bar.addAction(self.appimage_uninstall_action)
            else:
                self.menu_bar.addAction(self.appimage_install_action)

        self.spacebar_action = QAction(self)
        self.addAction(self.spacebar_action)
        self.spacebar_action.triggered.connect(self.on_spacebar)
        self.spacebar_action.setShortcut(
            QKeySequence(QtCore.Qt.Key.Key_Space),
        )

        self.subprocess_timer = None
        self.socket_server = None

        self.socket_server = SocketIPCServer(
            daw.MAIN_WINDOW.configure_callback,
            wave_edit.MAIN_WINDOW.configure_callback,
        )
        self.socket_server.start()

        if util.WITH_AUDIO:
            self.subprocess_timer = QtCore.QTimer(self)
            self.subprocess_timer.timeout.connect(self.subprocess_monitor)
            self.subprocess_timer.setSingleShot(False)
            self.subprocess_timer.start(1000)

        self.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        self.on_collapse_splitters(a_restore=True)

    def appimage_install(self):
        appimage_start_menu_install()
        self.menu_bar.removeAction(
            self.appimage_install_action,
        )
        self.menu_bar.addAction(
            self.appimage_uninstall_action,
        )
        QMessageBox.information(None, 'Success!', 'Added start menu shortcut')

    def appimage_uninstall(self):
        desktop_dir, desktop_path = appimage_start_menu_path()
        os.remove(desktop_path)
        self.menu_bar.removeAction(
            self.appimage_uninstall_action,
        )
        self.menu_bar.addAction(
            self.appimage_install_action,
        )
        QMessageBox.information(
            None,
            'Success!',
            'Removed start menu shortcut',
        )

    def set_tooltips_enabled(self):
        hidden = self.tooltips_action.isChecked()
        if hidden:
            sgqt.HINT_BOX.hide()
        else:
            sgqt.HINT_BOX.show()
        util.set_file_setting("hide-hint-box", 1 if hidden else 0)

    def _key_event(self, ev, press):
        super().keyPressEvent(ev)
        if shared.IS_PLAYING or shared.IS_RECORDING:
            return
        try:
            host = shared.TRANSPORT.current_host()
            key = str(ev.text())
            if host == HOST_INDEX_DAW and key in self.MIDI_NOTES:
                rack = daw.shared.PLUGIN_RACK.rack_index()
                note_offset = daw.shared.PLUGIN_RACK.octave() * 12
                channel = daw.shared.PLUGIN_RACK.midi_channel()
                note = self.MIDI_NOTES[key] + note_offset
                assert note >= 0 and note <= 120, note
                if press:
                    constants.DAW_IPC.note_on(rack, note, channel)
                else:
                    constants.DAW_IPC.note_off(rack, note, channel)
        except Exception as ex:
            LOG.exception(ex)

    def keyPressEvent(self, ev):
        self._key_event(ev, True)

    def keyReleaseEvent(self, ev):
        self._key_event(ev, False)

    def on_custom_font(self):
        font = get_font()
        font.choose_font()

    def on_clear_custom_font(self):
        font = get_font()
        font.clear_font()

    def _copy_to_clipboard(self, text):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(text, mode=cb.Mode.Clipboard)

    def copy_gdb_run_cmd(self):
        text = "run '{}' '{}' {} 0 30 1 --sleep".format(
            util.INSTALL_PREFIX,
            constants.PROJECT_DIR,
            os.getpid(),
        )
        self._copy_to_clipboard(text)

    def copy_valgrind_cmd(self):
        text = (
            "valgrind '{}-dbg' '{}' '{}' {} 0 1 1 "
            "--no-hardware --single-thread"
        ).format(
            util.BIN_PATH,
            util.INSTALL_PREFIX,
            constants.PROJECT_DIR,
            os.getpid(),
        )
        self._copy_to_clipboard(text)

    def on_samplepack(self):
        url = QtCore.QUrl(
            "https://github.com/stargatedaw/stargate-sample-pack",
        )
        QDesktopServices.openUrl(url)

    def on_sfzinstruments(self):
        url = QtCore.QUrl(
            "https://github.com/sfzinstruments",
        )
        QDesktopServices.openUrl(url)

    def on_youtube(self):
        url = QtCore.QUrl(
            "https://www.youtube.com/channel/UC0xYkPBN3cqMMaTQxc38Rfw",
        )
        QDesktopServices.openUrl(url)

    def on_manual(self):
        url = QtCore.QUrl(
            "https://github.com/stargatedaw/stargate/"
            "tree/main/docs/UserManual",
        )
        QDesktopServices.openUrl(url)

    def engine_lib_callback(self, a_path, a_msg):
        f_path = a_path.decode("utf-8")
        f_msg = a_msg.decode("utf-8")
        self.engine_callback_dict[f_path].emit(f_msg)

    def resizeEvent(self, a_event):
        if self.suppress_resize_events:
            return
        super().resizeEvent(a_event)

    def open_in_wave_editor(self, a_file):
        shared.TRANSPORT.host_combobox.setCurrentIndex(HOST_INDEX_WAVE_EDIT)
        self.main_stack.repaint()
        self.wave_editor_module.WAVE_EDITOR.open_file(a_file)
        #self.wave_editor_module.WAVE_EDITOR.sample_graph.repaint()

    def set_host(self, a_index):
        self.transport_stack.setCurrentIndex(a_index)
        self.main_stack.setCurrentIndex(a_index)
        self.current_module = shared.HOST_MODULES[a_index]
        self.current_window = self.host_windows[a_index]
        shared.CURRENT_HOST = a_index
        constants.IPC.set_host(a_index)
        self.current_module.TRANSPORT.set_time()

    def show_offline_rendering_wait_window_v2(
        self,
        a_cmd_list,
        a_file_name,
        f_file_name=None
    ):
        if not f_file_name:
            f_file_name = "{}.finished".format(a_file_name)

        def ok_handler():
            if os.path.isfile(a_file_name):
                constants.PROJECT.reload_audio_file(a_file_name)
                remove_path_from_painter_path_cache(a_file_name)
            f_window.close()

        def cancel_handler():
            f_timer.stop()
            try:
                f_proc.kill()
            except Exception as ex:
                LOG.error(
                    f"Exception while killing render process\n{ex}",
                )
                LOG.exception(ex)
            if os.path.isfile(a_file_name):
                os.remove(a_file_name)
            if os.path.isfile(f_file_name):
                os.remove(f_file_name)
            f_window.close()

        def timeout_handler():
            if f_proc.poll() is not None:
                f_timer.stop()
                f_ok.setEnabled(True)
                f_cancel.setEnabled(False)
                f_time_label.setText(
                    _("Finished in:"),
                )
                if os.path.isfile(f_file_name):
                    # Some times this does not exist, not sure why
                    os.remove(f_file_name)
                f_proc.communicate()[0]
                #f_output = f_proc.communicate()[0]
                #LOG.info(f_output)
                exit_code = f_proc.returncode
                if exit_code != 0:
                    f_window.close()
                    QMessageBox.warning(
                        self,
                        _("Error"),
                        _(f"Render exited with code {exit_code}"),
                    )
            else:
                f_elapsed_time = time.time() - f_start_time
                clock.display(str(round(f_elapsed_time, 1)))

        f_proc = run_process(a_cmd_list)
        f_start_time = time.time()
        f_window = QDialog(
            MAIN_WINDOW,
            (
                QtCore.Qt.WindowType.WindowTitleHint
                |
                QtCore.Qt.WindowType.FramelessWindowHint
            ),
        )
        f_window.setWindowTitle(_("Rendering to .wav, please wait"))
        f_window.setMinimumSize(360, 180)
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_time_label = QLabel("Elapsed Time:")
        f_time_label.setMinimumWidth(360)
        f_layout.addWidget(f_time_label)
        clock = QLCDNumber()
        clock.setDigitCount(7)
        clock.setMinimumWidth(210)
        clock.display("0:00.0")
        f_layout.addWidget(clock)
        f_timer = QtCore.QTimer()
        f_timer.timeout.connect(timeout_handler)

        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok = QPushButton(_("OK"))
        f_ok.setMinimumWidth(75)
        f_ok.pressed.connect(ok_handler)
        f_ok.setEnabled(False)
        f_ok_cancel_layout.addWidget(f_ok)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.setMinimumWidth(75)
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_timer.start(20)
        f_window.exec()

    def subprocess_monitor(self):
        try:
            if engine.ENGINE_PSUTIL:
                cpu = round(engine.ENGINE_PSUTIL.cpu_percent(), 1)
                mem = round(engine.ENGINE_PSUTIL.memory_percent(), 1)
                text = f'CPU: {cpu}% RAM: {mem}%'
                self.engine_mon_callback.emit(text)
        except:
            pass
        try:
            if (
                engine.ENGINE_SUBPROCESS
                and
                engine.ENGINE_SUBPROCESS.poll() is not None
            ):
                self.subprocess_timer.stop()
                exitCode = engine.ENGINE_SUBPROCESS.returncode
                handle_engine_error(exitCode)
        except Exception as ex:
            LOG.error("subprocess_monitor: {}".format(ex))
            LOG.exception(ex)

    def on_new(self):
        if shared.IS_PLAYING:
            return
        if new_project(self):
            self.prepare_to_quit()
            shared.MAIN_STACKED_WIDGET.start()

    def on_open(self):
        if shared.IS_PLAYING:
            return
        if open_project(self):
            self.prepare_to_quit()
            shared.MAIN_STACKED_WIDGET.start()

    def on_close(self):
        if shared.IS_PLAYING:
            return
        answer = QMessageBox.question(
            shared.MAIN_STACKED_WIDGET,
            _("Warning"),
            _("Close this project and return to the welcome screen?"),
            (
                QMessageBox.StandardButton.Yes
                |
                QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return
        self.prepare_to_quit()
        shared.MAIN_STACKED_WIDGET.show_welcome()

    def on_save(self):
        shared.PLUGIN_UI_DICT.save_all_plugin_state()
        constants.PROJECT.create_backup()

    def on_save_as(self):
        if shared.IS_PLAYING:
            return
        def ok_handler():
            f_name = str(f_lineedit.text()).strip()
            f_name = f_name.replace("/", "")
            if f_name:
                shared.PLUGIN_UI_DICT.save_all_plugin_state()
                if constants.PROJECT.create_backup(f_name):
                    f_window.close()
                else:
                    QMessageBox.warning(
                        self,
                        _("Error"),
                        _(
                            "This name already exists, please choose "
                            "another name"
                        ),
                    )

        f_window = QDialog(parent=MAIN_WINDOW)
        f_window.setWindowTitle(_("Save As..."))
        f_layout = QVBoxLayout(f_window)
        f_lineedit = QLineEdit()
        f_lineedit.setToolTip(
            'A descriptive name for this backup, you will be able to select '
            'it from the project recovery window in the welcome screen'
        )
        f_lineedit.setMinimumWidth(240)
        f_lineedit.setMaxLength(48)
        f_layout.addWidget(f_lineedit)
        f_ok_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_layout)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_layout.addWidget(f_cancel_button)
        f_cancel_button.pressed.connect(f_window.close)
        f_window.exec()

    def prepare_to_quit(self):
        try:
            self.setUpdatesEnabled(False)
            close_engine()
            shared.PLUGIN_UI_DICT.close_all_plugin_windows()
            if self.socket_server is not None:
                self.socket_server.free()
            for f_host in self.host_windows:
                f_host.prepare_to_quit()
                self.main_stack.removeWidget(f_host)
                f_host.setParent(None)

            for f_module in shared.HOST_MODULES:
                self.transport_stack.removeWidget(
                    f_module.TRANSPORT.group_box,
                )
                f_module.TRANSPORT.group_box.setParent(None)

            shared.IGNORE_CLOSE_EVENT = False
            if self.subprocess_timer:
                self.subprocess_timer.stop()
            shared.prepare_to_quit()
        except Exception as ex:
            LOG.error(
                "Exception thrown while attempting to exit, "
                "forcing Stargate to exit"
            )
            LOG.exception(ex)
            exit(999)

    def on_change_audio_settings(self):
        def callback():
            shared.MAIN_STACKED_WIDGET.start()

        self.prepare_to_quit()
        shared.MAIN_STACKED_WIDGET.show_hardware_dialog(callback, callback)

    def on_use_default_theme(self):
        util.clear_file_setting("default-style")
        QMessageBox.warning(
            MAIN_WINDOW,
            _("Theme Applied..."),
            _("Changed theme.  Please restart the application")
        )

    def on_copy_theme(self):
        try:
            path, _filter = QFileDialog.getSaveFileName(
                MAIN_WINDOW,
                _("Copy a theme directory"),
                util.THEMES_DIR,
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if path and str(path):
                path = str(path)
                if os.path.exists(path):
                    QMessageBox.warning(
                        MAIN_WINDOW,
                        _("Error"),
                        _(f"{path} already exists"),
                    )
                    return
                theme.copy_theme(path)
        except Exception as ex:
            LOG.exception(ex)
            show_generic_exception(ex)


    def on_open_theme(self):
        try:
            f_file, f_filter = QFileDialog.getOpenFileName(
                MAIN_WINDOW,
                _("Open a theme file"),
                util.THEMES_DIR,
                "Stargate Theme (*.sgtheme)",
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if f_file and str(f_file):
                f_file = str(f_file)
                scaler = ui_scaler_factory()
                font_size, font_unit = get_font().get_font_size()
                try:
                    theme.set_theme(f_file, scaler, font_size, font_unit)
                except Exception as ex:
                    show_generic_exception(
                        ex,
                        _("Could not load the theme"),
                    )
                    return
                QMessageBox.warning(
                    MAIN_WINDOW,
                    _("Theme Applied..."),
                    _("Changed theme.  Please restart the application")
                )
        except Exception as ex:
            show_generic_exception(ex)

    def on_version(self):
        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Version Info"))
        f_window.setFixedSize(420, 150)
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_minor_version = util.META_DOT_JSON['version']['minor']
        f_version = QLabel(
            f"{constants.MAJOR_VERSION}-{f_minor_version}",
        )
        f_version.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse,
        )
        f_layout.addWidget(f_version)
        f_ok_button = QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(f_window.close)
        f_window.exec()

    def on_spacebar(self):
        shared.TRANSPORT.on_spacebar()

    def on_collapse_splitters(self, a_restore=False):
        if a_restore or not self.transport_splitter.sizes()[0]:
            self.transport_splitter.setSizes([100, 9999])
        else:
            self.transport_splitter.setSizes([0, 9999])

    def mp3_converter_dialog(self):
        if which("avconv"):
            f_enc = "avconv"
        elif which("ffmpeg"):
            f_enc = "ffmpeg"
        else:
            f_enc = "avconv"

        f_lame = "lame"
        for f_app in (f_enc, f_lame):
            if which(f_app) is None:
                QMessageBox.warning(self, _("Error"),
                    sg_strings.avconv_error.format(f_app))
                return
        self.audio_converter_dialog("lame", f_enc, "mp3")

    def ogg_converter_dialog(self):
        if which("oggenc") is None or which("oggdec") is None:
            QMessageBox.warning(
                self,
                _("Error"),
                _("Error, vorbis-tools are not installed"),
            )
            return
        self.audio_converter_dialog("oggenc", "oggdec", "ogg")

    def audio_converter_dialog(self, a_enc, a_dec, a_label):
        def get_cmd(f_input_file, f_output_file):
            if f_wav_radiobutton.isChecked():
                if a_dec == "avconv" or a_dec == "ffmpeg":
                    f_cmd = [
                        which(a_dec),
                        "-i",
                        f_input_file,
                        f_output_file,
                    ]
                elif a_dec == "oggdec":
                    f_cmd = [
                        which(a_dec),
                        "--output",
                        f_output_file,
                        f_input_file,
                    ]
            else:
                if a_enc == "oggenc":
                    f_quality = float(str(f_mp3_br_combobox.currentText()))
                    f_quality = (320.0 / f_quality) * 10.0
                    f_quality = clip_value(f_quality, 3.0, 10.0)
                    f_cmd = [
                        which(a_enc),
                        "-q",
                        str(f_quality),
                        "-o",
                        f_output_file,
                        f_input_file,
                    ]
                elif a_enc == "lame":
                    f_cmd = [
                        which(a_enc),
                        "-b",
                        str(f_mp3_br_combobox.currentText()),
                        f_input_file,
                        f_output_file,
                    ]
            LOG.info(f_cmd)
            return f_cmd

        def ok_handler():
            f_input_file = str(f_name.text())
            f_output_file = str(f_output_name.text())
            if not f_input_file or not f_output_file:
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _("File names cannot be empty"),
                )
                return
            if f_batch_checkbox.isChecked():
                if f_wav_radiobutton.isChecked():
                    f_ext = ".{}".format(a_label)
                else:
                    f_ext = ".wav"
                f_ext = f_ext.upper()
                f_list = [x for x in os.listdir(f_input_file)
                    if x.upper().endswith(f_ext)]
                if not f_list:
                    QMessageBox.warning(
                        f_window,
                        _("Error"),
                        _("No {} files in {}".format(f_ext, f_input_file))
                    )
                    return
                f_proc_list = []
                for f_file in f_list:
                    f_in = os.path.join(f_input_file, f_file)
                    f_out = os.path.join(
                        f_output_file,
                        "{}{}".format(
                            f_file.rsplit(".", 1)[0],
                            self.ac_ext,
                        ),
                    )
                    f_cmd = get_cmd(f_in, f_out)
                    f_proc = subprocess.Popen(f_cmd)
                    f_proc_list.append((f_proc, f_out))
                for f_proc, f_out in f_proc_list:
                    f_status_label.setText(f_out)
                    QApplication.processEvents()
                    f_proc.communicate()
            else:
                f_cmd = get_cmd(f_input_file, f_output_file)
                f_proc = subprocess.Popen(f_cmd)
                f_proc.communicate()
            if f_close_checkbox.isChecked():
                f_window.close()
            QMessageBox.warning(
                self,
                _("Success"),
                _("Created file(s)"),
            )

        def cancel_handler():
            f_window.close()

        def set_output_file_name():
            if not str(f_output_name.text()):
                f_file = str(f_name.text())
                if f_file:
                    f_file_name = f_file.rsplit('.')[0] + self.ac_ext
                    f_output_name.setText(f_file_name)

        def file_name_select():
            try:
                if not os.path.isdir(self.last_ac_dir):
                    self.last_ac_dir = HOME
                if f_batch_checkbox.isChecked():
                    f_dir = QFileDialog.getExistingDirectory(
                        MAIN_WINDOW,
                        _("Open Folder"),
                        self.last_ac_dir,
                        options=QFileDialog.Option.DontUseNativeDialog,
                    )
                    if f_dir is None:
                        return
                    f_dir = str(f_dir)
                    if not f_dir:
                        return
                    f_name.setText(f_dir)
                    self.last_ac_dir = f_dir
                else:
                    f_file_name, f_filter = QFileDialog.getOpenFileName(
                        MAIN_WINDOW,
                        _("Select a file name to save to..."),
                        self.last_ac_dir,
                        filter=_("Audio Files {}").format(
                            '(*.wav *.{})'.format(a_label)
                        ),
                        options=QFileDialog.Option.DontUseNativeDialog,
                    )
                    if f_file_name and str(f_file_name):
                        f_name.setText(str(f_file_name))
                        self.last_ac_dir = os.path.dirname(f_file_name)
                        if f_file_name.lower().endswith(".{}".format(a_label)):
                            f_wav_radiobutton.setChecked(True)
                        elif f_file_name.lower().endswith(".wav"):
                            f_mp3_radiobutton.setChecked(True)
                        set_output_file_name()
                        self.last_ac_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                show_generic_exception(ex)

        def file_name_select_output():
            try:
                if not os.path.isdir(self.last_ac_dir):
                    self.last_ac_dir = HOME
                if f_batch_checkbox.isChecked():
                    f_dir = QFileDialog.getExistingDirectory(
                        MAIN_WINDOW,
                        _("Open Folder"),
                        self.last_ac_dir,
                        options=QFileDialog.Option.DontUseNativeDialog,
                    )
                    if f_dir is None:
                        return
                    f_dir = str(f_dir)
                    if not f_dir:
                        return
                    f_output_name.setText(f_dir)
                    self.last_ac_dir = f_dir
                else:
                    f_file_name, f_filter = QFileDialog.getSaveFileName(
                        MAIN_WINDOW,
                        _("Select a file name to save to..."),
                        self.last_ac_dir,
                        options=QFileDialog.Option.DontUseNativeDialog,
                    )
                    if f_file_name and str(f_file_name):
                        f_file_name = str(f_file_name)
                        if not f_file_name.endswith(self.ac_ext):
                            f_file_name += self.ac_ext
                        f_output_name.setText(f_file_name)
                        self.last_ac_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                LOG.exception(ex)

        def format_changed(a_val=None):
            if f_wav_radiobutton.isChecked():
                self.ac_ext = ".wav"
            else:
                self.ac_ext = ".{}".format(a_label)
            if not f_batch_checkbox.isChecked():
                f_str = str(f_output_name.text()).strip()
                if f_str and not f_str.endswith(self.ac_ext):
                    f_arr = f_str.rsplit(".")
                    f_output_name.setText(f_arr[0] + self.ac_ext)

        def batch_changed(a_val=None):
            if a_val:
                f_name.setToolTip(
                    'The folder containing files to be converted'
                )
                f_output_name.setToolTip(
                    'The folder to place converted files in'
                )
            else:
                f_name.setToolTip('The file to be converted')
                f_output_name.setToolTip('The name of the converted file')
            f_name.setText("")
            f_output_name.setText("")

        self.ac_ext = ".wav"
        f_window = QDialog(MAIN_WINDOW)

        f_window.setWindowTitle(_("{} Converter".format(a_label)))

        vlayout = QVBoxLayout()
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_window.setLayout(vlayout)

        f_name = QLineEdit()
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(480)
        f_layout.addWidget(QLabel(_("Input:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QPushButton(_("Select"))
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_output_name = QLineEdit()
        f_output_name.setReadOnly(True)
        f_output_name.setMinimumWidth(480)
        f_layout.addWidget(QLabel(_("Output:")), 1, 0)
        f_layout.addWidget(f_output_name, 1, 1)
        f_select_file_output = QPushButton(_("Select"))
        f_select_file_output.pressed.connect(file_name_select_output)
        f_layout.addWidget(f_select_file_output, 1, 2)

        f_layout.addWidget(QLabel(_("Convert to:")), 2, 1)
        f_rb_group = QButtonGroup()
        f_wav_radiobutton = QRadioButton("wav")
        f_wav_radiobutton.setChecked(True)
        f_rb_group.addButton(f_wav_radiobutton)
        f_wav_layout = QHBoxLayout()
        f_wav_layout.addWidget(f_wav_radiobutton)
        f_layout.addLayout(f_wav_layout, 3, 1)
        f_wav_radiobutton.toggled.connect(format_changed)

        f_mp3_radiobutton = QRadioButton(a_label)
        f_rb_group.addButton(f_mp3_radiobutton)
        f_mp3_layout = QHBoxLayout()
        f_mp3_layout.addWidget(f_mp3_radiobutton)
        f_mp3_radiobutton.toggled.connect(format_changed)
        f_mp3_br_combobox = QComboBox()
        f_mp3_br_combobox.addItems(["320", "256", "192", "160", "128"])
        f_mp3_layout.addWidget(QLabel(_("Bitrate")))
        f_mp3_layout.addWidget(f_mp3_br_combobox)
        f_layout.addLayout(f_mp3_layout, 4, 1)

        f_batch_checkbox = QCheckBox(_("Batch convert entire folder?"))
        f_batch_checkbox.stateChanged.connect(batch_changed)
        batch_changed(0)
        f_layout.addWidget(f_batch_checkbox, 6, 1)

        f_close_checkbox = QCheckBox("Close on finish?")
        f_close_checkbox.setChecked(True)
        f_layout.addWidget(f_close_checkbox, 9, 1)

        f_ok_layout = QHBoxLayout()
        f_ok_layout.addItem(
            QSpacerItem(
                10,
                10,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            ),
        )
        f_ok = QPushButton(_("OK"))
        f_ok.setMinimumWidth(75)
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        vlayout.addLayout(f_ok_layout)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.setMinimumWidth(75)
        f_cancel.pressed.connect(cancel_handler)
        f_ok_layout.addWidget(f_cancel)
        f_status_label = QLabel("")
        f_layout.addWidget(f_status_label, 15, 1)
        f_window.exec()

    def on_offline_render(self):
        shared.PLUGIN_UI_DICT.save_all_plugin_state()
        self.current_window.on_offline_render()

    def on_undo(self):
        self.current_window.on_undo()

    def on_redo(self):
        self.current_window.on_redo()

def final_gc(a_print=True):
    """ Brute-force garbage collect all possible objects to
        prevent the infamous PyQt SEGFAULT-on-exit...
    """
    LOG.info("Called final_gc")
    f_last_unreachable = gc.collect()
    if not f_last_unreachable:
        if a_print:
            LOG.info("Successfully garbage collected all objects")
        return
    for f_i in range(2, 12):
        time.sleep(0.1)
        f_unreachable = gc.collect()
        if f_unreachable == 0:
            if a_print:
                LOG.info("Successfully garbage collected all objects "
                    "in {} iterations".format(f_i))
            return
        elif f_unreachable >= f_last_unreachable:
            break
        else:
            f_last_unreachable = f_unreachable
    if a_print:
        LOG.warning("gc.collect() returned {} unreachable objects "
            "after {} iterations".format(f_unreachable, f_i))

def flush_events():
    LOG.info("Called flush_events")
    for f_i in range(5):
        shared.APP.processEvents()
        time.sleep(0.1)

def global_close_all():
    shared.PLUGIN_UI_DICT.close_all_plugin_windows()
    close_engine()
    for f_module in shared.HOST_MODULES:
        f_module.global_close_all()

def global_ui_refresh_callback(a_restore_all=False):
    """ Use this to re-open all existing items/sequences/song in
        their editors when the files have been changed externally
    """
    for f_module in shared.HOST_MODULES:
        f_module.global_ui_refresh_callback(a_restore_all)

#Opens or creates a new project
def global_open_project(a_project_file, a_wait=True):
    # TODO: SG DEPRECATED
    global PROJECT_FILE
    PROJECT_FILE = a_project_file
    open_engine(a_project_file, get_fps())
    constants.PROJECT = sg_project.SgProject()
    constants.PROJECT.suppress_updates = True
    constants.PROJECT.open_project(a_project_file, False)
    constants.PROJECT.suppress_updates = False
    try:
        constants.PROJECT.create_backup()
    except Exception as ex:
        LOG.error("constants.PROJECT.create_backup() failed")
        LOG.exception(ex)
    shared.PLUGIN_UI_DICT = SgPluginUiDict(
        constants.PROJECT,
        constants.IPC,
    )

    for f_module in shared.HOST_MODULES:
        f_module.global_open_project(a_project_file)
    open_bookmarks()


def global_new_project(a_project_file, a_wait=True):
    # TODO: SG DEPRECATED
    global PROJECT_FILE
    PROJECT_FILE = a_project_file
    constants.PROJECT = sg_project.SgProject()
    constants.PROJECT.new_project(a_project_file)
    MAIN_WINDOW.last_offline_dir = constants.PROJECT.user_folder
    shared.PLUGIN_UI_DICT = SgPluginUiDict(
        constants.PROJECT,
        constants.IPC,
    )

    for f_module in shared.HOST_MODULES:
        f_module.global_new_project(a_project_file)
    open_engine(a_project_file, get_fps())
    open_bookmarks()


def splash_screen_opening(project_file):
    if len(project_file) > 100:
        f_msg = "Opening ..." + project_file[-100:]
    else:
        f_msg = "Opening " + project_file
    SPLASH_SCREEN.status_update(f_msg)

def _load_project(project_file):
    if project_file:
        set_project(project_file)
    else:
        project_file = util.get_file_setting("last-project", str, None)
        if not project_file:
            project_file = os.path.join(
                constants.DEFAULT_PROJECT_DIR,
                "default-project",
                f"{constants.MAJOR_VERSION}.project",
            )
            LOG.info(f"No default project at '{project_file}'")

    if (
        os.path.exists(project_file)
        and
        not os.access(os.path.dirname(project_file), os.W_OK)
    ):
        QMessageBox.warning(
            MAIN_WINDOW,
            _("Error"),
            _(
                "You do not have read+write permissions to {}, please correct "
                "this and restart Stargate"
            ).format(
                os.path.dirname(project_file),
            ),
        )

        MAIN_WINDOW.prepare_to_quit()

    splash_screen_opening(project_file)

    if os.path.exists(project_file):
        try:
            check_project_version(
                MAIN_WINDOW,
                project_file,
            )
            global_open_project(project_file)
        except StargateProjectVersionError:
            exit(1)
        except Exception as ex:
            LOG.exception(ex)
            QMessageBox.warning(
                MAIN_WINDOW,
                _("Error"),
                _(
                    "Error opening project, check the logs for details.  "
                    "If the problem persists, you may need to use the "
                    "project recovery tool on the welcome screen"
                )
            )
            MAIN_WINDOW.prepare_to_quit()
    else:
        global_new_project(project_file)


def main(
    splash_screen,
    project_file,
):
    global MAIN_WINDOW, SPLASH_SCREEN
    scaler = ui_scaler_factory()
    major_version = util.META_DOT_JSON['version']['major']
    minor_version = util.META_DOT_JSON['version']['minor']
    LOG.info(f"Starting {major_version}-{minor_version}:{util.COMMIT_HASH}")
    log_screen_info()
    SPLASH_SCREEN = splash_screen
    widgets.knob_setup()
    QPixmapCache.setCacheLimit(1024 * 1024)
    MAIN_WINDOW = SgMainWindow()
    # Ensure that the engine is not running before trying to access
    # audio hardware
    pid = check_engine()
    if pid:
        f_answer = QMessageBox.question(
            None,
            _("Warning"),
            sg_strings.multiple_instances_warning,
            buttons=(
                QMessageBox.StandardButton.Ok
                |
                QMessageBox.StandardButton.Cancel
            ),
        )
        if f_answer == QMessageBox.StandardButton.Cancel:
            sys.exit(1)
        kill_engine(pid)

    MAIN_WINDOW.setup(scaler)
    shared.APP.lastWindowClosed.connect(shared.APP.quit)

    if not os.access(HOME, os.W_OK):
        QMessageBox.warning(
            MAIN_WINDOW,
            _("Error"),
            _(
                "You do not have read+write permissions to {}, please correct "
                "this and restart Stargate"
            ).format(HOME),
        )
        MAIN_WINDOW.prepare_to_quit()

    _load_project(project_file)

    shared.set_window_title()
    SPLASH_SCREEN.status_update(_("Loading project..."))
    for i in range(600):
        if (
            constants.READY
            or
            util.ENGINE_RETCODE is not None
        ):
            break
        time.sleep(0.05)
        QApplication.processEvents()

    if i < 15:
        SPLASH_SCREEN.status_update(_("Showing the main window"))
        time.sleep((20 - i) * 0.1)

    if util.ENGINE_RETCODE is not None:
        handle_engine_error(util.ENGINE_RETCODE)
        if util.ENGINE_RETCODE == 1003:
            shared.IGNORE_CLOSE_EVENT = False
            MAIN_WINDOW.prepare_to_quit()

    # Workaround for weird stuff happening in Windows during initialization
    constants.IPC_ENABLED = True
    return MAIN_WINDOW

