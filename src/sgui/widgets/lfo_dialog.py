from . import _shared
from .control import knob_control
from .playback_widget import playback_widget
from sglib.lib.translate import _
from sgui.sgqt import *

def lfo_dialog(a_update_callback, a_save_callback):
    """ Generic dialog for doing event transforms that are LFO-like.
        The actual transforms are performed by the caller using the
        event callbacks.  The caller should create a list of event
        objects and their original values.
    """
    def ok_handler():
        f_dialog.close()
        f_dialog.retval = True

    def update(*args):
        f_vals = [x.control.value() for x in f_controls]
        f_vals += [
            x.control.value() if y.isChecked() else z.control.value()
            for x, y, z in f_optional_controls
        ]
        a_update_callback(*f_vals)

    def save(*args):
        a_save_callback()

    def update_and_save(a_val=None):
        update()
        save()

    f_dialog = QDialog()
    f_dialog.setFixedSize(570, 200)
    f_dialog.retval = False
    f_dialog.setWindowTitle(_("LFO Tool"))
    f_vlayout = QVBoxLayout(f_dialog)
    f_layout = QGridLayout()
    f_vlayout.addLayout(f_layout)

    f_knob_size = 48

    f_phase_knob = knob_control(
        f_knob_size,
        _("Phase"),
        0,
        save,
        update,
        0,
        100,
        0,
        _shared.KC_DECIMAL,
        tooltip=(
            'The oscillator phase for the LFO.  0.0 starts at the '
            'beginning, 1.0 at the end'
        ),
    )
    f_phase_knob.add_to_grid_layout(f_layout, 0)

    f_start_freq_knob = knob_control(
        f_knob_size,
        _("Start Freq"),
        0,
        save,
        update,
        10,
        400,
        100,
        _shared.KC_HZ_DECIMAL,
        tooltip=(
            'The frequency of the LFO at the start of the region, in hertz'
        ),
    )
    f_start_freq_knob.add_to_grid_layout(f_layout, 5)

    f_end_freq_knob = knob_control(
        f_knob_size,
        _("End Freq"),
        0,
        save,
        update,
        10,
        400,
        100,
        _shared.KC_HZ_DECIMAL,
        tooltip=(
            'The frequency of the LFO at the end of the region, in hertz'
        ),
    )
    f_end_freq_knob.add_to_grid_layout(f_layout, 10)

    f_end_freq_cbox = QCheckBox()
    f_end_freq_cbox.setToolTip(
        'If checked, the End Freq. knob is enabled'
    )
    f_end_freq_cbox.stateChanged.connect(update_and_save)
    f_layout.addWidget(f_end_freq_cbox, 5, 10)

    f_start_amp_knob = knob_control(
        f_knob_size,
        _("Start Amp"),
        0,
        save,
        update,
        0,
        127,
        64,
        _shared.KC_INTEGER,
        tooltip=(
            'The amplitude of the LFO at the start of the region'
        )
    )
    f_start_amp_knob.add_to_grid_layout(f_layout, 11)

    f_end_amp_knob = knob_control(
        f_knob_size,
        _("End Amp"),
        0,
        save,
        update,
        0,
        127,
        64,
        _shared.KC_INTEGER,
        tooltip=(
            'The amplitude of the LFO at the end of the region'
        ),
    )
    f_end_amp_knob.add_to_grid_layout(f_layout, 12)

    f_end_amp_cbox = QCheckBox()
    f_end_amp_cbox.setToolTip(
        'If checked, the End Amp. knob is enabled'
    )
    f_end_amp_cbox.stateChanged.connect(update_and_save)
    f_layout.addWidget(f_end_amp_cbox, 5, 12)

    f_start_center_knob = knob_control(
        f_knob_size,
        _("Start Center"),
        0,
        save,
        update,
        0,
        127,
        64,
        _shared.KC_INTEGER,
        tooltip=(
            'Change the center line at the start of the LFO.  Amplitude '
            'should be less than full value if using this knob'
        ),
    )
    f_start_center_knob.add_to_grid_layout(f_layout, 15)

    f_end_center_knob = knob_control(
        f_knob_size,
        _("End Center"),
        0,
        save,
        update,
        0,
        127,
        64,
        _shared.KC_INTEGER,
        tooltip=(
            'Change the center line at the end of the LFO.  Amplitude '
            'should be less than full value if using this knob'
        ),
    )
    f_end_center_knob.add_to_grid_layout(f_layout, 16)

    f_end_center_cbox = QCheckBox()
    f_end_center_cbox.setToolTip(
        'If checked, the End Center knob is enabled'
    )
    f_end_center_cbox.stateChanged.connect(update_and_save)
    f_layout.addWidget(f_end_center_cbox, 5, 16)

    def start_fade_changed(*args):
        f_start, f_end = (
            int(x.control.value())
            for x in (f_start_fade_knob, f_end_fade_knob)
        )
        if  f_start >= f_end:
            f_end_fade_knob.control.setValue(f_start + 1)
        else:
            update()

    f_start_fade_knob = knob_control(
        f_knob_size,
        _("Start Fade"),
        0,
        save,
        start_fade_changed,
        0,
        99,
        0,
        _shared.KC_INTEGER,
        tooltip='Fade in the start of the LFO',
    )
    f_start_fade_knob.add_to_grid_layout(f_layout, 20)

    def end_fade_changed(*args):
        f_start, f_end = (
            int(x.control.value())
            for x in (f_start_fade_knob, f_end_fade_knob)
        )
        if f_end <= f_start:
            f_start_fade_knob.control.setValue(f_end - 1)
        else:
            update()

    f_end_fade_knob = knob_control(
        f_knob_size,
        _("End Fade"),
        0,
        save,
        end_fade_changed,
        1,
        100,
        100,
        _shared.KC_INTEGER,
        tooltip='Fade out the end of the LFO',
    )
    f_end_fade_knob.add_to_grid_layout(f_layout, 25)

    f_playback_widget = playback_widget()
    # Does not work, also there is no longer button styling for it
    # f_layout.addWidget(f_playback_widget.play_button, 1, 30)
    # f_layout.addWidget(f_playback_widget.stop_button, 1, 31)

    f_controls = (
        f_phase_knob, f_start_freq_knob, f_start_amp_knob,
        f_start_center_knob, f_start_fade_knob, f_end_fade_knob,
        )

    f_optional_controls = (
        (f_end_freq_knob, f_end_freq_cbox, f_start_freq_knob),
        (f_end_amp_knob, f_end_amp_cbox, f_start_amp_knob),
        (f_end_center_knob, f_end_center_cbox, f_start_center_knob),
        )

    ok_cancel_layout = QHBoxLayout()
    f_vlayout.addLayout(ok_cancel_layout)
    f_ok_button = QPushButton(_("OK"))
    ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(ok_handler)
    f_cancel_button = QPushButton("Cancel")
    ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(f_dialog.close)
    update()
    save()
    f_dialog.move(0, 0)
    f_dialog.exec(center=False)
    return f_dialog.retval

