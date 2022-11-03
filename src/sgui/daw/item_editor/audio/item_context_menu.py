from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.sgqt import *

from sglib.lib import strings as sg_strings, util
from sglib.lib.translate import _
from . import _shared
from .fade_vol_dialog import FadeVolDialogWidget
from .time_pitch_dialog import TimePitchDialogWidget
from sglib import constants
from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui.daw.lib import item as item_lib
import shutil


LAST_AUDIO_ITEM_DIR = HOME
CURRENT_ITEM = None

def show(current_item):
    global CURRENT_ITEM
    CURRENT_ITEM = current_item
    f_CURRENT_AUDIO_ITEM_INDEX = _shared.CURRENT_AUDIO_ITEM_INDEX
    _shared.CURRENT_AUDIO_ITEM_INDEX = CURRENT_ITEM.track_num
    f_menu = QMenu(shared.MAIN_WINDOW)

    shared.AUDIO_SEQ.context_menu_enabled = False

    f_file_menu = f_menu.addMenu(_("File"))
    f_save_a_copy_action = QAction("Save a Copy...", f_file_menu)
    f_file_menu.addAction(f_save_a_copy_action)
    f_save_a_copy_action.setToolTip('Save a new copy of this audio file')
    f_save_a_copy_action.triggered.connect(save_a_copy)

    f_open_folder_action = QAction(_("Open File in Browser"), f_file_menu)
    f_file_menu.addAction(f_open_folder_action)
    f_open_folder_action.setToolTip(
        'Open in the file browser the folder that this audio file is in'
    )
    f_open_folder_action.triggered.connect(open_item_folder)

    f_wave_editor_action = QAction(_("Open in Wave Editor"), f_file_menu)
    f_wave_editor_action.setToolTip(
        'Open this audio file in the Stargate built-in Wave Editor'
    )
    f_file_menu.addAction(f_wave_editor_action)
    f_wave_editor_action.triggered.connect(open_in_wave_editor)

    f_copy_file_path_action = QAction(
        _("Copy File Path to Clipboard"),
        f_file_menu,
    )
    f_copy_file_path_action.setToolTip(
        'Copy the full path to this audio file to the system clipboard'
    )
    f_file_menu.addAction(f_copy_file_path_action)
    f_copy_file_path_action.triggered.connect(
        copy_file_path_to_clipboard,
    )

    f_select_instance_action = QAction(
        _("Select All Instances of This File"),
        f_file_menu,
    )
    f_file_menu.addAction(f_select_instance_action)
    f_select_instance_action.setToolTip(
        'Select all instances of this audio file in this item.  '
        'Useful for performing actions on every instance of this file'
    )
    f_select_instance_action.triggered.connect(select_file_instance)

    f_file_menu.addSeparator()

    f_replace_action = QAction(
        _("Replace with Path in Clipboard"),
        f_file_menu,
    )
    f_file_menu.addAction(f_replace_action)
    f_replace_action.setToolTip(
        'Replace this file with the file path in the system clipboard.  '
        'You must copy the full path to a valid audio file of a supported '
        'type before using this'
    )
    f_replace_action.triggered.connect(replace_with_path_in_clipboard)

    f_properties_menu = f_menu.addMenu(_("Properties"))

    f_ts_mode_menu = f_properties_menu.addMenu("Timestretch Mode")
    f_ts_mode_menu.triggered.connect(ts_mode_menu_triggered)

    f_ts_modes = {
        x.audio_item.time_stretch_mode
        for x in shared.AUDIO_SEQ.get_selected()
    }

    for f_ts_mode in TIMESTRETCH_MODES:
        f_index = util.TIMESTRETCH_INDEXES[f_ts_mode]
        f_action = QAction(f_ts_mode, f_ts_mode_menu)
        f_action.setToolTip(sg_strings.timestretch_modes[f_index])
        f_ts_mode_menu.addAction(f_action)
        f_action.algo_name = f_ts_mode
        if len(f_ts_modes) == 1 and f_index in f_ts_modes:
            f_action.setCheckable(True)
            f_action.setChecked(True)

    if len(f_ts_modes) == 1 and [x for x in (3, 4) if x in f_ts_modes]:
        f_crisp_menu = f_properties_menu.addMenu("Crispness")
        f_crisp_menu.triggered.connect(crisp_menu_triggered)
        f_crisp_settings = {
            x.audio_item.crispness
            for x in shared.AUDIO_SEQ.get_selected()
        }
        for f_crisp_mode, f_index in zip(
            CRISPNESS_SETTINGS,
            range(len(CRISPNESS_SETTINGS))
        ):
            f_action = QAction(f_crisp_mode, f_crisp_menu)
            f_action.setToolTip(
                'Crispness parameters for the Rubberband time stretching '
                'library.  See the Rubberband documentation for more info'
            )
            f_crisp_menu.addAction(f_action)
            f_action.crisp_mode = f_crisp_mode
            if (
                len(f_crisp_settings) == 1
                and
                f_index in f_crisp_settings
            ):
                f_action.setCheckable(True)
                f_action.setChecked(True)

    f_output_modes = {
        x.audio_item.output_track
        for x in shared.AUDIO_SEQ.get_selected()
    }

    f_output_menu = f_properties_menu.addMenu(_("Output"))
    f_output_menu.triggered.connect(output_mode_triggered)
    for f_i, f_name, tooltip in zip(
        range(3),
        [_("Normal"), _("Sidechain"), _("Both")],
        (
            'Output to the normal audio channel',
            'Output to the sidechain audio channel',
            (
                'Output to normal and sidechain channels at the same time.  '
                'Note that this will cause a sound to mute itself when '
                'using a sidechain compressor'
            ),
        ),
    ):
        f_action = QAction(f_name, f_output_menu)
        f_output_menu.addAction(f_action)
        f_action.setToolTip(tooltip)
        f_action.output_val = f_i
        if len(f_output_modes) == 1 and f_i in f_output_modes:
            f_action.setCheckable(True)
            f_action.setChecked(True)

    f_volume_action = QAction(_("Volume..."), f_properties_menu)
    f_properties_menu.addAction(f_volume_action)
    f_volume_action.setToolTip(
        'Change the volume of the audio item.  You can also use CTRL+ALT+drag '
        'up and down to change volume of one or more audio items, and '
        'CTRL+SHIFT+drag to change for all instances of the file'
    )
    f_volume_action.triggered.connect(volume_dialog)

    f_normalize_action = QAction(_("Normalize..."), f_properties_menu)
    f_properties_menu.addAction(f_normalize_action)
    f_normalize_action.setToolTip(
        'Normalize audio items to a given level.  Note that this is '
        'pre-effects, using per-audio-item or per-file effects may '
        'change the volume level'
    )
    f_normalize_action.triggered.connect(normalize_dialog)

    f_reset_fades_action = QAction(_("Reset Fades"), f_properties_menu)
    f_properties_menu.addAction(f_reset_fades_action)
    f_reset_fades_action.setToolTip(
        'Reset the fade in and fade out handles to their default position '
        'of no fade in or out'
    )
    f_reset_fades_action.triggered.connect(reset_fades)

    f_reset_end_action = QAction(_("Reset Ends"), f_properties_menu)
    f_properties_menu.addAction(f_reset_end_action)
    f_reset_end_action.setToolTip(
        'Reset the end of the audio item to be the full length of the audio '
        'file.  Note that it will still be clipped by the length of the item.'
    )
    f_reset_end_action.triggered.connect(reset_end)

    f_move_to_end_action = QAction(_("Move to Item End"), f_properties_menu)
    f_properties_menu.addAction(f_move_to_end_action)
    f_move_to_end_action.setToolTip(
        'Move this audio item to the end of the sequencer item'
    )
    f_move_to_end_action.triggered.connect(move_to_item_end)

    f_reverse_action = QAction(_("Reverse/Unreverse"), f_properties_menu)
    f_properties_menu.addAction(f_reverse_action)
    f_reverse_action.setToolTip(
        'Toggle normal playback with playing the item backwards, For example '
        'turning a cymbal crash into a rising sound'
    )
    f_reverse_action.triggered.connect(_reverse)

    f_time_pitch_action = QAction(_("Time/Pitch..."), f_properties_menu)
    f_properties_menu.addAction(f_time_pitch_action)
    f_time_pitch_action.setToolTip(
        'Open the time stretching and pitchshifting dialog'
    )
    f_time_pitch_action.triggered.connect(time_pitch_dialog)

    f_fade_vol_action = QAction(_("Fade Volume..."), f_properties_menu)
    f_properties_menu.addAction(f_fade_vol_action)
    f_fade_vol_action.setToolTip(
        'Set the volume levels of the fade-in and fade-out handles.  This '
        'will affect how quickly a sound fades in or out'
    )
    f_fade_vol_action.triggered.connect(fade_vol_dialog)

    f_paif_menu = f_menu.addMenu(_("Effects"))

    f_paif_file_menu = f_paif_menu.addMenu(_("Per-File"))

    f_edit_papifx_action = QAction(_("Edit"), f_paif_file_menu)
    f_paif_file_menu.addAction(f_edit_papifx_action)
    f_edit_papifx_action.setToolTip(
        'Edit the per-file effects for this audio file.  This will affect '
        'all instances of this file in all sequencer items'
    )
    f_edit_papifx_action.triggered.connect(edit_papifx)

    f_paif_copy = QAction(_("Copy"), f_paif_file_menu)
    f_paif_file_menu.addAction(f_paif_copy)
    f_paif_copy.setToolTip(
        'Copy the per-file effects for this audio file to the clipboard, '
        'use this for duplicating one file\'s effects to another'
    )
    f_paif_copy.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_papifx_copy,
    )

    f_paif_paste = QAction(_("Paste"), f_paif_file_menu)
    f_paif_file_menu.addAction(f_paif_paste)
    f_paif_paste.setToolTip(
        'Paste per-file effects to this audio file.  You must already have '
        'copied effects to the clipboard before doing this.'
    )
    f_paif_paste.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_papifx_paste,
    )

    f_paif_clear = QAction(_("Clear"), f_paif_file_menu)
    f_paif_file_menu.addAction(f_paif_clear)
    f_paif_clear.setToolTip(
        'Clear all per-file effects from this audio file, there will be no '
        'effects after running this action'
    )
    f_paif_clear.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_papifx_clear,
    )

    f_paif_item_menu = f_paif_menu.addMenu(_("Per-Item"))

    f_edit_paif_action = QAction(_("Edit"), f_paif_item_menu)
    f_paif_item_menu.addAction(f_edit_paif_action)
    f_edit_paif_action.setToolTip(
        'Edit the per-audio-item effects for this audio item.  This will '
        'only affect this instance of this file in this sequencer items'
    )
    f_edit_paif_action.triggered.connect(edit_paif)

    f_paif_copy = QAction(_("Copy"), f_paif_item_menu)
    f_paif_item_menu.addAction(f_paif_copy)
    f_paif_copy.setToolTip(
        'Copy the per-audio-item effects for this audio item to the '
        'clipboard, use this for duplicating one item\'s effects to another'
    )
    f_paif_copy.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_paifx_copy,
    )

    f_paif_paste = QAction(_("Paste"), f_paif_item_menu)
    f_paif_item_menu.addAction(f_paif_paste)
    f_paif_paste.setToolTip(
        'Paste per-audio-item effects to this audio item.  You must already '
        'have copied effects to the clipboard before doing this.'
    )
    f_paif_paste.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_paifx_paste,
    )

    f_paif_clear = QAction(_("Clear"), f_paif_item_menu)
    f_paif_item_menu.addAction(f_paif_clear)
    f_paif_clear.setToolTip(
        'Clear all per-audio-item effects from this audio item, there will '
        'be no effects after running this action'
    )
    f_paif_clear.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_paifx_clear,
    )

    f_menu.exec(QCursor.pos())
    _shared.CURRENT_AUDIO_ITEM_INDEX = f_CURRENT_AUDIO_ITEM_INDEX

def save_a_copy():
    global LAST_AUDIO_ITEM_DIR
    f_file, f_filter = QFileDialog.getSaveFileName(
        parent=shared.MAIN_WINDOW,
        caption=_('Save audio item as .wav'),
        directory=LAST_AUDIO_ITEM_DIR,
        options=QFileDialog.Option.DontUseNativeDialog,
    )
    if not f_file is None and not str(f_file) == "":
        f_file = str(f_file)
        if not f_file.endswith(".wav"):
            f_file += ".wav"
        LAST_AUDIO_ITEM_DIR = os.path.dirname(f_file)
        f_orig_path = constants.PROJECT.get_wav_name_by_uid(
            CURRENT_ITEM.audio_item.uid,
        )
        shutil.copy(f_orig_path, f_file)

def open_item_folder():
    f_path = constants.PROJECT.get_wav_name_by_uid(
        CURRENT_ITEM.audio_item.uid,
    )
    shared.AUDIO_SEQ_WIDGET.open_file_in_browser(f_path)

def open_in_wave_editor():
    f_path = CURRENT_ITEM.get_file_path()
    glbl_shared.MAIN_WINDOW.open_in_wave_editor(f_path)

def copy_file_path_to_clipboard():
    f_path = CURRENT_ITEM.get_file_path()
    f_clipboard = QApplication.clipboard()
    f_clipboard.setText(f_path)

def select_file_instance():
    LOG.info(f"{_shared}")
    shared.AUDIO_SEQ.scene.clearSelection()
    f_uid = CURRENT_ITEM.audio_item.uid
    for f_item in shared.AUDIO_SEQ.audio_items:
        if f_item.audio_item.uid == f_uid:
            f_item.setSelected(True)

def replace_with_path_in_clipboard():
    f_path = _shared.global_get_audio_file_from_clipboard()
    if f_path is not None:
        CURRENT_ITEM.audio_item.uid = \
            constants.PROJECT.get_wav_uid_by_name(f_path)
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        constants.DAW_PROJECT.commit(_("Replace audio item"))
        global_open_audio_items(True)

def ts_mode_menu_triggered(a_action):
    f_index = TIMESTRETCH_INDEXES[a_action.algo_name]
    f_list = [x.audio_item for x in shared.AUDIO_SEQ.get_selected()]
    for f_item in f_list:
        f_item.time_stretch_mode = f_index
    timestretch_items(f_list)

def output_mode_triggered(a_action):
    f_list = shared.AUDIO_SEQ.get_selected()
    for f_item in f_list:
        f_item.audio_item.output_track = a_action.output_val
    item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
    constants.DAW_PROJECT.commit(_("Set audio items output mode"))
    global_open_audio_items(True)

def volume_dialog():
    def on_ok():
        f_val = round(f_db_spinbox.value(), 1)
        for f_item in shared.AUDIO_SEQ.get_selected():
            f_item.audio_item.vol = f_val
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        constants.DAW_PROJECT.commit(_("Normalize audio items"))
        global_open_audio_items(True)
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QDialog(shared.MAIN_WINDOW)
    f_window.f_result = None
    f_window.setWindowTitle(_("Volume"))
    f_window.setFixedSize(150, 90)
    f_layout = QVBoxLayout()
    f_window.setLayout(f_layout)
    f_hlayout = QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_hlayout.addWidget(QLabel("dB"))
    f_db_spinbox = QDoubleSpinBox()
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setDecimals(1)
    f_db_spinbox.setRange(-24, 24)
    f_vols = {
        float(x.audio_item.vol)
        for x in shared.AUDIO_SEQ.get_selected()
    }
    if len(f_vols) == 1:
        f_db_spinbox.setValue(f_vols.pop())
    else:
        f_db_spinbox.setValue(0.)
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

def normalize_dialog():
    f_val = _normalize_dialog()
    if f_val is None:
        return
    f_save = False
    audio_pool = constants.PROJECT.get_audio_pool()
    audio_pool_by_uid = audio_pool.by_uid()
    ap_entries = set()
    for f_item in shared.AUDIO_SEQ.get_selected():
        f_save = True
        entry = f_item.normalize(f_val, audio_pool_by_uid)
        ap_entries.add(entry)
    if f_save:
        constants.PROJECT.save_audio_pool(audio_pool)
        for entry in ap_entries:
            constants.IPC.audio_pool_entry_volume(
                entry.uid,
                entry.volume,
            )
        constants.DAW_PROJECT.commit(_("Normalize audio items"))
        global_open_audio_items(True)

def _normalize_dialog():
    def on_ok():
        f_window.f_result = f_db_spinbox.value()
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QDialog(shared.MAIN_WINDOW)
    f_window.f_result = None
    f_window.setWindowTitle(_("Normalize"))
    f_window.setFixedSize(150, 90)
    f_layout = QVBoxLayout()
    f_window.setLayout(f_layout)
    f_hlayout = QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_hlayout.addWidget(QLabel("dB"))
    f_db_spinbox = QDoubleSpinBox()
    f_db_spinbox.setDecimals(1)
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setRange(-18, 0)
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

def reset_fades():
    f_list = shared.AUDIO_SEQ.get_selected()
    if f_list:
        for f_item in f_list:
            f_item.audio_item.fade_in = 0.0
            f_item.audio_item.fade_out = 999.0
        item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        constants.DAW_PROJECT.commit(_("Reset audio item fades"))
        global_open_audio_items(True)

def reset_end():
    f_list = shared.AUDIO_SEQ.get_selected()
    for f_item in f_list:
        f_item.audio_item.sample_start = 0.0
        f_item.audio_item.sample_end = 1000.0
        CURRENT_ITEM.draw()
        CURRENT_ITEM.clip_at_sequence_end()
    item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
    constants.DAW_PROJECT.commit(_("Reset sample ends for audio item(s)"))
    global_open_audio_items()

def move_to_item_end():
    f_list = shared.AUDIO_SEQ.get_selected()
    if f_list:
        f_global_tempo = shared.CURRENT_SEQUENCE.get_tempo_at_pos(
            shared.CURRENT_ITEM_REF.start_beat,
        )
        for f_item in f_list:
            f_item.audio_item.clip_at_sequence_end(
                shared.CURRENT_ITEM_REF.length_beats,
                f_global_tempo,
                f_item.graph_object.length_in_seconds,
                False,
            )
        item_lib.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        constants.DAW_PROJECT.commit(_("Move audio item(s) to sequence end"))
        global_open_audio_items(True)

def _reverse():
    f_list = shared.AUDIO_SEQ.get_selected()
    for f_item in f_list:
        f_item.audio_item.reversed = not f_item.audio_item.reversed
        # Invert the start/end and fades so that the same section stays in
        # the sequencer exactly as it is, just reversed
        start = f_item.audio_item.sample_start
        end = f_item.audio_item.sample_end
        f_item.audio_item.sample_start = 1000. - end
        f_item.audio_item.sample_end = 1000. - start

        fade_in = f_item.audio_item.fade_in
        fade_out = f_item.audio_item.fade_out
        f_item.audio_item.fade_in = 999. - fade_out
        f_item.audio_item.fade_out = 1000. - fade_in - 1.

    item_lib.save_item(
        shared.CURRENT_ITEM_NAME,
        shared.CURRENT_ITEM,
    )
    constants.DAW_PROJECT.commit(_("Toggle audio items reversed"))
    global_open_audio_items(True)

def time_pitch_dialog():
    f_dialog = TimePitchDialogWidget(CURRENT_ITEM.audio_item)
    f_dialog.widget.exec()

def fade_vol_dialog():
    f_dialog = FadeVolDialogWidget(CURRENT_ITEM.audio_item)
    f_dialog.widget.exec()

def edit_papifx():
    CURRENT_ITEM.setSelected(True)
    shared.AUDIO_SEQ_WIDGET.folders_tab_widget.setCurrentIndex(2)

def edit_paif():
    CURRENT_ITEM.setSelected(True)
    shared.AUDIO_SEQ_WIDGET.folders_tab_widget.setCurrentIndex(3)

def crisp_menu_triggered(a_action):
    f_index = CRISPNESS_SETTINGS.index(a_action.crisp_mode)
    f_list = [
        x.audio_item
        for x in shared.AUDIO_SEQ.get_selected()
        if x.audio_item.time_stretch_mode in (3, 4)
    ]
    for f_item in f_list:
        f_item.crispness = f_index
    timestretch_items(f_list)

def timestretch_items(a_list):
    for f_item in a_list:
        if f_item.time_stretch_mode >= 3:
            try:
                constants.PROJECT.timestretch_audio_item(f_item)
            except FileNotFoundError as ex:
                QMessageBox.warning(
                    glbl_shared.MAIN_WINDOW,
                    _("Error"),
                    str(ex),
                )
                global_open_audio_items(True)
                return

    constants.PROJECT.save_stretch_dicts()

    for f_audio_item in shared.AUDIO_SEQ.get_selected():
        f_new_graph = constants.PROJECT.get_sample_graph_by_uid(
            f_audio_item.audio_item.uid,
        )
        f_audio_item.audio_item.clip_at_sequence_end(
            get_current_sequence_length(),
            shared.CURRENT_SEQUENCE.get_tempo_at_pos(
                shared.CURRENT_ITEM_REF.start_beat,
            ),
            f_new_graph.length_in_seconds,
        )

    item_lib.save_item(
        shared.CURRENT_ITEM_NAME,
        shared.CURRENT_ITEM,
    )
    constants.DAW_PROJECT.commit(
        _("Change timestretch mode for audio item(s)")
    )
    global_open_audio_items()

