from sglib import constants
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.plugins import *
from sgui.sgqt import *

from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui.daw import strings as daw_strings
from sgui.daw.lib import item as item_lib
from sgui.widgets.transport import AbstractTransportWidget
from sglib.lib import util
from sglib.lib.translate import _


MREC_EVENTS = []

class TransportWidget(AbstractTransportWidget):
    def __init__(self):
        self.recording_timestamp = None
        self.suppress_osc = True
        self.last_open_dir = HOME
        self.group_box = QWidget()
        self.group_box.setObjectName("transport_panel")
        self.hlayout1 = QHBoxLayout(self.group_box)

        self.loop_mode_checkbox = QCheckBox()
        self.loop_mode_checkbox.setObjectName("loop_mode")
        self.hlayout1.addWidget(self.loop_mode_checkbox)
        self.loop_mode_checkbox.stateChanged.connect(
            self.on_loop_mode_changed,
        )

        # Mouse tools
        self.tool_select_rb = QRadioButton()
        self.tool_select_rb.setObjectName("tool_select")
        self.tool_select_rb.setToolTip(
            _("Select items by clicking or dragging (hotkey: a)")
        )
        self.hlayout1.addWidget(self.tool_select_rb)
        self.tool_select_rb.clicked.connect(self.tool_select_clicked)
        self.tool_select_rb.setChecked(True)

        self.tool_draw_rb = QRadioButton()
        self.tool_draw_rb.setObjectName("tool_draw")
        self.tool_draw_rb.setToolTip(_("Draw items by clicking (hotkey: s)"))
        self.tool_draw_rb.clicked.connect(self.tool_draw_clicked)
        self.hlayout1.addWidget(self.tool_draw_rb)

        self.tool_erase_rb = QRadioButton()
        self.tool_erase_rb.setObjectName("tool_erase")
        self.tool_erase_rb.setToolTip(_(
            "Erase items by clicking and dragging (hotkey: d)"
        ))
        self.tool_erase_rb.clicked.connect(self.tool_erase_clicked)
        self.hlayout1.addWidget(self.tool_erase_rb)

        self.tool_split_rb = QRadioButton()
        self.tool_split_rb.setObjectName("tool_split")
        self.tool_split_rb.setToolTip(_("Split items by clicking (hotkey: f)"))
        self.tool_split_rb.clicked.connect(self.tool_split_clicked)
        self.hlayout1.addWidget(self.tool_split_rb)

        self.suppress_osc = False
        shared.HARDWARE_WIDGET.overdub_checkbox.setToolTip(
            _("Checking this box causes recording to "
            "unlink existing items and append new events to the "
            "existing events"))
        self.loop_mode_checkbox.setToolTip(
            "Use this to toggle between normal playback and looping a \n"
            "region set by right clicking the sequencer timeline.\n"
            "You can toggle with CTRL+L"
        )

    def tab_changed(self, index):
        if index == shared.TAB_ITEM_EDITOR:
            shared.ITEM_EDITOR.set_transport_tool_visibility()
        elif index == shared.TAB_SEQUENCER:
            # Restore all
            self.set_tool_button_visibility()
        else:
            self.set_tool_button_visibility(False, False, False, False)

    def set_tool_button_visibility(
        self,
        select=True,
        draw=True,
        erase=True,
        split=True,
    ):
        self.tool_select_rb.setVisible(select)
        shared.DAW.select_mode_action.setEnabled(select)

        for enabled, rb, action in (
            (
                draw,
                self.tool_draw_rb,
                shared.DAW.draw_mode_action,
            ),
            (
                erase,
                self.tool_erase_rb,
                shared.DAW.erase_mode_action,
            ),
            (
                split,
                self.tool_split_rb,
                shared.DAW.split_mode_action,
            ),
        ):
            rb.setVisible(enabled)
            action.setEnabled(enabled)
            if (
                not enabled
                and
                rb.isChecked()
            ):
                self.tool_select_clicked()

    def tool_select_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_SELECT
        if not self.tool_select_rb.isChecked():
            self.tool_select_rb.setChecked(True)

    def tool_draw_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_DRAW
        if not self.tool_draw_rb.isChecked():
            self.tool_draw_rb.setChecked(True)

    def tool_erase_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_ERASE
        if not self.tool_erase_rb.isChecked():
            self.tool_erase_rb.setChecked(True)

    def tool_split_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_SPLIT
        if not self.tool_split_rb.isChecked():
            self.tool_split_rb.setChecked(True)

    def open_project(self):
        shared.HARDWARE_WIDGET.audio_inputs.open_project()

    def on_panic(self):
        constants.DAW_PROJECT.ipc().panic()

    def set_time(self, a_beat=None):
        if a_beat is None:
            a_beat = shared.SEQUENCER.get_beat_value()
        f_text = shared.CURRENT_SEQUENCE.get_time_at_beat(a_beat)
        glbl_shared.TRANSPORT.set_time(f_text)

    def set_pos_from_cursor(self, a_beat):
        if glbl_shared.IS_PLAYING or glbl_shared.IS_RECORDING:
            f_beat = float(a_beat)
            self.set_time(f_beat)

    def set_controls_enabled(self, a_enabled):
        for f_widget in (
            shared.SEQ_WIDGET.snap_combobox,
            shared.HARDWARE_WIDGET.overdub_checkbox,
        ):
            f_widget.setEnabled(a_enabled)

    def on_play(self):
        if shared.MAIN_WINDOW.currentIndex() == shared.TAB_ITEM_EDITOR:
            shared.SEQUENCER.open_sequence()
        shared.PLAYLIST_EDITOR.on_play()
        shared.SEQ_WIDGET.on_play()
        shared.AUDIO_SEQ_WIDGET.on_play()
        shared.HARDWARE_WIDGET.on_play()
        shared.SEQUENCER.start_playback()
        constants.DAW_PROJECT.ipc().en_playback(
            1,
            shared.SEQUENCER.get_beat_value(),
        )
        self.set_controls_enabled(False)
        return True

    def on_stop(self):
        constants.DAW_PROJECT.ipc().en_playback(0)
        shared.PLAYLIST_EDITOR.on_stop()
        shared.SEQ_WIDGET.on_stop()
        shared.HARDWARE_WIDGET.on_stop()
        shared.AUDIO_SEQ_WIDGET.on_stop()
        self.set_controls_enabled(True)
        self.loop_mode_checkbox.setEnabled(True)

        if glbl_shared.IS_RECORDING:
            f_restart_engine = False
            f_audio_count = len(
                shared.HARDWARE_WIDGET.audio_inputs.active(),
            )
            if f_audio_count:
                f_stop_time = datetime.datetime.now()
                f_delta = (
                    f_stop_time - self.recording_timestamp) * f_audio_count
                f_restart_engine = glbl_shared.add_entropy(f_delta)
            if self.rec_end is None:
                self.rec_end = round(shared.SEQUENCER.get_beat_value() + 0.5)
            self.show_save_items_dialog(a_restart=f_restart_engine)

        shared.SEQUENCER.stop_playback()
        #shared.SEQ_WIDGET.open_sequence()
        self.set_time(shared.SEQUENCER.get_beat_value())
        #shared.global_set_playback_pos()

    def show_save_items_dialog(self, a_restart=False):
        f_inputs = shared.HARDWARE_WIDGET.audio_inputs.inputs
        def ok_handler():
            f_file_name = str(f_file.text())
            if f_file_name is None or f_file_name == "":
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _("You must select a name for the item"),
                )
                return

            f_sample_count = shared.CURRENT_SEQUENCE.get_sample_count(
                self.rec_start,
                self.rec_end,
                util.SAMPLE_RATE,
            )

            item_lib.save_recorded_items(
                f_file_name,
                MREC_EVENTS,
                shared.HARDWARE_WIDGET.overdub_checkbox.isChecked(),
                util.SAMPLE_RATE,
                self.rec_start,
                self.rec_end,
                f_inputs,
                f_sample_count,
                f_file_name,
            )
            shared.SEQ_WIDGET.open_sequence()
            if a_restart:
                glbl_shared.restart_engine()
            f_window.close()

        def text_edit_handler(a_val=None):
            text = util.remove_bad_chars(
                f_file.text()
            )
            if text != f_file.text():
                f_file.setText(text)

        def cancel_handler():
            constants.PROJECT.clear_audio_tmp_folder()
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Save Recorded Files"))
        f_window.setMinimumWidth(330)
        vlayout = QVBoxLayout()
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_window.setLayout(vlayout)
        f_layout.addWidget(QLabel(_("Save recorded items")), 0, 2)
        f_layout.addWidget(QLabel(_("Item Name:")), 3, 1)
        f_file = QLineEdit()
        f_file.setToolTip(
            'The name to assign to this recording.  You must choose a unique '
            'name each time'
        )
        f_file.setMaxLength(24)
        f_file.textEdited.connect(text_edit_handler)
        f_layout.addWidget(f_file, 3, 2)
        f_ok_button = QPushButton(_("Save"))
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QPushButton(_("Discard"))
        f_cancel_button.clicked.connect(cancel_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        vlayout.addLayout(f_ok_cancel_layout)
        f_window.exec()

    def on_rec(self):
        if self.loop_mode_checkbox.isChecked():
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("Loop recording is not supported",
            )
        )
            return False
        shared.HARDWARE_WIDGET.active_devices = [
            x for x in shared.MIDI_DEVICES_DIALOG.devices
            if x.record_checkbox.isChecked()
        ]
        if (
            not shared.HARDWARE_WIDGET.active_devices
            and
            not shared.HARDWARE_WIDGET.audio_inputs.active()
        ):
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("No MIDI or audio inputs record-armed")
            )
            return False
        shared.PLAYLIST_EDITOR.on_play()
        shared.SEQ_WIDGET.on_play()
        shared.HARDWARE_WIDGET.on_rec()
        shared.AUDIO_SEQ_WIDGET.on_play()
        shared.SEQUENCER.start_playback()
        self.set_controls_enabled(False)
        self.loop_mode_checkbox.setEnabled(False)
        MREC_EVENTS.clear()
        f_loop_pos = shared.SEQUENCER.get_loop_pos(a_warn=False)
        if (
            not self.loop_mode_checkbox.isChecked()
            or
            not f_loop_pos
        ):
            self.rec_start = shared.SEQUENCER.get_beat_value()
            self.rec_end = None
        else:
            self.rec_start, self.rec_end = f_loop_pos
        self.recording_timestamp = datetime.datetime.now()
        constants.DAW_PROJECT.ipc().en_playback(2, self.rec_start)
        return True

    def on_loop_mode_changed(self, a_loop_mode):
        # The states we expect are 0 or 2, not 0 or 1
        if a_loop_mode in (0, QtCore.Qt.CheckState.Unchecked):
            a_loop_mode = 0
        else:
            a_loop_mode = 1
        if not self.suppress_osc:
            constants.DAW_PROJECT.ipc().set_loop_mode(a_loop_mode)

    def toggle_loop_mode(self):
        self.loop_mode_checkbox.setChecked(
            not self.loop_mode_checkbox.isChecked()
        )

    def reset(self):
        self.loop_mode_checkbox.setChecked(False)
        shared.HARDWARE_WIDGET.overdub_checkbox.setChecked(False)

