from sglib import constants
from sglib.models.daw import *
from sgui.sgqt import *

from .  import _shared
from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui.daw.lib import item as item_lib
from sglib.lib import util
from sglib.lib.translate import _
import re

MENU = None

def cut_selected():
    _shared.copy_selected()
    _shared.delete_selected()

def takes_menu_triggered(a_action):
    f_uid = shared.SEQUENCER.current_item.audio_item.item_uid
    f_new_uid = a_action.item_uid
    for f_item in shared.SEQUENCER.get_selected_items():
        if f_item.audio_item.item_uid == f_uid:
            f_item_obj = f_item.audio_item
            shared.CURRENT_SEQUENCE.remove_item_ref(f_item_obj)
            f_item_obj.uid = f_new_uid
            shared.SEQUENCER.selected_item_strings.add(str(f_item_obj))
            f_item_ref = f_item_obj.clone()
            f_item_ref.item_uid = f_new_uid
            shared.CURRENT_SEQUENCE.add_item_ref_by_uid(f_item_ref)
    constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
    constants.DAW_PROJECT.commit(_("Change active take"))
    shared.SEQ_WIDGET.open_sequence()

def _next_item_name(item_name):
    match = re.match(
        r'(.*)-([0-9]+)',
        item_name,
    )
    if match:
        name, suffix = match.groups()
        suffix = int(suffix)
    else:
        name = item_name
        suffix = 1
    while constants.DAW_PROJECT.item_exists(
        f"{name}-{suffix}",
    ):
        suffix += 1
    return f"{name}-{suffix}"


def on_auto_unlink_selected():
    """ Adds an automatic -N suffix """
    if _shared.SEQUENCE_EDITOR_MODE != 0:
        return
    f_selected = list(shared.SEQUENCER.get_selected_items())
    if not f_selected:
        return

    f_takes = constants.DAW_PROJECT.get_takes()

    shared.SEQUENCER.selected_item_strings = set()
    for f_item in sorted(
        f_selected,
        key=lambda x: (x.audio_item.track_num, x.audio_item.start_beat)
    ):
        f_cell_text = _next_item_name(f_item.name)
        f_uid = constants.DAW_PROJECT.copy_item(f_item.name, f_cell_text)
        f_item_obj = f_item.audio_item
        f_takes.add_item(f_item_obj.item_uid, f_uid)
        shared.CURRENT_SEQUENCE.remove_item_ref(f_item_obj)
        f_item_obj.uid = f_uid
        f_item_ref = f_item_obj.clone()
        f_item_ref.item_uid = f_uid
        shared.SEQUENCER.selected_item_strings.add(str(f_item_ref))
        shared.CURRENT_SEQUENCE.add_item_ref_by_uid(f_item_ref)
    constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
    constants.DAW_PROJECT.save_takes(f_takes)
    constants.DAW_PROJECT.commit(_("Auto-Unlink items"))
    shared.SEQ_WIDGET.open_sequence()

def on_auto_unlink_unique():
    if _shared.SEQUENCE_EDITOR_MODE != 0:
        return
    f_result = [
        (x.name, x.audio_item)
        for x in shared.SEQUENCER.get_selected_items()
    ]

    if not f_result:
        return

    old_new_map = {}

    f_takes = constants.DAW_PROJECT.get_takes()

    for f_item_name in set(x[0] for x in f_result):
        f_cell_text = _next_item_name(f_item_name)
        f_uid = constants.DAW_PROJECT.copy_item(f_item_name, f_cell_text)
        old_new_map[f_item_name] = f_uid

    shared.SEQUENCER.selected_item_strings = set()

    for k, v in f_result:
        shared.CURRENT_SEQUENCE.remove_item_ref(v)
        f_new_uid = old_new_map[k]
        f_takes.add_item(v.item_uid, f_new_uid)
        v.uid = f_new_uid
        f_item_ref = sequencer_item(
            v.track_num,
            v.start_beat,
            v.length_beats,
            f_new_uid,
        )
        shared.SEQUENCER.selected_item_strings.add(str(f_item_ref))
        shared.CURRENT_SEQUENCE.add_item_ref_by_uid(f_item_ref)
    constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
    constants.DAW_PROJECT.save_takes(f_takes)
    constants.DAW_PROJECT.commit(_("Auto-Unlink unique items"))
    shared.SEQ_WIDGET.open_sequence()

def on_unlink_item():
    """ Rename a single instance of an item and
        make it into a new item
    """
    if _shared.SEQUENCE_EDITOR_MODE != 0:
        return

    if (
        not shared.SEQUENCER.current_coord
        or
        not shared.SEQUENCER.current_item
    ):
        return

    f_uid_dict = constants.DAW_PROJECT.get_items_dict()
    f_current_item = shared.SEQUENCER.current_item.audio_item

    f_current_item_text = f_uid_dict.get_name_by_uid(
        f_current_item.item_uid)

    def note_ok_handler():
        f_cell_text = str(f_new_lineedit.text())
        if f_cell_text == f_current_item_text:
            QMessageBox.warning(
                shared.SEQUENCER.group_box,
                _("Error"),
                _("You must choose a different name than the original item"),
            )
            return
        if constants.DAW_PROJECT.item_exists(f_cell_text):
            QMessageBox.warning(
                shared.SEQUENCER.group_box,
                _("Error"),
                _("An item with this name already exists."),
            )
            return
        f_uid = constants.DAW_PROJECT.copy_item(
            f_current_item_text,
            str(f_new_lineedit.text()),
        )
        shared.SEQUENCER.last_item_copied = f_cell_text

        f_item_ref = f_current_item.clone()
        f_takes = constants.DAW_PROJECT.get_takes()
        f_takes.add_item(f_current_item.item_uid, f_uid)
        f_item_ref.item_uid = f_uid
        shared.CURRENT_SEQUENCE.add_item_ref_by_uid(f_item_ref)
        constants.DAW_PROJECT.save_takes(f_takes)
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(
            _("Unlink item '{}' as '{}'").format(
            f_current_item_text, f_cell_text),
        )
        shared.SEQUENCER.open_sequence()
        f_window.close()

    def note_cancel_handler():
        f_window.close()

    def on_name_changed():
        f_new_lineedit.setText(
            util.remove_bad_chars(
                f_new_lineedit.text()
            )
        )

    f_window = QDialog(shared.MAIN_WINDOW)
    f_window.setWindowTitle(_("Copy and unlink item..."))
    f_layout = QGridLayout()
    f_window.setLayout(f_layout)
    f_new_lineedit = QLineEdit(f_current_item_text)
    f_new_lineedit.editingFinished.connect(on_name_changed)
    f_new_lineedit.setMaxLength(24)
    f_layout.addWidget(QLabel(_("New name:")), 0, 0)
    f_layout.addWidget(f_new_lineedit, 0, 1)
    f_ok_button = QPushButton(_("OK"))
    f_layout.addWidget(f_ok_button, 5, 0)
    f_ok_button.clicked.connect(note_ok_handler)
    f_cancel_button = QPushButton(_("Cancel"))
    f_layout.addWidget(f_cancel_button, 5, 1)
    f_cancel_button.clicked.connect(note_cancel_handler)
    f_window.exec()

def on_rename_items():
    if _shared.SEQUENCE_EDITOR_MODE != 0:
        return
    f_result = []
    for f_item_name in (
        x.name
        for x in shared.SEQUENCER.get_selected_items()
    ):
        if not f_item_name in f_result:
            f_result.append(f_item_name)
    if not f_result:
        return

    def ok_handler():
        f_new_name = str(f_new_lineedit.text())
        if f_new_name == "":
            QMessageBox.warning(
                shared.SEQUENCER.group_box,
                _("Error"),
                _("Name cannot be blank"),
            )
            return
        global SEQUENCE_CLIPBOARD
        #Clear the clipboard, otherwise the names could be invalid
        SEQUENCE_CLIPBOARD = []
        constants.DAW_PROJECT.rename_items(f_result, f_new_name)
        constants.DAW_PROJECT.commit(_("Rename items"))
        shared.SEQ_WIDGET.open_sequence()
        if shared.DRAW_LAST_ITEMS:
            shared.global_open_items()
        f_window.close()

    def cancel_handler():
        f_window.close()

    def on_name_changed():
        f_new_lineedit.setText(
            util.remove_bad_chars(
                f_new_lineedit.text()
            )
        )

    f_window = QDialog(shared.MAIN_WINDOW)
    f_window.setWindowTitle(_("Rename selected items..."))
    f_layout = QGridLayout()
    f_window.setLayout(f_layout)
    f_new_lineedit = QLineEdit()
    f_new_lineedit.editingFinished.connect(on_name_changed)
    f_new_lineedit.setMaxLength(24)
    f_layout.addWidget(QLabel(_("New name:")), 0, 0)
    f_layout.addWidget(f_new_lineedit, 0, 1)
    f_ok_button = QPushButton(_("OK"))
    f_layout.addWidget(f_ok_button, 5, 0)
    f_ok_button.clicked.connect(ok_handler)
    f_cancel_button = QPushButton(_("Cancel"))
    f_layout.addWidget(f_cancel_button, 5, 1)
    f_cancel_button.clicked.connect(cancel_handler)
    f_window.exec()

def transpose_dialog():
    if _shared.SEQUENCE_EDITOR_MODE != 0:
        return
    f_item_set = {x.name for x in shared.SEQUENCER.get_selected_items()}
    if len(f_item_set) == 0:
        QMessageBox.warning(
            shared.MAIN_WINDOW,
            _("Error"),
            _("No items selected"),
        )
        return

    def transpose_ok_handler():
        for f_item_name in f_item_set:
            f_item = constants.DAW_PROJECT.get_item_by_name(f_item_name)
            f_item.transpose(
                f_semitone.value(),
                f_octave.value(),
                a_selected_only=False,
                a_duplicate=f_duplicate_notes.isChecked(),
            )
            item_lib.save_item(f_item_name, f_item)
        constants.DAW_PROJECT.commit(_("Transpose item(s)"))
        if shared.CURRENT_ITEM:
            shared.global_open_items(
                shared.CURRENT_ITEM_NAME,
            )
        if f_duplicate_notes.isChecked():
            shared.SEQ_WIDGET.open_sequence()
        f_window.close()

    def transpose_cancel_handler():
        f_window.close()

    f_window = QDialog(shared.MAIN_WINDOW)
    f_window.setWindowTitle(_("Transpose"))
    f_layout = QGridLayout()
    f_window.setLayout(f_layout)

    f_semitone = QSpinBox()
    f_semitone.setRange(-12, 12)
    f_layout.addWidget(QLabel(_("Semitones")), 0, 0)
    f_layout.addWidget(f_semitone, 0, 1)
    f_octave = QSpinBox()
    f_octave.setRange(-5, 5)
    f_layout.addWidget(QLabel(_("Octaves")), 1, 0)
    f_layout.addWidget(f_octave, 1, 1)
    f_duplicate_notes = QCheckBox(_("Duplicate notes?"))
    f_duplicate_notes.setToolTip(
        _(
            "Checking this box causes the transposed "
            "notes to be added rather than moving the existing notes."
        ),
    )
    f_layout.addWidget(f_duplicate_notes, 2, 1)
    f_ok = QPushButton(_("OK"))
    f_ok.pressed.connect(transpose_ok_handler)
    f_layout.addWidget(f_ok, 6, 0)
    f_cancel = QPushButton(_("Cancel"))
    f_cancel.pressed.connect(transpose_cancel_handler)
    f_layout.addWidget(f_cancel, 6, 1)
    f_window.exec()

def glue_selected():
    if glbl_shared.IS_PLAYING:
        return
    f_did_something = False
    f_selected = [x.audio_item for x in shared.SEQUENCER.get_selected()]
    for f_i in range(TRACK_COUNT_ALL):
        f_track_items = [x for x in f_selected if x.track_num == f_i]
        if len(f_track_items) > 1:
            f_did_something = True
            f_track_items.sort()
            f_new_ref = f_track_items[0].clone()
            f_items_dict = constants.DAW_PROJECT.get_items_dict()
            f_old_name = f_items_dict.get_name_by_uid(f_new_ref.item_uid)
            f_new_name = constants.DAW_PROJECT.get_next_default_item_name(
                f_old_name,
                f_items_dict,
            )
            f_new_uid = constants.DAW_PROJECT.create_empty_item(f_new_name)
            f_new_item = constants.DAW_PROJECT.get_item_by_uid(f_new_uid)
            f_tempo = shared.CURRENT_SEQUENCE.get_tempo_at_pos(
                f_new_ref.start_beat,
            )
            f_last_ref = f_track_items[-1]
            f_new_ref.item_uid = f_new_uid
            f_new_ref.length_beats = (
                f_last_ref.start_beat - f_new_ref.start_beat
            ) + f_last_ref.length_beats
            shared.CURRENT_SEQUENCE.add_item_ref_by_uid(f_new_ref)
            f_first = True
            for f_ref in f_track_items:
                f_tempo = shared.CURRENT_SEQUENCE.get_tempo_at_pos(
                    f_ref.start_beat,
                )
                f_item = constants.DAW_PROJECT.get_item_by_uid(f_ref.item_uid)
                f_new_item.extend(f_new_ref, f_ref, f_item, f_tempo)
                if not f_first:
                    shared.CURRENT_SEQUENCE.remove_item_ref(f_ref)
                else:
                    f_first = False
            util.print_sorted_dict(locals())
            item_lib.save_item(f_new_name, f_new_item)
    if f_did_something:
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(_("Glue sequencer items"))
        shared.SEQ_WIDGET.open_sequence()
    else:
        QMessageBox.warning(
            shared.MAIN_WINDOW,
            _("Error"),
            _("You must select at least 2 items on one or more tracks"),
        )

def populate_takes_menu():
    takes_menu.clear()
    if shared.SEQUENCER.current_item:
        f_takes = constants.DAW_PROJECT.get_takes()
        f_take_list = f_takes.get_take(
            shared.SEQUENCER.current_item.audio_item.item_uid,
        )
        if f_take_list:
            f_items_dict = constants.DAW_PROJECT.get_items_dict()
            for f_uid in f_take_list[1]:
                f_name = f_items_dict.get_name_by_uid(f_uid)
                f_action = takes_menu.addAction(f_name)
                f_action.item_uid = f_uid

def init():
    global \
        MENU, \
        cut_action, \
        glue_action, \
        rename_action, \
        takes_menu, \
        transpose_action, \
        unlink_action, \
        unlink_selected_action, \
        unlink_unique_action
    MENU = QMenu(shared.SEQUENCER)
    MENU.addAction(_shared.copy_action)

    cut_action = MENU.addAction(_("Cut"))
    cut_action.triggered.connect(cut_selected)
    cut_action.setShortcut(QKeySequence.StandardKey.Cut)

    paste_orig_action = MENU.addAction(_("Paste to Original Track"))
    paste_orig_action.triggered.connect(_shared.paste_clipboard)

    MENU.addSeparator()
    MENU.addAction(_shared.delete_action)
    MENU.addSeparator()

    takes_menu = MENU.addMenu(_("Takes"))
    takes_menu.triggered.connect(takes_menu_triggered)

    unlink_selected_action = MENU.addAction(
        _("Create New Take for Item(s)"),
    )
    unlink_selected_action.setShortcut(
        QKeySequence.fromString("CTRL+U"),
    )
    unlink_selected_action.triggered.connect(on_auto_unlink_selected)
    unlink_unique_action = MENU.addAction(
        _("Create New Take for Unique Item(s)"),
    )
    unlink_unique_action.setShortcut(
        QKeySequence.fromString("ALT+U"),
    )
    unlink_unique_action.triggered.connect(on_auto_unlink_unique)
    unlink_action = MENU.addAction(
        _("Create Named Take for Single Item..."),
    )
    unlink_action.triggered.connect(on_unlink_item)
    MENU.addSeparator()
    rename_action = MENU.addAction(_("Rename Selected Item(s)..."))
    rename_action.triggered.connect(on_rename_items)
    transpose_action = MENU.addAction(_("Transpose..."))
    transpose_action.triggered.connect(transpose_dialog)
    glue_action = MENU.addAction(_("Glue Selected"))
    glue_action.triggered.connect(glue_selected)
    glue_action.setShortcut(
        QKeySequence.fromString("CTRL+G"),
    )
