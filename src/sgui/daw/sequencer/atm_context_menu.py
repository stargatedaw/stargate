from .  import _shared
from sglib import constants
from sglib.math import clip_value, linear_interpolate
from sgui import shared as glbl_shared
from sgui import widgets
from sgui.daw import shared
from sglib.models.daw import *
from sglib.lib import util
from sglib.lib.translate import _
from sgui.sgqt import *
import math


MENU = None
track_atm_clipboard = []

def clear_plugin():
    if not shared.SEQUENCER.current_coord:
        return
    f_track = shared.SEQUENCER.current_coord[0]
    f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(f_track)
    if f_track_port_num is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("No automation selected for this track")
        )
        return
    f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
    shared.ATM_SEQUENCE.clear_plugins([f_index])
    shared.SEQUENCER.automation_save_callback()

def paste_atm_point():
    if glbl_shared.IS_PLAYING:
        return
    shared.SEQUENCER.context_menu_enabled = False
    if glbl_shared.CC_CLIPBOARD is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _(
                "Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."
            ),
        )
        return
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_beat = _shared.quantize(f_beat)
    f_val = glbl_shared.CC_CLIPBOARD
    f_port, f_index = shared.TRACK_PANEL.has_automation(
        shared.SEQUENCER.current_coord[0],
    )
    if f_port is not None:
        f_point = DawAtmPoint(
            f_beat,
            f_port,
            f_val,
            *shared.TRACK_PANEL.get_atm_params(f_track)
        )
        shared.ATM_SEQUENCE.add_point(f_point)
        shared.SEQUENCER.draw_point(f_point)
        shared.SEQUENCER.automation_save_callback()

def select_all():
    track_num, beat, val = shared.SEQUENCER.current_coord
    beat = _shared.quantize(beat)
    shared.SEQUENCER.atm_select_all(track_num)

def select_left():
    track_num, beat, val = shared.SEQUENCER.current_coord
    beat = _shared.quantize(beat)
    shared.SEQUENCER.atm_select_left(track_num, beat)

def select_right():
    track_num, beat, val = shared.SEQUENCER.current_coord
    beat = _shared.quantize(beat)
    shared.SEQUENCER.atm_select_right(track_num, beat)

def copy_track_sequence():
    if not shared.SEQUENCER.current_coord:
        return
    f_range = shared.SEQUENCER.get_loop_pos()
    if not f_range:
        return
    f_start, f_end = f_range
    f_track = shared.SEQUENCER.current_coord[0]
    f_plugins = constants.DAW_PROJECT.get_track_plugin_uids(f_track)
    if not f_plugins:
        return
    shared.SEQUENCER.track_atm_clipboard = \
        shared.ATM_SEQUENCE.copy_range_by_plugins(
            f_start,
            f_end,
            f_plugins,
        )
    shared.SEQUENCER.automation_save_callback()

def paste_track_sequence():
    if (
        not shared.SEQUENCER.current_coord
        or
        not shared.SEQUENCER.track_atm_clipboard
    ):
        return
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_beat = _shared.quantize(f_beat)
    for f_point in (
        x.clone()
        for x in shared.SEQUENCER.track_atm_clipboard
    ):
        f_point.beat += f_beat
        shared.ATM_SEQUENCE.add_point(f_point)
    shared.SEQUENCER.automation_save_callback()

def clear_track_sequence():
    if not shared.SEQUENCER.current_coord:
        return
    f_range = shared.SEQUENCER.get_loop_pos()
    if not f_range:
        return
    f_start, f_end = f_range
    f_track, f_beat = shared.SEQUENCER.current_coord[:2]
    f_plugins = constants.DAW_PROJECT.get_track_plugin_uids(f_track)
    if not f_plugins:
        return
    shared.ATM_SEQUENCE.clear_range_by_plugins(f_start, f_end, f_plugins)
    shared.SEQUENCER.automation_save_callback()

def clear_track():
    if not shared.SEQUENCER.current_coord:
        return
    f_track = shared.SEQUENCER.current_coord[0]
    f_plugins = constants.DAW_PROJECT.get_track_plugin_uids(f_track)
    if not f_plugins:
        return
    shared.ATM_SEQUENCE.clear_plugins(f_plugins)
    shared.SEQUENCER.automation_save_callback()

# Not used
def clear_port():
    if not shared.SEQUENCER.current_coord:
        return
    f_track = shared.SEQUENCER.current_coord[0]
    (
        f_track_port_num,
        f_track_index,
    ) = shared.TRACK_PANEL.has_automation(f_track)

    if f_track_port_num is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("No automation selected for this track"),
        )
        return
    f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
    shared.ATM_SEQUENCE.clear_port(f_index, f_track_port_num)
    shared.SEQUENCER.automation_save_callback()

def transform_atm_callback(a_add, a_mul):
    shared.SEQUENCER.setUpdatesEnabled(False)
    for f_point, f_val in zip(
        shared.SEQUENCER.atm_selected,
        shared.SEQUENCER.atm_selected_vals,
    ):
        f_val = (f_val * a_mul) + a_add
        f_val = clip_value(f_val, 0.0, 127.0, True)
        f_point.item.cc_val = f_val
        f_point.setPos(
            shared.SEQUENCER.get_pos_from_point(f_point.item),
        )
    shared.SEQUENCER.setUpdatesEnabled(True)
    shared.SEQUENCER.update()

def transform_atm():
    shared.SEQUENCER.atm_selected = sorted(
        shared.SEQUENCER.get_selected_points(),
    )
    if not shared.SEQUENCER.atm_selected:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("No automation points selected"),
        )
        return
    f_start_beat = shared.SEQUENCER.atm_selected[0].item.beat
    shared.SEQUENCER.set_playback_pos(f_start_beat)
    f_scrollbar = shared.SEQUENCER.horizontalScrollBar()
    f_scrollbar.setValue(
        int(_shared.SEQUENCER_PX_PER_BEAT * f_start_beat),
    )

    shared.SEQUENCER.atm_selected_vals = [
        x.item.cc_val
        for x in shared.SEQUENCER.atm_selected
    ]

    f_result = widgets.add_mul_dialog(
        transform_atm_callback,
        lambda: shared.SEQUENCER.automation_save_callback(a_open=False)
    )

    if not f_result:
        for f_point, f_val in zip(
            shared.SEQUENCER.atm_selected,
            shared.SEQUENCER.atm_selected_vals,
        ):
            f_point.item.cc_val = f_val
        shared.SEQUENCER.automation_save_callback()
    else:
        shared.SEQUENCER.open_sequence()

def lfo_atm_callback(
    a_phase,
    a_start_freq,
    a_start_amp,
    a_start_center,
    a_start_fade,
    a_end_fade,
    a_end_freq,
    a_end_amp,
    a_end_center,
):
    a_phase, a_start_freq, a_start_fade, a_end_freq, a_end_fade = (
        x * 0.01
        for x in (
            a_phase,
            a_start_freq,
            a_start_fade,
            a_end_freq,
            a_end_fade,
        )
    )

    a_phase *= math.pi
    f_start_beat, f_end_beat = shared.SEQUENCER.get_loop_pos()

    f_length_beats = f_end_beat - f_start_beat
    two_pi = 2.0 * math.pi
    f_start_radians_p64, f_end_radians_p64 = (
        (x * two_pi) / 8.0
        for x in (a_start_freq, a_end_freq)
    )
    f_length_beats_recip = 1.0 / f_length_beats

    shared.SEQUENCER.setUpdatesEnabled(False)

    for f_point in shared.SEQUENCER.atm_selected:
        f_pos_beats = f_point.item.beat - f_start_beat
        f_pos = f_pos_beats * f_length_beats_recip
        f_center = linear_interpolate(
            a_start_center, a_end_center, f_pos)
        f_amp = linear_interpolate(
            a_start_amp, a_end_amp, f_pos)

        if f_pos < a_start_fade:
            f_amp *= f_pos / a_start_fade
        elif f_pos > a_end_fade:
            f_amp *= 1.0 - (
                (f_pos - a_end_fade) / (1.0 - a_end_fade))

        f_val = (math.sin(a_phase) * f_amp) + f_center
        f_val = clip_value(f_val, 0.0, 127.0, True)
        f_point.item.cc_val = f_val
        f_point.setPos(shared.SEQUENCER.get_pos_from_point(f_point.item))

        a_phase += linear_interpolate(
            f_start_radians_p64,
            f_end_radians_p64,
            f_pos,
        )
        if a_phase >= two_pi:
            a_phase -= two_pi

    shared.SEQUENCER.setUpdatesEnabled(True)
    shared.SEQUENCER.update()

def lfo_atm():
    if not shared.SEQUENCER.current_coord:
        return
    f_range = shared.SEQUENCER.get_loop_pos()
    if not f_range:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _(
                "You must set the region start and end by right-clicking on "
                "the sequencer header"
            ),
        )
        return
    f_start_beat, f_end_beat = f_range
    if f_end_beat - f_start_beat > 64:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("LFO patterns are limited to 64 beats in length"),
        )
        return
    f_scrollbar = shared.SEQUENCER.horizontalScrollBar()
    f_scrollbar.setValue(
        int(_shared.SEQUENCER_PX_PER_BEAT * f_start_beat),
    )
    shared.SEQUENCER.set_playback_pos(f_start_beat)
    f_step = 1.0 / 16.0
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
    if f_index is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _(
                "Track has no automation selected.  Use the menu button on "
                "the track to select a plugin and control to automate"
            ),
        )
        return

    f_port, f_atm_uid = shared.TRACK_PANEL.has_automation(f_track)
    f_old = shared.ATM_SEQUENCE.clear_range(
        f_index,
        f_port,
        f_start_beat,
        f_end_beat,
    )
    if f_old:
        shared.SEQUENCER.automation_save_callback()
    f_pos = f_start_beat
    shared.SEQUENCER.scene.clearSelection()
    shared.SEQUENCER.atm_selected = []

    for f_i in range(int((f_end_beat - f_start_beat) / f_step)):
        f_point = DawAtmPoint(
            f_pos,
            f_port,
            64.0,
            f_index,
            f_plugin,
        )
        shared.ATM_SEQUENCE.add_point(f_point)
        f_item = shared.SEQUENCER.draw_point(f_point)
        shared.SEQUENCER.atm_selected.append(f_item)
        f_pos += f_step

    f_result = widgets.lfo_dialog(
        lfo_atm_callback,
        lambda : shared.SEQUENCER.automation_save_callback(a_open=False)
    )

    if not f_result:
        for f_point in shared.SEQUENCER.atm_selected:
            shared.ATM_SEQUENCE.remove_point(f_point.item)
        if f_old:
            for f_point in f_old:
                shared.ATM_SEQUENCE.add_point(f_point)
        shared.SEQUENCER.automation_save_callback()
    else:
        shared.SEQUENCER.open_sequence()

def break_atm(checked=False, new_val=1):
    if _shared.SEQUENCE_EDITOR_MODE != 1:
        return
    assert new_val in (0, 1), "Unexpected value '{}'".format(new_val)
    points = [
        x.item
        for x in shared.SEQUENCER.get_selected_points()
    ]
    if points:
        for point in points:
            point.break_after = new_val
        shared.SEQUENCER.automation_save_callback()
    else:
        QMessageBox.warning(None, "Error", "No points selected")

def unbreak_atm():
    break_atm(new_val=0)

def init():
    global \
        MENU, \
        break_atm_action, \
        unbreak_atm_action
    MENU = QMenu(shared.SEQUENCER)
    MENU.addAction(_shared.copy_action)

    paste_action = QAction(_("Paste"), MENU)
    MENU.addAction(paste_action)
    paste_action.setToolTip(
        'Paste previously copied automation points to the track they came from'
    )
    paste_action.triggered.connect(_shared._paste)

    paste_ctrl_action = QAction(_("Paste Plugin Control"), MENU)
    MENU.addAction(paste_ctrl_action)
    paste_ctrl_action.setToolTip(
        'Paste a single automation point from a control value copied by '
        'right-clicking on a plugin knob and choosing "copy value"'
    )
    paste_ctrl_action.triggered.connect(paste_atm_point)

    select_menu = MENU.addMenu("Select")

    select_all_action = QAction('All', select_menu)
    select_menu.addAction(select_all_action)
    select_all_action.setToolTip(
        'Select all automation points in this track for the currently '
        'selected automation parameter'
    )
    select_all_action.triggered.connect(select_all)

    select_left_action = QAction('Left', select_menu)
    select_menu.addAction(select_left_action)
    select_left_action.setToolTip(
        'Select all automation points to the left of the mouse cursor in '
        'this track for the currently selected automation parameter'
    )
    select_left_action.triggered.connect(select_left)

    select_right_action = QAction('Right', select_menu)
    select_menu.addAction(select_right_action)
    select_right_action.setToolTip(
        'Select all automation points to the right of the mouse cursor in '
        'this track for the currently selected automation parameter'
    )
    select_right_action.triggered.connect(select_right)

    track_atm_menu = MENU.addMenu(_("All Plugins for Track"))

    copy_track_sequence_action = QAction(_("Copy Region"), track_atm_menu)
    track_atm_menu.addAction(copy_track_sequence_action)
    copy_track_sequence_action.setToolTip(
        'Copy automation points for all plugins on this track within the '
        'region set by right clicking on the sequencer timeline and '
        'setting the region start and end'
    )
    copy_track_sequence_action.triggered.connect(copy_track_sequence)

    paste_track_sequence_action = QAction(_("Paste Region"), track_atm_menu)
    track_atm_menu.addAction(paste_track_sequence_action)
    paste_track_sequence_action.setToolTip(
        'Paste a previously copied region to the current track'
    )
    paste_track_sequence_action.triggered.connect(paste_track_sequence)

    track_atm_menu.addSeparator()

    clear_track_sequence_action = QAction(_("Clear Region"), track_atm_menu)
    track_atm_menu.addAction(clear_track_sequence_action)
    clear_track_sequence_action.setToolTip(
        'Clear all automation points in a region for all plugins on a track. '
        'Set the region start and end by right-clicking on the sequencer '
        'timeline'
    )
    clear_track_sequence_action.triggered.connect(clear_track_sequence)

    atm_clear_menu = MENU.addMenu(_("Clear All"))

    atm_clear_menu.addSeparator()

    clear_plugin_action = QAction(_("Current Plugin"), atm_clear_menu)
    atm_clear_menu.addAction(clear_plugin_action)
    clear_plugin_action.setToolTip(
        'Clear all automation points for the currently selected plugin on '
        'this track'
    )
    clear_plugin_action.triggered.connect(clear_plugin)

    atm_clear_menu.addSeparator()

    clear_track_action = QAction(_("Track"), atm_clear_menu)
    atm_clear_menu.addAction(clear_track_action)
    clear_track_action.setToolTip(
        'Clear all automation points on all plugins on this track'
    )
    clear_track_action.triggered.connect(clear_track)

    transform_atm_action = QAction(_("Transform..."), MENU)
    MENU.addAction(transform_atm_action)
    transform_atm_action.setToolTip(
        'Open a dialog to allow transforming the automation point values '
        'in various ways'
    )
    transform_atm_action.triggered.connect(transform_atm)

    lfo_atm_action = QAction(_("LFO Tool..."), MENU)
    MENU.addAction(lfo_atm_action)
    lfo_atm_action.setToolTip(
        'Open a dialog to allow creating LFO shaped automation curves'
    )
    lfo_atm_action.triggered.connect(lfo_atm)

    MENU.addSeparator()

    break_atm_action = QAction(
        _("Break after selected automation point(s)"),
        MENU,
    )
    break_atm_action.setToolTip(
        'Break the automation line after each selected point.  This causes '
        'automation to only move when there is an automation point, and not '
        'smoothly move between the points'
    )
    MENU.addAction(break_atm_action)
    break_atm_action.triggered.connect(break_atm)
    break_atm_action.setShortcut(QKeySequence.fromString("CTRL+B"))

    unbreak_atm_action = QAction(
        _("Un-break after selected automation point(s)"),
        MENU,
    )
    unbreak_atm_action.setToolTip(
        'Unbreak a previously broken automation line, cause automation after '
        'each selected point to be smooth again'
    )
    MENU.addAction(unbreak_atm_action)
    unbreak_atm_action.triggered.connect(unbreak_atm)
    unbreak_atm_action.setShortcut(
        QKeySequence.fromString("CTRL+SHIFT+B"),
    )
    MENU.addSeparator()
    MENU.addAction(_shared.delete_action)

