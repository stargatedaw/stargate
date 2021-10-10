#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

from sgui.plugins import *
from sgui.sgqt import *
from sgui.widgets import *
from sglib.lib.util import *

from . import *
from .filedragdrop import FileDragDropper
from .hardware import HardwareWidget, MidiDevicesDialog
from .item_editor.audio import (
    AudioItemSeq,
    AudioItemSeqWidget,
)
from .item_editor.automation import (
    AutomationEditor,
    AutomationEditorWidget,
)
from .item_editor.editor import ItemEditorWidget
from .item_editor.notes import (
    PianoRollEditor,
    PianoRollEditorWidget,
)
from .sequencer import (
    ItemSequencer,
    PlaylistWidget,
    SequencerWidget,
    TrackPanel,
)
from .transport import (
    MREC_EVENTS,
    TransportWidget,
)
from sglib import constants
from sglib.api.daw import api_project_notes
from sgui import plugins
from sgui import shared as glbl_shared
from sgui.daw import strings as daw_strings
from sgui.daw.lib import undo as undo_lib
from sglib.lib import *
from sglib.lib import strings as sg_strings
from sglib.lib.translate import _
from sglib.log import LOG

import datetime
import math
import os
import random
import shutil
import subprocess
import traceback


CLOSE_ENGINE_ON_RENDER = True

class MainWindow(QScrollArea):
    """ The main window for DAW-Next that contains all widgets
        except TransportWidget
    """
    def __init__(self):
        QScrollArea.__init__(self)
        self.first_offline_render = True
        self.last_offline_dir = HOME
        self.copy_to_clipboard_checked = False
        self.last_midi_dir = None

        self.setObjectName("plugin_ui")
        self.widget = QWidget()
        self.widget.setObjectName("plugin_ui")
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.widget.setLayout(self.main_layout)

        # Transport shortcuts (added here so they will work
        # when the transport is hidden)

        self.loop_mode_action = QAction(self)
        self.addAction(self.loop_mode_action)
        self.loop_mode_action.setShortcut(
            QKeySequence.fromString("CTRL+L"))
        self.loop_mode_action.triggered.connect(
            shared.TRANSPORT.toggle_loop_mode,
        )

        self.select_mode_action = QAction(self)
        self.addAction(self.select_mode_action)
        self.select_mode_action.setShortcut(QKeySequence.fromString("A"))
        self.select_mode_action.triggered.connect(
            shared.TRANSPORT.tool_select_clicked,
        )

        self.draw_mode_action = QAction(self)
        self.addAction(self.draw_mode_action)
        self.draw_mode_action.setShortcut(QKeySequence.fromString("S"))
        self.draw_mode_action.triggered.connect(
            shared.TRANSPORT.tool_draw_clicked)

        self.erase_mode_action = QAction(self)
        self.addAction(self.erase_mode_action)
        self.erase_mode_action.setShortcut(QKeySequence.fromString("D"))
        self.erase_mode_action.triggered.connect(
            shared.TRANSPORT.tool_erase_clicked)

        self.split_mode_action = QAction(self)
        self.addAction(self.split_mode_action)
        self.split_mode_action.setShortcut(QKeySequence.fromString("F"))
        self.split_mode_action.triggered.connect(
            shared.TRANSPORT.tool_split_clicked)

        #The tabs
        self.main_tabwidget = QTabWidget()
        self.main_layout.addWidget(self.main_tabwidget)

        # TODO: SG MISC: Move this to it's own class
        self.song_sequence_tab = QWidget()
        self.song_sequence_vlayout = QVBoxLayout()
        self.song_sequence_vlayout.setContentsMargins(1, 1, 1, 1)
        self.song_sequence_tab.setLayout(self.song_sequence_vlayout)
        self.sequencer_widget = QWidget()
        self.sequencer_vlayout = QVBoxLayout(self.sequencer_widget)
        self.sequencer_vlayout.setContentsMargins(1, 1, 1, 1)
        self.sequencer_vlayout.addWidget(self.song_sequence_tab)
        self.main_tabwidget.addTab(self.sequencer_widget, _("Sequencer"))

        self.song_sequence_vlayout.addWidget(shared.SEQ_WIDGET.widget)

        self.midi_scroll_area = QScrollArea()
        self.midi_scroll_area.setWidgetResizable(True)
        self.midi_scroll_widget = QWidget()
        self.midi_scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.midi_hlayout = QHBoxLayout(self.midi_scroll_widget)
        self.midi_hlayout.setContentsMargins(0, 0, 0, 0)
        self.midi_scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
        )
        self.midi_scroll_area.setWidget(self.midi_scroll_widget)
        self.midi_hlayout.addWidget(shared.TRACK_PANEL.tracks_widget)
        self.midi_hlayout.addWidget(shared.SEQUENCER)

        shared.PLAYLIST_EDITOR = PlaylistWidget()
        self.file_browser = FileDragDropper(util.is_audio_midi_file)
        self.file_browser.folders_tab_widget.insertTab(
            0,
            shared.PLAYLIST_EDITOR.parent,
            _("Songs"),
        )
        self.file_browser.folders_tab_widget.setCurrentIndex(0)
        self.file_browser.set_multiselect(True)
        self.file_browser.hsplitter.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.sequencer_vlayout.addWidget(self.file_browser.hsplitter)
        self.file_browser.hsplitter.insertWidget(0, self.midi_scroll_area)
        self.file_browser.hsplitter.setSizes([9999, 200])

        self.midi_scroll_area.scrollContentsBy = self.midi_scrollContentsBy
        self.vscrollbar = self.midi_scroll_area.verticalScrollBar()
        self.vscrollbar.sliderReleased.connect(self.vscrollbar_released)
        self.vscrollbar.setSingleStep(shared.SEQUENCE_EDITOR_TRACK_HEIGHT)

        self.main_tabwidget.addTab(
            shared.PLUGIN_RACK.widget,
            _("Plugin Rack"),
        )
        self.main_tabwidget.addTab(
            shared.ITEM_EDITOR.widget,
            _("Item Editor"),
        )

        self.automation_tab = QWidget()
        self.automation_tab.setObjectName("plugin_ui")

        self.main_tabwidget.addTab(
            shared.ROUTING_GRAPH_WIDGET,
            _("Routing"),
        )
        self.main_tabwidget.addTab(
            shared.MIXER_WIDGET.widget,
            _("Mixer"),
        )
        self.main_tabwidget.addTab(
            shared.HARDWARE_WIDGET,
            _("Hardware"),
        )

        self.notes_tab = ProjectNotes(
            self,
            api_project_notes.load,
            api_project_notes.save,
        )
        self.main_tabwidget.addTab(
            self.notes_tab.widget,
            _("Project Notes"),
        )

        self.main_tabwidget.currentChanged.connect(self.tab_changed)
        shared.DAW = self

    def open_project(self):
        """ Open an existing project in the widgets """
        # TODO: SG DEPRECATED: Use new files/folders
        MAIN_WINDOW.last_offline_dir = constants.PROJECT.user_folder
        MAIN_WINDOW.notes_tab.load()
        shared.PLAYLIST_EDITOR.open()

    def new_project(self):
        """ Open a new project in the widgets """
        # TODO: SG DEPRECATED: Use new files/folders
        self.last_offline_dir = constants.PROJECT.user_folder
        self.notes_tab.load()
        shared.PLAYLIST_EDITOR.open()

    def vscrollbar_released(self, a_val=None):
        # Avoid a bug where the bottom track is truncated
        if self.vscrollbar.value() == self.vscrollbar.maximum():
            return
        f_val = round(
            self.vscrollbar.value() /
            shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        ) * shared.SEQUENCE_EDITOR_TRACK_HEIGHT
        self.vscrollbar.setValue(int(f_val))

    def on_offline_render(self):
        def copy_cmd_args():
            f_run_cmd = [
                str(x) for x in (
                    "daw",
                    "'{}'".format(constants.DAW_PROJECT.project_folder),
                    "test.wav",
                    f_start_beat,
                    f_end_beat,
                    "44100",
                    512,
                    1,
                    0,
                    0,
                    constants.DAW_CURRENT_SEQUENCE_UID,
                )
            ]
            f_clipboard = QApplication.clipboard()
            f_clipboard.setText(" ".join(f_run_cmd))

        def ok_handler():
            if str(f_name.text()) == "":
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _("Name cannot be empty"),
                )
                return

            if f_copy_to_clipboard_checkbox.isChecked():
                self.copy_to_clipboard_checked = True
                f_clipboard = QApplication.clipboard()
                f_clipboard.setText(f_name.text())
            else:
                self.copy_to_clipboard_checked = False

            f_stem = 1 if f_stem_render_checkbox.isChecked() else 0
            f_out_file = f_name.text()
            f_fini = os.path.join(f_out_file, "finished") if f_stem else None
            f_samp_rate = f_sample_rate.currentText()
            f_buff_size = util.DEVICE_SETTINGS["bufferSize"]
            f_thread_count = 1 if util.IS_WINDOWS else \
                util.DEVICE_SETTINGS["threads"]

            self.last_offline_dir = os.path.dirname(str(f_name.text()))

            f_window.close()

            f_cmd = [
                str(x) for x in (
                    util.BIN_PATH,
                    "daw",
                    constants.DAW_PROJECT.project_folder,
                    f_out_file,
                    f_start_beat,
                    f_end_beat,
                    f_samp_rate,
                    f_buff_size,
                    f_thread_count,
                    util.USE_HUGEPAGES,
                    f_stem,
                    constants.DAW_CURRENT_SEQUENCE_UID,
                )
            ]
            LOG.info(f"Rendering {f_cmd} to '{f_out_file}'")
            glbl_shared.MAIN_WINDOW.show_offline_rendering_wait_window_v2(
                f_cmd,
                f_out_file,
                f_file_name=f_fini,
            )

            if f_stem:
                f_tracks = constants.DAW_PROJECT.get_tracks()
                for f_file in os.listdir(f_out_file):
                    f_track_num = f_file.split(".", 1)[0].zfill(3)
                    f_track_name = f_tracks.tracks[int(f_track_num)].name
                    f_new = "{}-{}.wav".format(f_track_num, f_track_name)
                    os.rename(
                        os.path.join(f_out_file, f_file),
                        os.path.join(f_out_file, f_new))

        def cancel_handler():
            f_window.close()

        def stem_check_changed(a_val=None):
            f_name.setText("")

        def file_name_select():
            if not os.path.isdir(self.last_offline_dir):
                self.last_offline_dir = HOME
            if f_stem_render_checkbox.isChecked():
                f_file = QFileDialog.getExistingDirectory(
                    MAIN_WINDOW,
                    _('Select an empty directory to render stems to'),
                    self.last_offline_dir,
                    (
                        QFileDialog.Option.ShowDirsOnly
                        |
                        QFileDialog.Option.DontUseNativeDialog
                    ),
                )
                if f_file and str(f_file):
                    if os.listdir(f_file):
                        QMessageBox.warning(
                            self, _("Error"),
                            _("The directory is not empty"))
                    else:
                        f_name.setText(f_file)
                        self.last_offline_dir = f_file
            else:
                f_file_name, f_filter = QFileDialog.getSaveFileName(
                    shared.MAIN_WINDOW,
                    _("Select a file name to save to..."),
                    self.last_offline_dir,
                    options=QFileDialog.Option.DontUseNativeDialog,
                )
                f_file_name = str(f_file_name)
                if f_file_name and str(f_file_name):
                    if not f_file_name.endswith(".wav"):
                        f_file_name += ".wav"
                    if f_file_name and str(f_file_name):
                        f_name.setText(f_file_name)
                    self.last_offline_dir = os.path.dirname(f_file_name)

        f_marker_pos = shared.SEQUENCER.get_loop_pos(a_warn=False)

        if not f_marker_pos:
            QMessageBox.warning(
                MAIN_WINDOW,
                _("Error"),
                _(
                    "You must set the region markers first by "
                    "right-clicking on the sequencer timeline.  "
                    "Only the region will be exported."
                ),
            )
            return

        # Force the plugin state to be saved to disk first if it changed
        shared.PLUGIN_RACK.tab_selected(False)

        f_start_beat, f_end_beat = f_marker_pos

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Offline Render"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_name = QLineEdit()
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(360)
        f_layout.addWidget(QLabel(_("File Name:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QPushButton(_("Select"))
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_sample_rate_hlayout = QHBoxLayout()
        f_layout.addLayout(f_sample_rate_hlayout, 3, 1)
        f_sample_rate_hlayout.addWidget(QLabel(_("Sample Rate")))
        f_sample_rate = QComboBox()
        f_sample_rate.setMinimumWidth(105)
        f_sample_rate.addItems([
            "44100",
            "48000",
            "88200",
            "96000",
            "192000",
            "384000",
            "768000",
            "1536000",
        ])

        try:
            f_sr_index = f_sample_rate.findText(
                util.DEVICE_SETTINGS["sampleRate"])
            f_sample_rate.setCurrentIndex(f_sr_index)
        except:
            pass

        f_sample_rate_hlayout.addWidget(f_sample_rate)

        f_stem_render_checkbox = QCheckBox(_("Stem Render"))
        f_sample_rate_hlayout.addWidget(f_stem_render_checkbox)
        f_stem_render_checkbox.stateChanged.connect(stem_check_changed)

        f_sample_rate_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        f_layout.addWidget(QLabel(
            _("File is exported to 32 bit .wav at the selected sample rate. "
            "\nYou can convert the format using "
            "Menu->Tools->MP3/Ogg Converter")),
            6, 1)
        f_copy_to_clipboard_checkbox = QCheckBox(
            _("Copy export path to clipboard?"),
        )
        f_copy_to_clipboard_checkbox.setChecked(self.copy_to_clipboard_checked)
        f_layout.addWidget(f_copy_to_clipboard_checkbox, 7, 1)
        f_ok_layout = QHBoxLayout()

        if util.IS_LINUX:
            f_debug_button = QPushButton(_("Copy cmd args"))
            f_debug_button.setToolTip(
                _("For developer use only")
            )
            f_ok_layout.addWidget(f_debug_button)
            f_debug_button.pressed.connect(copy_cmd_args)

        f_ok_layout.addItem(
            QSpacerItem(
                10,
                10,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
        )
        f_ok = QPushButton(_("OK"))
        f_ok.setMinimumWidth(75)
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 1)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.setMinimumWidth(75)
        f_cancel.pressed.connect(cancel_handler)
        f_ok_layout.addWidget(f_cancel)
        f_window.exec()

    def on_undo(self):
        if glbl_shared.IS_PLAYING or not self.check_tab_for_undo():
            return
        glbl_shared.APP.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        if undo_lib.undo():
            global_ui_refresh_callback()
            glbl_shared.APP.restoreOverrideCursor()
        else:
            glbl_shared.APP.restoreOverrideCursor()
            QMessageBox.warning(
                MAIN_WINDOW,
                "Error",
                "No more undo history left",
            )

    def on_redo(self):
        if glbl_shared.IS_PLAYING or not self.check_tab_for_undo():
            return
        glbl_shared.APP.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        if undo_lib.redo():
            shared.global_ui_refresh_callback()
            glbl_shared.APP.restoreOverrideCursor()
        else:
            glbl_shared.APP.restoreOverrideCursor()
            QMessageBox.warning(
                shared.MAIN_WINDOW,
                "Error",
                "Already at the latest commit",
            )

    def check_tab_for_undo(self):
        index = self.main_tabwidget.currentIndex()
        if index in (
            shared.TAB_ITEM_EDITOR,
            shared.TAB_ROUTING,
            shared.TAB_SEQUENCER,
        ):
            return True
        else:
            QMessageBox.warning(
                shared.MAIN_WINDOW, "Error",
                "Undo/redo only supported for the sequencer, item editor "
                "and routing tab.  Individual plugins have undo for each "
                "control by right-clicking and selecting the undo menu")
            return False

    def tab_changed(self):
        f_index = self.main_tabwidget.currentIndex()

        shared.TRANSPORT.tab_changed(f_index)

        constants.DAW_PROJECT.set_undo_context(f_index)
        if f_index == shared.TAB_SEQUENCER and not glbl_shared.IS_PLAYING:
            shared.SEQUENCER.open_sequence()
        elif f_index == shared.TAB_ITEM_EDITOR:
            shared.ITEM_EDITOR.tab_changed()
        elif f_index == shared.TAB_ROUTING:
            shared.ROUTING_GRAPH_WIDGET.draw_graph(
                constants.DAW_PROJECT.get_routing_graph(),
                shared.TRACK_NAMES,
            )
        elif f_index == shared.TAB_MIXER:
            global_open_mixer()

        shared.PLUGIN_RACK.tab_selected(f_index == shared.TAB_PLUGIN_RACK)
        QApplication.restoreOverrideCursor()

    def set_tooltips(self, a_on):
        if a_on:
            shared.ROUTING_GRAPH_WIDGET.setToolTip(sg_strings.routing_graph)
        else:
            shared.ROUTING_GRAPH_WIDGET.setToolTip("")

    def midi_scrollContentsBy(self, x, y):
        QScrollArea.scrollContentsBy(self.midi_scroll_area, x, y)
        f_y = self.midi_scroll_area.verticalScrollBar().value()
        shared.SEQUENCER.set_header_y_pos(f_y)

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
                    f_beat = float(a_val)
                    global_set_playback_pos(f_beat)
            elif a_key == "peak":
                global_update_peak_meters(a_val)
            elif a_key == "cc":
                f_track_num, f_cc, f_val = a_val.split("|")
                f_cc_dict[(f_track_num, f_cc)] = f_val
            elif a_key == "ui":
                f_plugin_uid, f_name, f_val = a_val.split("|", 2)
                f_ui_dict[(f_plugin_uid, f_name)] = f_val
            elif a_key == "mrec":
                MREC_EVENTS.append(a_val)
            elif a_key == "ne":
                f_state, f_note = a_val.split("|")
                shared.PIANO_ROLL_EDITOR.highlight_keys(f_state, f_note)
            elif a_key == "ml":
                glbl_shared.PLUGIN_UI_DICT.midi_learn_control[0].update_cc_map(
                    a_val, glbl_shared.PLUGIN_UI_DICT.midi_learn_control[1])
            elif a_key == "ready":
                glbl_shared.on_ready()
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
            f_track_num, f_cc = (int(x) for x in k)
            uids = []
            if f_track_num in shared.PLUGIN_RACK.plugin_racks:
                rack = shared.PLUGIN_RACK.plugin_racks[f_track_num]
                uids.extend(rack.get_plugin_uids())
            if f_track_num in shared.MIXER_WIDGET.tracks:
                track = shared.MIXER_WIDGET.tracks[f_track_num]
                uids.extend(track.get_plugin_uids())
            for f_plugin_uid in uids:
                if f_plugin_uid in glbl_shared.PLUGIN_UI_DICT:
                    glbl_shared.PLUGIN_UI_DICT[
                        f_plugin_uid].set_cc_val(f_cc, f_val)

    def prepare_to_quit(self):
        try:
            for f_widget in (
                shared.AUDIO_SEQ,
                shared.CC_EDITOR,
                shared.PB_EDITOR,
                shared.PIANO_ROLL_EDITOR,
                shared.ROUTING_GRAPH_WIDGET,
                shared.SEQUENCER,
            ):
                f_widget.prepare_to_quit()
        except Exception as ex:
            LOG.error("Exception raised while attempting to close DAW")
            LOG.exception(ex)

def init():
    global MAIN_WINDOW, TRANSPORT
    shared.ATM_SEQUENCE = DawAtmRegion()
    shared.SEQUENCER = ItemSequencer()
    shared.PB_EDITOR = AutomationEditor(a_is_cc=False)
    shared.CC_EDITOR = AutomationEditor()
    shared.CC_EDITOR_WIDGET = AutomationEditorWidget(shared.CC_EDITOR)

    shared.SEQ_WIDGET = SequencerWidget()
    shared.TRACK_PANEL = TrackPanel()

    shared.PIANO_ROLL_EDITOR = PianoRollEditor()
    shared.PIANO_ROLL_EDITOR_WIDGET = PianoRollEditorWidget()
    shared.AUDIO_SEQ = AudioItemSeq()
    shared.AUDIO_SEQ_WIDGET = AudioItemSeqWidget()
    shared.ITEM_EDITOR = ItemEditorWidget()
    shared.MIXER_WIDGET = plugins.MixerWidget(TRACK_COUNT_ALL)

    get_mixer_peak_meters()

    shared.MIDI_EDITORS = (
        shared.CC_EDITOR,
        shared.PB_EDITOR,
        shared.PIANO_ROLL_EDITOR,
    )

    shared.MIDI_DEVICES_DIALOG = MidiDevicesDialog()
    shared.HARDWARE_WIDGET = HardwareWidget()
    shared.TRANSPORT = TransportWidget()
    TRANSPORT = shared.TRANSPORT

    shared.ROUTING_GRAPH_WIDGET = widgets.RoutingGraphWidget(
        routing_graph_toggle_callback,
    )

    shared.PLUGIN_RACK = PluginRackTab()

    # Must call this after instantiating the other widgets,
    # as it relies on them existing
    shared.MAIN_WINDOW = MainWindow()
    MAIN_WINDOW = shared.MAIN_WINDOW

    shared.PIANO_ROLL_EDITOR.verticalScrollBar().setSliderPosition(
        shared.PIANO_ROLL_EDITOR.scene.height() * 0.4,
    )

    shared.ITEM_EDITOR.snap_combobox.setCurrentIndex(4)

    if glbl_shared.TOOLTIPS_ENABLED:
        set_tooltips_enabled(glbl_shared.TOOLTIPS_ENABLED)

