"""

"""

from sglib import constants
from . import _shared
from .editor import PianoRollEditor
from .key import PianoKeyItem
from .note import PianoRollNoteItem
from sgui.daw import shared
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.models import stargate as sg_project
from sglib.lib import util
from sglib.lib import scales
from sglib.lib.util import *
from sglib.lib.translate import _
from sgui.sgqt import *


class PianoRollEditorWidget:
    """ This is the parent widget that contains the PianoRollEditor """
    def __init__(self):
        self.widget = QWidget()
        self.widget.setContentsMargins(0, 0, 0, 0)
        self.vlayout = QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.widget.setLayout(self.vlayout)

        self.hlayout = QHBoxLayout()
        self.hlayout.setContentsMargins(5, 5, 5, 5)
        self.hlayout.setSpacing(5)
        self.scale_key_combobox = QComboBox()
        self.scale_key_combobox.setToolTip(
            'Choose the root key for the musical scale to use'
        )
        self.scale_key_combobox.setMinimumWidth(60)
        self.scale_key_combobox.addItems(_shared.PIANO_ROLL_NOTE_LABELS)
        self.scale_key_combobox.currentIndexChanged.connect(
            self.reload_handler)
        self.hlayout.addWidget(QLabel("Key:"))
        self.hlayout.addWidget(self.scale_key_combobox)
        self.scale_combobox = QComboBox()
        self.scale_combobox.setToolTip('Choose the musical scale to use')
        self.scale_combobox.setMinimumWidth(172)
        self.scale_combobox.addItems(scales.SCALE_NAMES)
        self.scale_combobox.currentIndexChanged.connect(self.reload_handler)
        self.hlayout.addWidget(QLabel(_("Scale:")))
        self.hlayout.addWidget(self.scale_combobox)

        self.hlayout.addWidget(QLabel("V"))
        self.vzoom_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hlayout.addWidget(self.vzoom_slider)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setMaximumWidth(72)
        self.vzoom_slider.setRange(9, 24)
        self.vzoom_slider.setToolTip('Vertical zoom')
        self.vzoom_slider.setValue(int(shared.PIANO_ROLL_NOTE_HEIGHT))
        self.vzoom_slider.valueChanged.connect(self.set_midi_vzoom)
        self.vzoom_slider.sliderReleased.connect(self.save_vzoom)

        self.param_combobox = QComboBox()
        self.param_combobox.setToolTip(
            'Per note expression parameters for plugins.  Use '
            'CTRL+ALT+drag (change value) and CTRL+SHIFT+drag (value curve) '
            'selected items to modify these values'
        )
        self.param_combobox.setMinimumWidth(75)
        self.param_combobox.addItems(
            ['Velocity', 'Pan', 'Attack', 'Decay', 'Sustain', 'Release'],
        )
        self.param_combobox.currentIndexChanged.connect(self.param_changed)
        self.hlayout.addWidget(QLabel(_("Parameter")))
        self.hlayout.addWidget(self.param_combobox)

        self.edit_menu_button = QPushButton(_("Menu"))
        self.edit_menu_button.setFixedWidth(60)
        self.edit_menu = QMenu(self.widget)
        self.edit_menu_button.setMenu(self.edit_menu)
        self.hlayout.insertWidget(0, self.edit_menu_button)

        self.edit_actions_menu = self.edit_menu.addMenu(_("Edit"))

        self.copy_action = QAction(_("Copy"), self.edit_actions_menu)
        self.edit_actions_menu.addAction(self.copy_action)
        self.copy_action.setToolTip(
            'Copy selected note items to the clipboard.  Useful for copying '
            'notes between MIDI channels or items.  Select+CTRL+drag can be '
            'used to copy notes within this item/channel to new positions'
        )
        self.copy_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.copy_selected,
        )
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)

        self.cut_action = QAction(_("Cut"), self.edit_actions_menu)
        self.edit_actions_menu.addAction(self.cut_action)
        self.cut_action.setToolTip(
            'Copy selected note items to the clipboard, then remove them '
            'from this item/channel.  Useful for moving notes between MIDI '
            'channels or items'
        )
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)

        self.paste_action = QAction(_("Paste"))
        self.edit_actions_menu.addAction(self.paste_action)
        self.paste_action.setToolTip(
            'Paste previously copied notes into this item/channel, at the '
            'original position they were copied/cut from'
        )
        self.paste_action.triggered.connect(shared.PIANO_ROLL_EDITOR.paste)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)

        self.select_all_action = QAction(
            _("Select All"),
            self.edit_actions_menu,
        )
        self.edit_actions_menu.addAction(self.select_all_action)
        self.select_all_action.setToolTip('Select all MIDI notes')
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)

        self.clear_selection_action = QAction(
            _("Clear Selection"),
            self.edit_actions_menu,
        )
        self.edit_actions_menu.addAction(self.clear_selection_action)
        self.clear_selection_action.setToolTip('Unselect all MIDI notes')
        self.clear_selection_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.scene.clearSelection,
        )
        self.clear_selection_action.setShortcut(
            QKeySequence.fromString("Esc")
        )

        self.edit_actions_menu.addSeparator()

        self.delete_selected_action = QAction(
            _("Delete"),
            self.edit_actions_menu,
        )
        self.edit_actions_menu.addAction(self.delete_selected_action)
        self.delete_selected_action.setToolTip(
            'Delete selected MIDI notes'
        )
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(
            QKeySequence.StandardKey.Delete,
        )

        self.quantize_action = QAction(_("Quantize..."), self.edit_menu)
        self.edit_menu.addAction(self.quantize_action)
        self.quantize_action.setToolTip(
            'Open a dialog to quantize selected notes'
        )
        self.quantize_action.triggered.connect(self.quantize_dialog)

        self.transpose_menu = self.edit_menu.addMenu(_("Transpose"))

        self.transpose_action = QAction(_("Dialog..."), self.transpose_menu)
        self.transpose_menu.addAction(self.transpose_action)
        self.transpose_action.setToolTip(
            'Open a dialog to transpose selected notes'
        )
        self.transpose_action.triggered.connect(self.transpose_dialog)

        self.transpose_menu.addSeparator()

        self.up_semitone_action = QAction(
            _("Up Semitone"),
            self.transpose_menu,
        )
        self.transpose_menu.addAction(self.up_semitone_action)
        self.up_semitone_action.setToolTip(
            'Transpose selected notes up one semitone'
        )
        self.up_semitone_action.triggered.connect(self.transpose_up_semitone)
        self.up_semitone_action.setShortcut(
            QKeySequence.fromString("SHIFT+UP"),
        )

        self.down_semitone_action = QAction(
            _("Down Semitone"),
            self.transpose_menu,
        )
        self.transpose_menu.addAction(self.down_semitone_action)
        self.down_semitone_action.setToolTip(
            'Transpose selected notes down one semitone'
        )
        self.down_semitone_action.triggered.connect(
            self.transpose_down_semitone,
        )
        self.down_semitone_action.setShortcut(
            QKeySequence.fromString("SHIFT+DOWN"),
        )

        self.up_octave_action = QAction(_("Up Octave"), self.transpose_menu)
        self.transpose_menu.addAction(self.up_octave_action)
        self.up_octave_action.setToolTip(
            'Transpose selected notes up one octave'
        )
        self.up_octave_action.triggered.connect(self.transpose_up_octave)
        self.up_octave_action.setShortcut(
            QKeySequence.fromString("ALT+UP"),
        )

        self.down_octave_action = QAction(
            _("Down Octave"),
            self.transpose_menu,
        )
        self.transpose_menu.addAction(self.down_octave_action)
        self.down_octave_action.setToolTip(
            'Transpose selected notes up one octave'
        )
        self.down_octave_action.triggered.connect(self.transpose_down_octave)
        self.down_octave_action.setShortcut(
            QKeySequence.fromString("ALT+DOWN"),
        )

        self.velocity_menu = self.edit_menu.addMenu(_("Velocity"))

        self.velocity_menu.addSeparator()

        self.vel_random_index = 0
        self.velocity_random_menu = self.velocity_menu.addMenu(_("Randomness"))
        self.random_types = [_("None"), _("Tight"), _("Loose")]
        self.vel_rand_action_group = QActionGroup(
            self.velocity_random_menu,
        )
        self.velocity_random_menu.triggered.connect(self.vel_rand_triggered)

        for f_i, f_type, tooltip in zip(
            range(len(self.random_types)),
            self.random_types,
            (
                'No randomness, initial velocity is always 100',
                (
                    'Slight randomness, every note drawn will have a value '
                    'near 100'
                ),
                'More extreme randomness',
            ),
        ):
            f_action = QAction(f_type, self.velocity_random_menu)
            self.velocity_random_menu.addAction(f_action)
            f_action.setToolTip(tooltip)
            f_action.setActionGroup(self.vel_rand_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.vel_emphasis_index = 0
        self.velocity_emphasis_menu = self.velocity_menu.addMenu(_("Emphasis"))
        self.emphasis_types = [_("None"), _("On-beat"), _("Off-beat")]
        self.vel_emphasis_action_group = QActionGroup(
            self.velocity_random_menu)
        self.velocity_emphasis_menu.triggered.connect(
            self.vel_emphasis_triggered)

        for f_i, f_type, tooltip in zip(
            range(len(self.emphasis_types)),
            self.emphasis_types,
            (
                'No emphasis, velocity is consistent',
                'Higher velocity near a beat, lower velocity off beat',
                'Lower velocity near a beat, higher velocity off beat',
            ),
        ):
            f_action = QAction(f_type, self.velocity_emphasis_menu)
            self.velocity_emphasis_menu.addAction(f_action)
            f_action.setToolTip(tooltip)
            f_action.setActionGroup(self.vel_emphasis_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.expression_menu = self.edit_menu.addMenu(_("Expression"))

        self.reset_velocity_action = QAction(
            _("Reset Velocity"),
            self.expression_menu,
        )
        self.expression_menu.addAction(self.reset_velocity_action)
        self.reset_velocity_action.setToolTip(
            'Reset velocity of selected notes to 100'
        )
        self.reset_velocity_action.triggered.connect(self.reset_velocity)

        self.reset_pan_action = QAction(_("Reset Pan"), self.expression_menu)
        self.expression_menu.addAction(self.reset_pan_action)
        self.reset_pan_action.setToolTip(
            'Reset the per-note pan of selected notes to center'
        )
        self.reset_pan_action.triggered.connect(self.reset_pan)

        self.reset_attack_action = QAction(
            _("Reset Attack"),
            self.expression_menu,
        )
        self.expression_menu.addAction(self.reset_attack_action)
        self.reset_attack_action.setToolTip(
            'Reset the per-note attack modification to zero'
        )
        self.reset_attack_action.triggered.connect(self.reset_attack)

        self.reset_decay_action = QAction(
            _("Reset Decay"),
            self.expression_menu,
        )
        self.expression_menu.addAction(self.reset_decay_action)
        self.reset_decay_action.setToolTip(
            'Reset the per-note decay modification to zero'
        )
        self.reset_decay_action.triggered.connect(self.reset_decay)

        self.reset_sustain_action = QAction(
            _("Reset Sustain"),
            self.expression_menu,
        )
        self.expression_menu.addAction(self.reset_sustain_action)
        self.reset_sustain_action.setToolTip(
            'Reset the per-note sustain modification to zero'
        )
        self.reset_sustain_action.triggered.connect(self.reset_sustain)

        self.reset_release_action = QAction(
            _("Reset Release"),
            self.expression_menu,
        )
        self.expression_menu.addAction(self.reset_release_action)
        self.reset_release_action.setToolTip(
            'Reset the per-note release modification to zero'
        )
        self.reset_release_action.triggered.connect(self.reset_release)

        self.edit_menu.addSeparator()

        self.glue_selected_action = QAction(
            _("Glue Selected"),
            self.edit_menu,
        )
        self.edit_menu.addAction(self.glue_selected_action)
        self.glue_selected_action.setToolTip(
            'Glue together selected notes of the same MIDI note number into '
            'new, larger notes'
        )
        self.glue_selected_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.glue_selected,
        )
        self.glue_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+G"),
        )

        self.half_selected_action = QAction(
            _("Split Selected in Half"),
            self.edit_menu,
        )
        self.edit_menu.addAction(self.half_selected_action)
        self.half_selected_action.setToolTip(
            'Cut selected notes in half'
        )
        self.half_selected_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.half_selected,
        )
        self.half_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+H"),
        )

        self.edit_menu.addSeparator()

        self.draw_last_action = QAction(
            _("Draw Last Item(s)"),
            self.edit_menu,
        )
        self.edit_menu.addAction(self.draw_last_action)
        self.draw_last_action.setToolTip(
            'Draw the last item opened before the current as semi-transparent '
            '"ghost notes".  Use this for comparison to ensure that 2 parts '
            'are musically harmonious'
        )
        self.draw_last_action.triggered.connect(self.draw_last)
        self.draw_last_action.setCheckable(True)
        self.draw_last_action.setShortcut(
            QKeySequence.fromString("CTRL+F"),
        )

        self.open_last_action = QAction(
            _("Open Last Item(s)"),
            self.edit_menu,
        )
        self.edit_menu.addAction(self.open_last_action)
        self.open_last_action.setToolTip(
            'Open the previously opened item.  Use this to rapidly switch '
            'between 2 items you are editing'
        )
        self.open_last_action.triggered.connect(self.open_last)
        self.open_last_action.setShortcut(
            QKeySequence.fromString("ALT+F"),
        )

        self.edit_menu.addSeparator()

        self.preview_note_action = QAction('Preview Notes', self.edit_menu)
        self.edit_menu.addAction(self.preview_note_action)
        self.preview_note_action.setToolTip(
            'Enable or disable playing any notes that are drawn or moved.'
        )
        self.preview_note_action.triggered.connect(self.toggle_preview_note)
        self.open_last_action.setShortcut(
            QKeySequence.fromString("ALT+N"),
        )
        self.preview_note_action.setCheckable(True)
        if get_file_setting('preview-note', bool, True):
            self.preview_note_action.setChecked(True)

        self.hlayout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Policy.Expanding),
        )

        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(shared.PIANO_ROLL_EDITOR)

    def toggle_preview_note(self):
        active = get_file_setting('preview-note', int, 1)
        set_file_setting('preview-note', int(not active))
        self.preview_note_action.setChecked(not active)

    def param_changed(self, value):
        _shared.PARAMETER = value
        shared.PIANO_ROLL_EDITOR.draw_item()

    def set_midi_vzoom(self, a_val):
        shared.PIANO_ROLL_NOTE_HEIGHT = a_val
        shared.PIANO_ROLL_EDITOR.draw_item()

    def save_vzoom(self):
        util.set_file_setting("PIANO_VZOOM", self.vzoom_slider.value())

    def quantize_dialog(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        shared.ITEM_EDITOR.quantize_dialog(
            shared.PIANO_ROLL_EDITOR.has_selected,
        )

    def transpose_dialog(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        shared.ITEM_EDITOR.transpose_dialog(
            shared.PIANO_ROLL_EDITOR.has_selected,
            channel=shared.ITEM_EDITOR.get_midi_channel(),
        )

    def select_all(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        for f_note in shared.PIANO_ROLL_EDITOR.note_items:
            f_note.setSelected(True)

    def open_last(self):
        if shared.LAST_ITEM_NAME:
            global_open_items(
                shared.LAST_ITEM_NAME,
                a_new_ref=shared.LAST_ITEM_REF,
            )
            shared.PIANO_ROLL_EDITOR.draw_item()

    def draw_last(self):
        shared.DRAW_LAST_ITEMS = not shared.DRAW_LAST_ITEMS
        self.draw_last_action.setChecked(shared.DRAW_LAST_ITEMS)
        shared.PIANO_ROLL_EDITOR.draw_item()
        #global_open_items()

    def vel_rand_triggered(self, a_action):
        self.vel_random_index = a_action.my_index
        self.set_vel_rand()

    def vel_emphasis_triggered(self, a_action):
        self.vel_emphasis_index = a_action.my_index
        self.set_vel_rand()

    def transpose_up_semitone(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(1)

    def transpose_down_semitone(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(-1)

    def transpose_up_octave(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(12)

    def transpose_down_octave(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(-12)

    def set_vel_rand(self, a_val=None):
        shared.PIANO_ROLL_EDITOR.set_vel_rand(
            self.vel_random_index,
            self.vel_emphasis_index,
        )

    def on_delete_selected(self):
        shared.PIANO_ROLL_EDITOR.delete_selected()

    def on_cut(self):
        if shared.PIANO_ROLL_EDITOR.copy_selected():
            self.on_delete_selected()

    def reload_handler(self, a_val=None):
        constants.DAW_PROJECT.set_midi_scale(
            self.scale_key_combobox.currentIndex(),
            self.scale_combobox.currentIndex(),
        )
        if shared.CURRENT_ITEM:
            shared.PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
            shared.PIANO_ROLL_EDITOR.draw_item()
        else:
            shared.PIANO_ROLL_EDITOR.clear_drawn_items()

    def set_expression_param(self, param: int, value=0.0):
        channel = shared.ITEM_EDITOR.get_midi_channel()
        if shared.PIANO_ROLL_EDITOR.has_selected:
            for note in shared.PIANO_ROLL_EDITOR.get_selected_items():
                note.note_item.set_pmn_param(param, value)
        else:
            for note in shared.CURRENT_ITEM.notes:
                if note.channel == channel:
                    note.set_pmn_param(param, value)
        shared.global_save_and_reload_items()

    def reset_velocity(self):
        self.set_expression_param(0, 100)

    def reset_pan(self):
        self.set_expression_param(1)

    def reset_attack(self):
        self.set_expression_param(2)

    def reset_decay(self):
        self.set_expression_param(3)

    def reset_sustain(self):
        self.set_expression_param(4)

    def reset_release(self):
        self.set_expression_param(5)

