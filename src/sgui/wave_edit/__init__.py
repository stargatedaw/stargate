from sglib.lib import *
from sglib.lib.util import *
from sgui.plugins import *
from sgui.sgqt import *
from sgui.widgets import *

from sgui.daw.item_editor.audio._shared import (
    remove_path_from_painter_path_cache,
)

from sglib import constants
from sglib.api.wave_edit import api_project_notes
from sglib.ipc.abstract import AbstractIPC
from sglib.lib import strings as sg_strings
from sglib.lib.translate import _
from sglib.log import LOG
from sglib.math import clip_value
from sglib.models.project.abstract import AbstractProject
from sglib.models.track_plugin import track_plugin, track_plugins
from sglib.models.stargate import AudioInputTrack, AudioInputTracks
from sgui import shared as glbl_shared
from sgui.util import show_generic_exception
from sgui.widgets.transport import AbstractTransportWidget
import os
import math


TRACK_COUNT_ALL = 1

TAB_EDITOR = 0
TAB_PLUGIN_RACK = 1
TAB_NOTES = 2

TOTAL_FX_COUNT = 10

wave_edit_folder = os.path.join("projects", "wave_edit")
wave_edit_folder_tracks = os.path.join(wave_edit_folder, "tracks")
file_wave_editor_bookmarks = os.path.join(
    wave_edit_folder, "bookmarks.txt")
file_notes = os.path.join(wave_edit_folder, "notes.txt")
file_pyinput = os.path.join(wave_edit_folder, "input.txt")


class WaveEditProject(AbstractProject):
    def __init__(self, a_with_audio):
        self.TRACK_COUNT = TRACK_COUNT_ALL
        self.suppress_updates = False

    def ipc(self):
        return constants.WAVE_EDIT_IPC

    def save_track_plugins(self, a_uid, a_track):
        f_folder = wave_edit_folder_tracks
        if not self.suppress_updates:
            self.save_file(f_folder, str(a_uid), str(a_track))

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file))[0]
        self.track_pool_folder = os.path.join(
            self.project_folder, wave_edit_folder_tracks)
        #files
        self.pynotes_file = os.path.join(
            self.project_folder, file_notes)
        self.pywebm_file = os.path.join(
            self.project_folder, file_wave_editor_bookmarks)
        self.audio_inputs_file = os.path.join(
            self.project_folder, file_pyinput)

        self.project_folders = [
            self.project_folder, self.track_pool_folder,]

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            LOG.warning("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

#        if a_notify_osc:
#            constants.WAVE_EDIT_IPC.open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            LOG.info(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

        plugins = track_plugins()
        for i2 in range(TOTAL_FX_COUNT):
            plugins.plugins.append(track_plugin(i2, 0, -1))
        self.save_track_plugins(0, plugins)

#        self.commit("Created project")
#        if a_notify_osc:
#            constants.WAVE_EDIT_IPC.open_song(self.project_folder)

    def get_notes(self):
        if os.path.isfile(self.pynotes_file):
            return read_file_text(self.pynotes_file)
        else:
            return ""

    def write_notes(self, a_text):
        write_file_text(self.pynotes_file, a_text)

    def set_we_bm(self, a_file_list):
        f_list = [x for x in sorted(a_file_list) if len(x) < 1000]
        write_file_text(self.pywebm_file, "\n".join(f_list))

    def get_we_bm(self):
        if os.path.exists(self.pywebm_file):
            f_list = read_file_text(self.pywebm_file).split("\n")
            return [x for x in f_list if x]
        else:
            return []

    def save_audio_inputs(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", file_pyinput, str(a_tracks))

    def get_audio_inputs(self):
        if os.path.isfile(self.audio_inputs_file):
            with open(self.audio_inputs_file) as f_file:
                f_str = f_file.read()
            return AudioInputTracks.from_str(f_str)
        else:
            return AudioInputTracks()


def normalize_dialog():
    def on_ok():
        f_window.f_result = f_db_spinbox.value()
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QDialog(MAIN_WINDOW)
    f_window.f_result = None
    f_window.setWindowTitle(_("Normalize"))
    f_window.setFixedSize(150, 90)
    f_layout = QVBoxLayout()
    f_window.setLayout(f_layout)
    f_hlayout = QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_hlayout.addWidget(QLabel("dB"))
    f_db_spinbox = QDoubleSpinBox()
    f_db_spinbox.setToolTip(
        'The volume to normalize to, in decibels.  This will move the volume '
        'fader so that the audio peaks at almost exactly this volume'
    )
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setRange(-18.0, 0.0)
    f_db_spinbox.setDecimals(1)
    f_db_spinbox.setValue(0.0)
    f_ok_button = QPushButton(_("OK"))
    f_ok_cancel_layout = QHBoxLayout()
    f_layout.addLayout(f_ok_cancel_layout)
    f_ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(on_ok)
    f_cancel_button = QPushButton(_("Cancel"))
    f_ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(on_cancel)
    f_window.exec()
    return f_window.f_result

class AudioInput:
    def __init__(self, a_num, a_layout, a_callback, a_count):
        self.input_num = int(a_num)
        self.callback = a_callback
        a_layout.addWidget(QLabel(str(a_num)), a_num + 1, 21)
        self.name_lineedit = QLineEdit(str(a_num))
        self.name_lineedit.setMaximumWidth(120)
        self.name_lineedit.setToolTip('A friendly name to give this input')
        self.name_lineedit.editingFinished.connect(self.name_update)
        a_num += 1
        a_layout.addWidget(self.name_lineedit, a_num, 0)
        self.rec_checkbox = QCheckBox("")
        self.rec_checkbox.setToolTip(
            'Enable or disable recording of this input'
        )
        self.rec_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.rec_checkbox, a_num, 1)

        self.monitor_checkbox = QCheckBox(_(""))
        self.monitor_checkbox.setToolTip(
            'Monitor ths input, play it through the monitor speakers'
        )
        self.monitor_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.monitor_checkbox, a_num, 2)

        self.vol_layout = QHBoxLayout()
        a_layout.addLayout(self.vol_layout, a_num, 3)
        self.vol_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.vol_slider.setToolTip('Volume gain for this input in decibels')
        self.vol_slider.setRange(-240, 240)
        self.vol_slider.setValue(0)
        self.vol_slider.setMinimumWidth(240)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_slider.sliderReleased.connect(self.update_engine)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QLabel("0.0dB")
        self.vol_label.setMinimumWidth(64)
        self.vol_layout.addWidget(self.vol_label)
        self.stereo_combobox = QComboBox()
        self.stereo_combobox.setToolTip(
            'Select an audio channel to pair with this one as the right '
            'channel of a stereo pair'
        )
        a_layout.addWidget(self.stereo_combobox, a_num, 4)
        self.stereo_combobox.setMinimumWidth(72)
        self.stereo_combobox.addItems([_("None")] +
            [str(x) for x in range(a_count + 1)])
        self.stereo_combobox.currentIndexChanged.connect(self.update_engine)
        self.suppress_updates = False

    def name_update(self, a_val=None):
        self.update_engine(a_notify=False)

    def update_engine(self, a_val=None, a_notify=True):
        if not self.suppress_updates:
            self.callback(a_notify)

    def vol_changed(self):
        f_vol = self.get_vol()
        self.vol_label.setText("{}dB".format(f_vol))
        if not self.suppress_updates:
            constants.IPC.audio_input_volume(self.input_num, f_vol)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def get_name(self):
        return str(self.name_lineedit.text())

    def get_value(self):
        f_on = 1 if self.rec_checkbox.isChecked() else 0
        f_vol = self.get_vol()
        f_monitor = 1 if self.monitor_checkbox.isChecked() else 0
        f_stereo = self.stereo_combobox.currentIndex() - 1
        return AudioInputTrack(
            f_on,
            f_monitor,
            f_vol,
            0,
            f_stereo,
            0,
            self.name_lineedit.text(),
        )

    def set_value(self, a_val):
        self.suppress_updates = True
        f_rec = True if a_val.rec else False
        f_monitor = True if a_val.monitor else False
        self.name_lineedit.setText(a_val.name)
        self.rec_checkbox.setChecked(f_rec)
        self.monitor_checkbox.setChecked(f_monitor)
        self.vol_slider.setValue(int(a_val.vol * 10.0))
        self.stereo_combobox.setCurrentIndex(a_val.stereo + 1)
        self.suppress_updates = False


class AudioInputWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

        self.widget = QWidget()
        self.setWidget(self.widget)
        self.main_layout = QVBoxLayout(self.widget)
        self.layout = QGridLayout()
        self.main_layout.addWidget(QLabel(_("Audio Inputs")))
        self.main_layout.addLayout(self.layout)
        f_labels = (
            _("Name"), _("Rec."), _("Mon."), _("Gain"), _("Stereo"))
        for f_i, f_label in zip(range(len(f_labels)), f_labels):
            self.layout.addWidget(QLabel(f_label), 0, f_i)
        self.inputs = []
        f_count = 0
        if "audioInputs" in util.DEVICE_SETTINGS:
            f_count = int(util.DEVICE_SETTINGS["audioInputs"])
        for f_i in range(f_count):
            f_input = AudioInput(f_i, self.layout, self.callback, f_count - 1)
            self.inputs.append(f_input)
        self.layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
            200,
            0
        )

    def callback(self, a_notify):
        f_result = AudioInputTracks()
        for f_i, f_input in zip(range(len(self.inputs)), self.inputs):
            f_result.add_track(f_i, f_input.get_value())
        constants.WAVE_EDIT_PROJECT.save_audio_inputs(f_result)
        if a_notify:
            constants.WAVE_EDIT_PROJECT.ipc().save_audio_inputs()

    def active(self):
        return [x.get_value() for x in self.inputs
            if x.rec_checkbox.isChecked()]

    def open_project(self):
        f_audio_inputs = constants.WAVE_EDIT_PROJECT.get_audio_inputs()
        for k, v in f_audio_inputs.tracks.items():
            if k < len(self.inputs):
                self.inputs[k].set_value(v)


class TransportWidget(AbstractTransportWidget):
    def __init__(self):
        self.suppress_osc = True
        self.open_rec_dir = True
        self.start_sequence = 0
        self.last_bar = 0
        self.last_open_dir = HOME
        self.group_box = QWidget()
        self.group_box.setObjectName("transport_panel")
        self.vlayout = QVBoxLayout(self.group_box)
        self.hlayout1 = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout1)

        self.audio_inputs = AudioInputWidget()

        self.hlayout1.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        self.suppress_osc = False

    def open_project(self):
        self.audio_inputs.open_project()

    def on_panic(self):
        pass
        #constants.WAVE_EDIT_PROJECT.ipc().panic()

    def set_time(self, f_text="0:00.0"):
        #f_text = "{}:{}.{}".format(f_minutes, str(f_seconds).zfill(2), f_frac)
        glbl_shared.TRANSPORT.set_time(f_text)

    def on_play(self):
        if not WAVE_EDITOR.current_file:
            return False
        WAVE_EDITOR.on_play()
        constants.WAVE_EDIT_PROJECT.ipc().wn_playback(1)
        return True

    def on_stop(self):
        constants.WAVE_EDIT_PROJECT.ipc().wn_playback(0)
        WAVE_EDITOR.on_stop()
        if glbl_shared.IS_RECORDING:
            self.show_rec_dialog()

    def on_rec(self):
        if not self.audio_inputs.active():
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("No audio inputs are active, cannot record.  "
                "Enable one or more inputs in the transport drop-down.\n"
                "If there are no inputs in the drop-down, you will need "
                "to open the Menu->File->HardwareSettings in the \n"
                "transport and set the number of audio inputs to 1 or more"))
            return False
        constants.WAVE_EDIT_PROJECT.ipc().wn_playback(2)
        return True

    def show_rec_dialog(self):
        def on_ok():
            f_txt = str(f_name_lineedit.text()).strip()
            if not f_txt:
                QMessageBox.warning(
                    MAIN_WINDOW,
                    _("Error"),
                    _("Name cannot be empty"),
                )
                return
            for x in ("\\", "/", "~", "|"):
                if x in f_txt:
                    QMessageBox.warning(
                        MAIN_WINDOW, _("Error"),
                        _("Invalid char '{}'".format(x)))
                    return
            for f_i, f_ai in zip(
                range(len(self.audio_inputs.inputs)),
                self.audio_inputs.inputs,
            ):
                f_val = f_ai.get_value()
                if f_val.rec:
                    f_path = os.path.join(
                        constants.PROJECT.audio_tmp_folder, "{}.wav".format(f_i))
                    if os.path.isfile(f_path):
                        f_file_name = "-".join(
                            str(x) for x in (f_txt, f_i, f_ai.get_name()))
                        f_new_path = os.path.join(
                            constants.PROJECT.audio_rec_folder, f_file_name)
                        if f_new_path.lower().endswith(".wav"):
                            f_new_path = f_new_path[:-4]
                        if os.path.exists(f_new_path + ".wav"):
                            for f_i in range(10000):
                                f_tmp = "{}-{}.wav".format(f_new_path, f_i)
                                if not os.path.exists(f_tmp):
                                    f_new_path = f_tmp
                                    break
                        else:
                            f_new_path += ".wav"
                        shutil.move(f_path, f_new_path)
                    else:
                        LOG.error("Error, path did not exist: {}".format(f_path))
            self.open_rec_dir = f_open_rec_dir_checkbox.isChecked()
            if self.open_rec_dir:
                WAVE_EDITOR.file_browser.set_folder(
                    constants.PROJECT.audio_rec_folder)
            f_window.close()

        def on_cancel():
            constants.PROJECT.clear_audio_tmp_folder()
            f_window.close()

        def dialog_close_event(a_event):
            QDialog.closeEvent(f_window, a_event)

        f_window = QDialog(MAIN_WINDOW)
        f_window.closeEvent = dialog_close_event
        f_window.setWindowTitle(_("Save Recorded Audio"))
        #f_window.setFixedSize(420, 90)
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout = QHBoxLayout()
        f_layout.addLayout(f_hlayout)
        f_hlayout.addWidget(QLabel("Name"))
        f_name_lineedit = QLineEdit()
        f_name_lineedit.setMinimumWidth(330)
        f_hlayout.addWidget(f_name_lineedit)
        f_open_rec_dir_checkbox = QRadioButton(
            _("Open recording directory in the file browser when finished?"),
        )
        f_layout.addWidget(f_open_rec_dir_checkbox)
        if self.open_rec_dir:
            f_open_rec_dir_checkbox.setChecked(True)
        f_ok_button = QPushButton(_("OK"))
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(on_ok)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.pressed.connect(on_cancel)
        f_window.exec()

class audio_item(SgAudioItem):
    def clone(self):
        return audio_item.from_arr(str(self).strip("\n").split("|"))

    @staticmethod
    def from_str(f_str):
        return audio_item.from_arr(f_str.split("|"))

    @staticmethod
    def from_arr(a_arr):
        f_result = audio_item(*a_arr)
        return f_result

class MainWindow(QTabWidget):
    def __init__(self):
        super().__init__()
        self.first_offline_render = True
        self.last_offline_dir = HOME
        self.copy_to_clipboard_checked = True

        self.setObjectName("plugin_ui")

        #The tabs
        self.engine_mon_label = QLabel()
        self.engine_mon_label.setFixedWidth(150)
        self.engine_mon_label.setToolTip(sg_strings.ENGINE_MON)
        self.setCornerWidget(self.engine_mon_label)

        self.addTab(WAVE_EDITOR.widget, _("Wave Editor"))

        self.addTab(
            TRANSPORT.audio_inputs,
            _("Hardware"),
        )

        self.notes_tab = ProjectNotes(
            self,
            api_project_notes.load,
            api_project_notes.save,
        )
        self.addTab(
            self.notes_tab.widget,
            _("Project Notes"),
        )
        self.currentChanged.connect(self.tab_changed)

    def on_undo(self):
        QMessageBox.warning(
            MAIN_WINDOW,
            "Error",
            "Wave Editor does not support undo/redo",
        )

    def on_redo(self):
        self.on_undo()

    def tab_changed(self):
        f_index = self.currentIndex()
        if f_index == TAB_PLUGIN_RACK:
            for plugin in PLUGIN_RACK.plugins:
                if plugin.plugin_ui:
                    plugin.plugin_ui.widget_show()

    def on_offline_render(self, a_val=None):
        WAVE_EDITOR.on_export()

    def configure_callback(self, arr):
        f_pc_dict = {}
        f_ui_dict = {}
        f_cc_dict = {}
        for f_line in arr.split("\n"):
            if f_line == "":
                break
            a_key, a_val = f_line.split("|", 1)
            if a_key == "pc":
                f_plugin_uid, f_port, f_val = a_val.split("|")
                f_pc_dict[(f_plugin_uid, f_port)] = f_val
            elif a_key == "cur":
                if glbl_shared.IS_PLAYING:
                    f_sequence, f_bar, f_beat = a_val.split("|")
                    TRANSPORT.set_pos_from_cursor(f_sequence, f_bar, f_beat)
                    for f_editor in (AUDIO_SEQ, SEQUENCE_EDITOR):
                        f_editor.set_playback_pos(f_bar, f_beat)
            elif a_key == "peak":
                global_update_peak_meters(a_val)
            elif a_key == "cc":
                f_track_num, f_cc, f_val, channel = a_val.split("|")
                f_cc_dict[(f_track_num, f_cc, channel)] = f_val
            elif a_key == "ui":
                f_plugin_uid, f_name, f_val = a_val.split("|", 2)
                f_ui_dict[(f_plugin_uid, f_name)] = f_val
            elif a_key == "mrec":
                MREC_EVENTS.append(a_val)
            elif a_key == "ne":
                f_state, f_note = a_val.split("|")
                PIANO_ROLL_EDITOR.highlight_keys(f_state, f_note)
            elif a_key == "ml":
                glbl_shared.PLUGIN_UI_DICT.midi_learn_control[0].update_cc_map(
                    a_val, glbl_shared.PLUGIN_UI_DICT.midi_learn_control[1])
            elif a_key == "wec":
                if glbl_shared.IS_PLAYING:
                    value = float(a_val)
                    if math.isnan(value):
                        LOG.error(f"Engine sent value {a_val}")
                        return
                    WAVE_EDITOR.set_playback_cursor(value)
            elif a_key == "ready":
                glbl_shared.on_ready()
            elif a_key == "stop":
                LOG.info("Received message to stop playback from engine")
                glbl_shared.TRANSPORT.stop_button.trigger()
        #This prevents multiple events from moving the same control,
        #only the last goes through
        for k, f_val in f_ui_dict.items():
            f_plugin_uid, f_name = k
            if int(f_plugin_uid) in glbl_shared.PLUGIN_UI_DICT:
                glbl_shared.PLUGIN_UI_DICT[int(f_plugin_uid)].ui_message(
                    f_name, f_val)
        for k, f_val in f_pc_dict.items():
            f_plugin_uid, f_port = (int(x) for x in k)
            if f_plugin_uid in glbl_shared.PLUGIN_UI_DICT:
                glbl_shared.PLUGIN_UI_DICT[f_plugin_uid].set_control_val(
                    f_port, float(f_val))
        for k, f_val in f_cc_dict.items():
            f_track_num, f_cc, channel = (int(x) for x in k)
            plugin_uids = TRACK_PANEL.tracks[f_track_num].get_plugin_uids()
            for f_plugin_uid, plugin_channel in plugin_uids:
                if f_plugin_uid in glbl_shared.PLUGIN_UI_DICT:
                    plugin = glbl_shared.PLUGIN_UI_DICT[f_plugin_uid]
                    plugin.set_cc_val(f_cc, f_val)

    def prepare_to_quit(self):
        WAVE_EDITOR.sample_graph.scene.clear()

def global_update_peak_meters(a_val):
    for f_val in a_val.split("|"):
        f_list = f_val.split(":")
        f_index = int(f_list[0])
        if f_index in ALL_PEAK_METERS:
            for f_pkm in ALL_PEAK_METERS[f_index]:
                f_pkm.set_value(f_list[1:])
        else:
            LOG.warning("{} not in ALL_PEAK_METERS".format(f_index))


class WaveEditorWidget:
    def __init__(self):
        self.file_name = None
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.right_widget = QWidget()
        self.vlayout = QVBoxLayout(self.right_widget)
        self.file_browser = widgets.FileBrowserWidget()
        self.file_browser.load_button.pressed.connect(self.on_file_open)
        self.file_browser.list_file.itemDoubleClicked.connect(
            self.on_file_open)
        self.file_browser.preview_button.pressed.connect(self.on_preview)
        self.file_browser.stop_preview_button.pressed.connect(
            self.on_stop_preview)
        self.file_browser.list_file.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection,
        )
        self.layout.addWidget(self.file_browser.hsplitter)
        self.file_browser.hsplitter.addWidget(self.right_widget)
        self.file_hlayout = QHBoxLayout()

        self.sample_graph = AudioItemViewerWidget(
            self.marker_callback,
            self.marker_callback,
            self.marker_callback,
            self.marker_callback,
        )

        self.menu = QMenu(self.widget)
        self.menu_button = QPushButton(_("Menu"))
        self.menu_button.setMenu(self.menu)
        self.file_hlayout.addWidget(self.menu_button)

        self.export_action = QAction(_("Export..."), self.menu)
        self.export_action.setToolTip(
            'Open a dialog to export the file with edits and effects'
        )
        self.menu.addAction(self.export_action)
        self.export_action.triggered.connect(self.on_export)

        self.menu.addSeparator()

        self.copy_action = QAction(_("Copy File to Clipboard"), self.menu)
        self.menu.addAction(self.copy_action)
        self.copy_action.setToolTip(
            'Copy the full path to the file to the system clipboard'
        )
        self.copy_action.triggered.connect(self.copy_file_to_clipboard)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)

#        self.copy_item_action = self.menu.addAction(_("Copy as Audio Item"))
#        self.copy_item_action.triggered.connect(self.copy_audio_item)
#        self.copy_item_action.setShortcut(
#            QKeySequence.fromString("ALT+C"))

        self.paste_action = QAction(_("Paste File from Clipboard"), self.menu)
        self.menu.addAction(self.paste_action)
        self.paste_action.setToolTip(
            'First, you must copy the full path to an audio file to the '
            'system clipboard.  Open an audio file in the wave editor from '
            'the system clipboard'
        )
        self.paste_action.triggered.connect(self.open_file_from_clipboard)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)

        self.open_folder_action = QAction(
            _("Open parent folder in browser"),
            self.menu,
        )
        self.open_folder_action.setToolTip(
            'Open the parent folder of the currently loaded audio file in '
            'the file browser'
        )
        self.menu.addAction(self.open_folder_action)
        self.open_folder_action.triggered.connect(self.open_item_folder)

        self.menu.addSeparator()

        self.bookmark_action = QAction(_("Bookmark File"), self.menu)
        self.menu.addAction(self.bookmark_action)
        self.bookmark_action.setToolTip(
            'Bookmark this file in the project.  This will add the file to '
            'the Bookmarks button menu, so that it can be quickly opened '
            'again later, even after closing and reopening Stargate DAW'
        )
        self.bookmark_action.triggered.connect(self.bookmark_file)
        self.bookmark_action.setShortcut(
            QKeySequence.fromString("CTRL+D"),
        )

        self.delete_bookmark_action = QAction(_("Delete Bookmark"), self.menu)
        self.menu.addAction(self.delete_bookmark_action)
        self.delete_bookmark_action.setToolTip(
            'Delete this file from the project bookmarks.  It will no longer '
            'appear in the Bookmarks button menu'
        )
        self.delete_bookmark_action.triggered.connect(self.delete_bookmark)
        self.delete_bookmark_action.setShortcut(
            QKeySequence.fromString("ALT+D"),
        )

        self.menu.addSeparator()

        _action = self.menu.addMenu(self.sample_graph.scene_context_menu)
        _action.setText(_("Markers"))

        self.menu.addSeparator()

        self.normalize_action = QAction(_("Normalize"), self.menu)
        self.menu.addAction(self.normalize_action)
        self.normalize_action.setToolTip(
            'Normalize the volume of this sample (non-destructive).  The '
            'volume slider will be set to peak at a specified volume'
        )
        self.normalize_action.triggered.connect(self.normalize_dialog)

        self.stretch_shift_action = QAction(
            _("Time-Stretch/Pitch-Shift..."),
            self.menu,
        )
        self.menu.addAction(self.stretch_shift_action)
        self.stretch_shift_action.setToolTip(
            'Open a dialog to time stretch and/or pitch shift the audio file'
        )
        self.stretch_shift_action.triggered.connect(self.stretch_shift_dialog)

        self.bookmark_button = QPushButton(_("Bookmarks"))
        self.bookmark_button.setToolTip(
            'This button will show a menu of any project bookmarks you have '
            'created.  See the menu button for the bookmark action'
        )
        self.file_hlayout.addWidget(self.bookmark_button)

        self.history_button = QPushButton(_("History"))
        self.history_button.setToolTip(
            'Shows a history of files opened during this session.  To save '
            'the files permanently, bookmark them using the menu button'
        )
        self.file_hlayout.addWidget(self.history_button)

        ###############################

        self.menu_info = QMenu()
        self.menu_info_button = QPushButton(_("Info"))
        self.menu_info_button.setMenu(self.menu_info)
        self.file_hlayout.addWidget(self.menu_info_button)

        self.file_lineedit = QLineEdit()
        self.file_lineedit.setToolTip('The currently opened audio file')
        self.file_lineedit.setReadOnly(True)
        self.file_hlayout.addWidget(self.file_lineedit)
        self.vlayout.addLayout(self.file_hlayout)
        self.edit_tab = QWidget()
        self.file_browser.folders_tab_widget.addTab(
            self.edit_tab,
            _("Channel"),
        )
        self.edit_hlayout = QHBoxLayout(self.edit_tab)
        self.vol_layout = QVBoxLayout()
        self.edit_hlayout.addLayout(self.vol_layout)
        self.vol_slider = QSlider(QtCore.Qt.Orientation.Vertical)
        self.vol_slider.setToolTip('The volume slider for the audio file')
        self.vol_slider.setEnabled(False)
        self.vol_slider.setRange(-240, 120)
        self.vol_slider.setValue(0)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QLabel("0.0db")
        self.vol_label.setMinimumWidth(75)
        self.vol_layout.addWidget(self.vol_label)
        self.peak_meter = widgets.peak_meter(28, a_text=True)
        ALL_PEAK_METERS[0] = [self.peak_meter]
        self.ctrl_vlayout = QVBoxLayout()
        self.edit_hlayout.addLayout(self.ctrl_vlayout)
        self.fade_in_start = QSpinBox()
        self.fade_in_start.setToolTip(
            'The fade-in start volume.  This is the initial volume you will '
            'hear at the beginning of the fade-in, as it fades up to 0dB'
        )
        self.fade_in_start.setRange(-50, -6)
        self.fade_in_start.setValue(-24)
        self.fade_in_start.valueChanged.connect(self.marker_callback)
        self.ctrl_vlayout.addWidget(QLabel(_("Fade-In")))
        self.ctrl_vlayout.addWidget(self.fade_in_start)
        self.fade_out_end = QSpinBox()
        self.fade_out_end.setToolTip(
            'The fade-out end volume.  This will be the final volume you hear '
            'before the audio stops playing.  At the beginning of the fade '
            'out, volume will begin to decrease from 0dB to this value'
        )
        self.fade_out_end.setRange(-50, -6)
        self.fade_out_end.setValue(-24)
        self.fade_out_end.valueChanged.connect(self.marker_callback)
        self.ctrl_vlayout.addWidget(QLabel(_("Fade-Out")))
        self.ctrl_vlayout.addWidget(self.fade_out_end)
        self.ctrl_vlayout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Policy.Expanding),
        )
        self.edit_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.hlayout = QHBoxLayout()

        self.vlayout.addLayout(self.hlayout)
        self.hlayout.addWidget(self.sample_graph)
        self.hlayout.addWidget(self.peak_meter.widget)

        self.label_action = QWidgetAction(self.menu_button)
        self.label_action.setDefaultWidget(self.sample_graph.label)
        self.menu_info.addAction(self.label_action)
        self.sample_graph.label.setFixedSize(210, 123)

        self.orig_pos = 0
        self.duration = None
        self.sixty_recip = 1.0 / 60.0
        self.playback_cursor = None
        self.time_label_enabled = False
        self.file_browser.hsplitter.setSizes([420, 9999])
        self.copy_to_clipboard_checked = True
        self.last_offline_dir = HOME
        self.open_exported = False
        self.history = []
        self.graph_object = None
        self.current_file = None
        self.callbacks_enabled = True

        self.controls_to_disable = (
            self.file_browser.load_button,
            self.file_browser.preview_button,
            self.file_browser.stop_preview_button,
            self.history_button,
            self.sample_graph,
            self.vol_slider,
            self.bookmark_button,
            self.fade_in_start,
            self.fade_out_end,
        )
        self.sample_graph.setToolTip(
            "Load samples here by using the browser on the left "
            "and clicking the  'Load' button.  Move the markers to set "
            'sample start/end and fade in/out'
        )

    def save_callback(self):
        f_result = track_plugins()
        f_result.plugins = [x.get_value() for x in self.plugins]
        constants.WAVE_EDIT_PROJECT.save_track_plugins(
            self.track_number,
            f_result,
        )

    def open_plugins(self):
        f_plugins = constants.WAVE_EDIT_PROJECT.get_track_plugins(
            self.track_number,
        )
        if f_plugins:
            for f_plugin in f_plugins.plugins:
                self.plugins[f_plugin.index].set_value(f_plugin)

    def name_callback(self):
        return "Wave Editor"

    def copy_audio_item(self):
        pass
#        if self.graph_object is None:
#            return
#        f_uid = constants.PROJECT.get_wav_uid_by_name(self.current_file)
#        f_item = self.get_audio_item(f_uid)
#        raise NotImplementedError

    def bookmark_file(self):
        if self.graph_object is None:
            return
        f_list = self.get_bookmark_list()
        if self.current_file not in f_list:
            f_list.append(self.current_file)
            constants.WAVE_EDIT_PROJECT.set_we_bm(f_list)
            self.open_project()

    def get_bookmark_list(self):
        f_list = constants.WAVE_EDIT_PROJECT.get_we_bm()
        f_resave = False
        for f_item in f_list[:]:
            if not os.path.isfile(f_item):
                f_resave = True
                f_list.remove(f_item)
                LOG.warning("os.path.isfile({}) returned False, removing "
                    "from bookmarks".format(f_item))
        if f_resave:
            constants.WAVE_EDIT_PROJECT.set_we_bm(f_list)
        return sorted(f_list)

    def open_project(self):
        f_list = self.get_bookmark_list()
        if f_list:
            f_menu = QMenu(self.widget)
            f_menu.triggered.connect(self.open_file_from_action)
            self.bookmark_button.setMenu(f_menu)
            for f_item in f_list:
                f_action = f_menu.addAction(f_item)
                f_action.file_name = f_item
        else:
            self.bookmark_button.setMenu(None)

    def delete_bookmark(self):
        if self.graph_object is None:
            return
        f_list = constants.WAVE_EDIT_PROJECT.get_we_bm()
        if self.current_file in f_list:
            f_list.remove(self.current_file)
            constants.WAVE_EDIT_PROJECT.set_we_bm(f_list)
            self.open_project()

    def open_item_folder(self):
        f_path = str(self.file_lineedit.text())
        self.file_browser.open_file_in_browser(f_path)

    def normalize_dialog(self):
        if self.graph_object is None or glbl_shared.IS_PLAYING:
            return
        f_val = normalize_dialog()
        if f_val is not None:
            self.normalize(f_val)

    def normalize(self, a_value):
        f_val = self.graph_object.normalize(a_value)
        self.vol_slider.setValue(int(f_val * 10.0))

    def stretch_shift_dialog(self):
        f_path = self.current_file
        if f_path is None or glbl_shared.IS_PLAYING:
            return

        f_base_file_name = f_path.rsplit("/", 1)[1]
        f_base_file_name = f_base_file_name.rsplit(".", 1)[0]
        LOG.info(f_base_file_name)

        def on_ok(a_val=None):
            f_file, f_filter = QFileDialog.getSaveFileName(
                MAIN_WINDOW,
                "Save file as...",
                self.last_offline_dir,
                filter="Wav File (*.wav)",
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if f_file is None:
                return
            f_file = str(f_file)
            if f_file == "":
                return

            f_algo = str(f_algo_combobox.currentText())
            f_stretch = f_timestretch_amt.value()
            f_pitch = f_pitch_shift.value()

            if not f_file.endswith(".wav"):
                f_file += ".wav"
            self.last_offline_dir = os.path.dirname(f_file)

            if f_algo == "Rubberband":
                f_crispness = f_crispness_combobox.currentIndex()
                f_preserve_formants = f_preserve_formants_checkbox.isChecked()
                f_proc = util.rubberband(
                    f_path,
                    f_file,
                    f_stretch,
                    f_pitch,
                    f_crispness,
                    f_preserve_formants,
                )
            elif f_algo == "SBSMS":
                stretch_end = timestretch_end.value() \
                    if timestretch_end_checkbox.isChecked() else None
                pitch_end = pitch_shift_end.value() if \
                    pitch_shift_end_checkbox.isChecked() else None
                f_proc = util.sbsms(
                    f_path,
                    f_file,
                    f_stretch,
                    f_pitch,
                    stretch_end,
                    pitch_end,
                )
            elif f_algo == "Paulstretch":
                f_proc = util.paulstretch(
                    f_path,
                    f_file,
                    f_stretch,
                )
            else:
                raise ValueError(f"Invalid algorithm {f_algo}")

            f_proc.wait()
            self.open_file(f_file)
            f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        def algo_changed(index=None):
            algo = str(f_algo_combobox.currentText())
            if algo == "Rubberband":
                f_timestretch_amt.setRange(0.2, 4.0)
                pitch_shift_label.show()
                f_pitch_shift.show()
                rubberband_groupbox.show()
                sbsms_groupbox.hide()
            elif algo == "SBSMS":
                f_timestretch_amt.setRange(0.2, 4.0)
                pitch_shift_label.show()
                f_pitch_shift.show()
                rubberband_groupbox.hide()
                sbsms_groupbox.show()
            elif algo == "Paulstretch":
                f_timestretch_amt.setRange(0.2, 30.0)
                rubberband_groupbox.hide()
                sbsms_groupbox.hide()
                f_pitch_shift.hide()
                pitch_shift_label.hide()

        f_window = QDialog(self.widget)
        f_window.setMinimumWidth(390)
        f_window.setWindowTitle(_("Time-Stretch/Pitch-Shift Sample"))
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)

        f_time_gridlayout = QGridLayout()
        f_layout.addLayout(f_time_gridlayout)

        pitch_shift_label = QLabel(_("Pitch(semitones):"))
        f_time_gridlayout.addWidget(pitch_shift_label, 10, 0)
        f_pitch_shift = QDoubleSpinBox()
        f_pitch_shift.setRange(-36, 36)
        f_pitch_shift.setValue(0.0)
        f_pitch_shift.setDecimals(6)
        f_time_gridlayout.addWidget(f_pitch_shift, 10, 1)

        f_time_gridlayout.addWidget(QLabel(_("Stretch:")), 5, 0)
        f_timestretch_amt = QDoubleSpinBox()
        f_timestretch_amt.setRange(0.2, 4.0)
        f_timestretch_amt.setDecimals(6)
        f_timestretch_amt.setSingleStep(0.1)
        f_timestretch_amt.setValue(1.0)
        f_time_gridlayout.addWidget(f_timestretch_amt, 5, 1)
        f_time_gridlayout.addWidget(QLabel(_("Algorithm:")), 0, 0)
        f_algo_combobox = QComboBox()

        f_time_gridlayout.addWidget(f_algo_combobox, 0, 1)

        rubberband_groupbox = QGroupBox(_("Rubberband Options"))
        f_layout.addWidget(rubberband_groupbox)
        rubberband_groupbox_layout = QGridLayout(rubberband_groupbox)
        rubberband_groupbox_layout.addWidget(QLabel(_("Crispness")), 12, 0)
        f_crispness_combobox = QComboBox()
        f_crispness_combobox.addItems(CRISPNESS_SETTINGS)
        f_crispness_combobox.setCurrentIndex(5)
        rubberband_groupbox_layout.addWidget(f_crispness_combobox, 12, 1)
        f_preserve_formants_checkbox = QCheckBox("Preserve formants?")
        f_preserve_formants_checkbox.setChecked(True)
        rubberband_groupbox_layout.addWidget(
            f_preserve_formants_checkbox,
            18,
            1,
        )

        sbsms_groupbox = QGroupBox(_("SBSMS Options"))
        f_layout.addWidget(sbsms_groupbox)
        sbsms_groupbox_layout = QGridLayout(sbsms_groupbox)
        pitch_shift_end_checkbox = QCheckBox(_("Pitch Shift End"))
        sbsms_groupbox_layout.addWidget(pitch_shift_end_checkbox, 10, 0)
        pitch_shift_end = QDoubleSpinBox()
        sbsms_groupbox_layout.addWidget(pitch_shift_end, 10, 1)
        pitch_shift_end.setRange(-36, 36)
        pitch_shift_end.setValue(0.0)
        pitch_shift_end.setDecimals(6)
        timestretch_end_checkbox = QCheckBox(_("Time Stretch End"))
        sbsms_groupbox_layout.addWidget(timestretch_end_checkbox, 20, 0)
        timestretch_end = QDoubleSpinBox()
        sbsms_groupbox_layout.addWidget(timestretch_end, 20, 1)
        timestretch_end.setRange(0.2, 4.0)
        timestretch_end.setDecimals(6)
        timestretch_end.setSingleStep(0.1)
        timestretch_end.setValue(1.0)

        f_layout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        algorithms = ["Rubberband"]
        if util.SBSMS:
            algorithms.append('SBSMS')
        if util.PAULSTRETCH_PATH:
            algorithms.append('Paulstretch')
        f_algo_combobox.addItems(algorithms)
        f_algo_combobox.currentIndexChanged.connect(algo_changed)
        f_algo_combobox.setMinimumWidth(120)
        algo_changed()

        f_hlayout2 = QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)

        f_window.exec()

    def open_file_from_action(self, a_action):
        self.open_file(a_action.file_name)

    def show_offline_rendering_wait_window(self, a_file_name):
        f_file_name = "{}.finished".format(a_file_name)
        def ok_handler():
            constants.PROJECT.reload_audio_file(a_file_name)
            remove_path_from_painter_path_cache(a_file_name)
            if self.open_exported:
                self.open_file(a_file_name)
            f_window.close()

        def cancel_handler():
            f_window.close()

        def timeout_handler():
            if os.path.isfile(f_file_name):
                f_ok.setEnabled(True)
                f_timer.stop()
                f_time_label.setText(
                    _("Finished in {}").format(f_time_label.text()))
                os.remove(f_file_name)
            else:
                f_elapsed_time = time.time() - f_start_time
                f_time_label.setText(str(round(f_elapsed_time, 1)))

        f_start_time = time.time()
        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Rendering to .wav, please wait"))
        vlayout = QVBoxLayout()
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_window.setLayout(vlayout)
        f_time_label = QLabel("")
        f_time_label.setMinimumWidth(360)
        f_layout.addWidget(f_time_label, 1, 1)
        f_timer = QtCore.QTimer()
        f_timer.timeout.connect(timeout_handler)

        ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(ok_cancel_layout)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(ok_handler)
        f_ok.setEnabled(False)
        ok_cancel_layout.addWidget(f_ok)
        #f_cancel = QPushButton("Cancel")
        #f_cancel.pressed.connect(cancel_handler)
        #f_layout.addWidget(f_cancel, 9, 2)
        f_timer.start(100)
        f_window.exec()

    def on_export(self):
        if not self.history:
            QMessageBox.warning(self.widget, _("Error"), _("No file loaded"))
            return

        if glbl_shared.IS_PLAYING:
            return

        def ok_handler():
            if str(f_name.text()) == "":
                QMessageBox.warning(
                    f_window, _("Error"), _("Name cannot be empty"))
                return

            if f_copy_to_clipboard_checkbox.isChecked():
                self.copy_to_clipboard_checked = True
                f_clipboard = QApplication.clipboard()
                f_clipboard.setText(f_name.text())
            else:
                self.copy_to_clipboard_checked = False

            f_file_name = str(f_name.text())
            constants.WAVE_EDIT_PROJECT.ipc().we_export(f_file_name)
            self.last_offline_dir = os.path.dirname(f_file_name)
            self.open_exported = f_open_exported.isChecked()
            f_window.close()
            self.show_offline_rendering_wait_window(
                f_file_name,
            )

        def cancel_handler():
            f_window.close()

        def file_name_select():
            try:
                if not os.path.isdir(self.last_offline_dir):
                    self.last_offline_dir = HOME
                f_file_name, f_filter = QFileDialog.getSaveFileName(
                    MAIN_WINDOW,
                    _("Select a file name to save to..."),
                    self.last_offline_dir,
                    options=QFileDialog.Option.DontUseNativeDialog,
                )
                f_file_name = str(f_file_name)
                if not f_file_name is None and f_file_name != "":
                    if not f_file_name.endswith(".wav"):
                        f_file_name += ".wav"
                    if (
                        not f_file_name is None
                        and
                        not str(f_file_name) == ""
                    ):
                        f_name.setText(f_file_name)
                    self.last_offline_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                show_generic_exception(ex)

        def on_overwrite(a_val=None):
            f_name.setText(self.file_lineedit.text())

        # Force the plugin state to be saved to disk first if it changed
        PLUGIN_RACK.save_callback()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Render"))
        vlayout = QVBoxLayout()
        f_layout = QGridLayout()
        vlayout.addLayout(f_layout)
        f_window.setLayout(vlayout)

        f_name = QLineEdit()
        f_name.setToolTip('The path to the new file to create')
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(360)
        f_layout.addWidget(QLabel(_("File Name:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QPushButton(_("Select"))
        f_select_file.setToolTip(
            'Open a file browser dialog to select the new file to create'
        )
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_overwrite_button = QPushButton("Overwrite\nFile")
        f_overwrite_button.setToolTip(
            'Overwrite the existing file.  This button populates the current '
            'file name into the File Name field'
        )
        f_layout.addWidget(f_overwrite_button, 3, 0)
        f_overwrite_button.pressed.connect(on_overwrite)

        f_layout.addWidget(QLabel(sg_strings.export_format), 3, 1)
        f_copy_to_clipboard_checkbox = QCheckBox(
            _("Copy export path to clipboard?"),
        )
        f_copy_to_clipboard_checkbox.setToolTip(
            'Useful for right-click pasting back into the audio sequencer'
        )
        f_copy_to_clipboard_checkbox.setChecked(self.copy_to_clipboard_checked)
        f_layout.addWidget(f_copy_to_clipboard_checkbox, 4, 1)
        f_open_exported = QCheckBox("Open exported item?")
        f_open_exported.setToolTip(
            'Open the exported audio file into the wave editor when finished'
        )
        f_open_exported.setChecked(self.open_exported)
        f_layout.addWidget(f_open_exported, 6, 1)
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
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        vlayout.addLayout(f_ok_layout)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_layout.addWidget(f_cancel)
        f_window.exec()


    def on_reload(self):
        pass

    def vol_changed(self, a_val=None):
        f_result = round(self.vol_slider.value()  * 0.1, 1)
        self.marker_callback()
        self.vol_label.setText("{}dB".format(f_result))

    def on_preview(self):
        f_list = self.file_browser.files_selected()
        if f_list:
            constants.IPC.preview_audio(f_list[0])

    def on_stop_preview(self):
        constants.IPC.stop_preview()

    def on_file_open(self):
        if glbl_shared.IS_PLAYING:
            return
        f_file = self.file_browser.files_selected()
        if not f_file:
            return
        f_file_str = f_file[0]
        self.open_file(f_file_str)

    def copy_file_to_clipboard(self):
        f_clipboard = QApplication.clipboard()
        f_clipboard.setText(str(self.file_lineedit.text()))

    def open_file_from_clipboard(self):
        if glbl_shared.IS_PLAYING:
            return
        f_clipboard = QApplication.clipboard()
        f_text = str(f_clipboard.text()).strip()
        if len(f_text) < 1000 and os.path.isfile(f_text):
            self.open_file(f_text)
        else:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("No file path in the clipboard"))

    def open_file(self, a_file):
        f_file = str(a_file)
        if not os.path.exists(f_file):
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _("{} does not exist").format(f_file),
            )
            return
        self.file_name = f_file
        glbl_shared.APP.setOverrideCursor(
            QtCore.Qt.CursorShape.WaitCursor,
        )
        self.clear_sample_graph()
        self.current_file = f_file
        self.file_lineedit.setText(f_file)
        self.set_sample_graph(f_file)
        self.duration = float(
            self.graph_object.frame_count,
        ) / float(
            self.graph_object.sample_rate,
        )
        if f_file in self.history:
            self.history.remove(f_file)
        self.history.append(f_file)
        f_menu = QMenu(self.history_button)
        f_menu.triggered.connect(self.open_file_from_action)
        for f_path in reversed(self.history):
            f_action = f_menu.addAction(f_path)
            f_action.file_name = f_path
        self.history_button.setMenu(f_menu)
        constants.WAVE_EDIT_PROJECT.ipc().ab_open(
            constants.PROJECT.get_wav_uid_by_name(a_file, a_cp=False),
        )
        self.marker_callback()
        glbl_shared.APP.restoreOverrideCursor()
        self.vol_slider.setEnabled(True)

    def get_audio_item(self, a_uid=0):
        f_start = self.sample_graph.start_marker.value
        f_end = self.sample_graph.end_marker.value
        f_diff = f_end - f_start
        f_diff = clip_value(f_diff, 0.1, 1000.0)
        f_fade_in = ((self.sample_graph.fade_in_marker.value - f_start) /
            f_diff) * 1000.0
        f_fade_out = 1000.0 - (((f_end -
            self.sample_graph.fade_out_marker.value) / f_diff) * 1000.0)

        return audio_item(
            a_uid, a_sample_start=f_start, a_sample_end=f_end,
            a_vol=self.vol_slider.value() * 0.1,
            a_fade_in=f_fade_in, a_fade_out=f_fade_out,
            a_fadein_vol=self.fade_in_start.value(),
            a_fadeout_vol=self.fade_out_end.value())

    def set_audio_item(self, a_item):
        self.callbacks_enabled = False
        self.sample_graph.start_marker.set_value(a_item.sample_start)
        self.sample_graph.end_marker.set_value(a_item.sample_end)
        f_start = self.sample_graph.start_marker.value
        f_end = self.sample_graph.end_marker.value
        f_diff = f_end - f_start
        f_diff = clip_value(f_diff, 0.1, 1000.0)
        f_fade_in = (f_diff * (a_item.fade_in / 1000.0)) + f_start
        f_fade_out = (f_diff * (a_item.fade_out / 1000.0)) + f_start
        self.sample_graph.fade_in_marker.set_value(f_fade_in)
        self.sample_graph.fade_out_marker.set_value(f_fade_out)
        self.vol_slider.setValue(int(a_item.vol * 10.0))
        self.fade_in_start.setValue(a_item.fadein_vol)
        self.fade_out_end.setValue(a_item.fadeout_vol)
        self.callbacks_enabled = True
        self.marker_callback()

    def marker_callback(self, a_val=None):
        if self.callbacks_enabled:
            item = self.get_audio_item()
            constants.WAVE_EDIT_PROJECT.ipc().we_set(f"0|{item}")
            if hasattr(self.sample_graph, 'start_marker'):
                start = self.sample_graph.start_marker.value
                self.set_time_label(start * 0.001, True)

    def set_playback_cursor(self, a_pos):
        if self.playback_cursor is not None:
            self.playback_cursor.setPos(
                a_pos * widgets.AUDIO_ITEM_SCENE_WIDTH, 0.0)
        self.set_time_label(a_pos)

    def set_time_label(self, a_value, a_override=False):
        if self.history and (a_override or self.time_label_enabled):
            f_seconds = self.duration * a_value
            f_minutes = int(f_seconds * self.sixty_recip)
            f_seconds %= 60.0
            f_tenths = round(f_seconds - float(int(f_seconds)), 1)
            f_seconds = str(int(f_seconds)).zfill(2)
            glbl_shared.TRANSPORT.set_time("{}:{}.{}".format(
                f_minutes, f_seconds, str(f_tenths)[2]))

    def on_play(self):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(False)
        self.time_label_enabled = True
        self.playback_cursor = self.sample_graph.scene.addLine(
            self.sample_graph.start_marker.line.line(),
            self.sample_graph.start_marker.line.pen(),
        )

    def on_stop(self):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(True)
        if self.playback_cursor is not None:
            #self.sample_graph.scene.removeItem(self.playback_cursor)
            self.playback_cursor = None
        self.time_label_enabled = False
        if self.history:
            self.set_time_label(
                self.sample_graph.start_marker.value * 0.001, True)
        if self.graph_object is not None:
            self.sample_graph.redraw_item(
                self.sample_graph.start_marker.value,
                self.sample_graph.end_marker.value,
                self.sample_graph.fade_in_marker.value,
                self.sample_graph.fade_out_marker.value)

    def set_sample_graph(self, a_file_name):
        self.graph_object = constants.PROJECT.get_sample_graph_by_name(
            a_file_name,
            a_cp=False,
        )
        self.sample_graph.draw_item(
            self.graph_object,
            0.0,
            1000.0,
            0.0,
            1000.0,
        )

    def clear_sample_graph(self):
        self.sample_graph.clear_drawn_items()

    def clear(self):
        self.clear_sample_graph()
        self.file_lineedit.setText("")


def global_close_all():
    global OPEN_ITEM_UIDS, AUDIO_ITEMS_TO_DROP
    WAVE_EDITOR.clear()

#Opens or creates a new project
def global_open_project(a_project_file):
    global TRACK_NAMES, PLUGIN_RACK
    constants.WAVE_EDIT_PROJECT = WaveEditProject(WITH_AUDIO)
    constants.WAVE_EDIT_PROJECT.suppress_updates = True
    constants.WAVE_EDIT_PROJECT.open_project(a_project_file, False)
    WAVE_EDITOR.last_offline_dir = constants.PROJECT.user_folder
    constants.WAVE_EDIT_PROJECT.suppress_updates = False
    MAIN_WINDOW.last_offline_dir = constants.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.load()
    WAVE_EDITOR.open_project()
    TRANSPORT.open_project()
    PLUGIN_RACK = PluginRack(
        constants.WAVE_EDIT_PROJECT,
        0,
        PluginSettingsWaveEditor,
    )
    MAIN_WINDOW.insertTab(
        1,
        PLUGIN_RACK.widget,
        _("Plugin Rack"),
    )


def global_new_project(a_project_file):
    global PLUGIN_RACK
    constants.WAVE_EDIT_PROJECT = WaveEditProject(WITH_AUDIO)
    constants.WAVE_EDIT_PROJECT.new_project(a_project_file)
    WAVE_EDITOR.last_offline_dir = constants.PROJECT.user_folder
    MAIN_WINDOW.last_offline_dir = constants.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.load()
    WAVE_EDITOR.open_project()
    PLUGIN_RACK = PluginRack(
        constants.WAVE_EDIT_PROJECT,
        0,
        PluginSettingsWaveEditor,
    )
    MAIN_WINDOW.insertTab(
        1,
        PLUGIN_RACK.widget,
        _("Plugin Rack"),
    )

def on_ready():
    if WAVE_EDITOR.file_name:
        WAVE_EDITOR.open_file(WAVE_EDITOR.file_name)

def active_audio_pool_uids():
    result = constants.WAVE_EDIT_PROJECT.get_plugin_audio_pool_uids()
    if WAVE_EDITOR.file_name:
        result.add(
            constants.PROJECT.get_wav_uid_by_name(
                WAVE_EDITOR.file_name,
                a_cp=False,
            )
        )
    return result

constants.WAVE_EDIT_PROJECT = WaveEditProject(True)

ALL_PEAK_METERS = {}

WAVE_EDITOR = WaveEditorWidget()
TRANSPORT = TransportWidget()
MAIN_WINDOW = MainWindow()

CLOSE_ENGINE_ON_RENDER = False

PLUGIN_RACK = None

def init():
    pass
