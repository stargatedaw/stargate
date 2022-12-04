from . import _shared
from .control import *
from .note_selector import NoteSelectorWidget
from sglib.lib.translate import _
from sgui.sgqt import *


class main_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_vol_port,
        a_glide_port,
        a_pitchbend_port,
        a_port_dict,
        a_title=_("Main"),
        a_uni_voices_port=None,
        a_uni_spread_port=None,
        a_preset_mgr=None,
        a_poly_port=None,
        a_min_note_port=None,
        a_max_note_port=None,
        a_pitch_port=None,
        a_pb_min=1,
        knob_kwargs={},
    ):
        self.group_box = QGroupBox()
        self.group_box.setObjectName("plugin_groupbox")
        self.group_box.setTitle(str(a_title))
        self.layout = QGridLayout(self.group_box)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.vol_knob = knob_control(
            a_size,
            _("Vol"),
            a_vol_port,
            a_rel_callback,
            a_val_callback,
            -30,
            12,
            -6,
            _shared.KC_INTEGER,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip='Master volume for the entire plugin',
        )
        self.vol_knob.add_to_grid_layout(self.layout, 0)
        if a_uni_voices_port is not None and a_uni_spread_port is not None:
            self.uni_voices_knob = knob_control(
                a_size,
                _("Unison"),
                a_uni_voices_port,
                a_rel_callback,
                a_val_callback,
                1,
                7,
                1,
                _shared.KC_INTEGER,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    'Unison voices for the entire plugin.  Gives a thicker '
                    'sound'
                ),
            )
            self.uni_voices_knob.add_to_grid_layout(self.layout, 1)
            self.uni_spread_knob = knob_control(
                a_size,
                _("Spread"),
                a_uni_spread_port,
                a_rel_callback,
                a_val_callback,
                10,
                100,
                50,
                _shared.KC_DECIMAL,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    'Unison detune.  Lower values sound thinner, larger '
                    'values sound bigger but more discordant'
                ),
            )
            self.uni_spread_knob.add_to_grid_layout(self.layout, 2)
        if a_pitch_port is not None:
            self.pitch_knob = knob_control(
                a_size,
                _("Pitch"),
                a_pitch_port,
                a_rel_callback,
                a_val_callback,
                -36,
                36,
                0,
                _shared.KC_INTEGER,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    'Instrument pitch offset in semitones.  Adjust the '
                    'pitch of all incoming MIDI notes'
                ),
            )
            self.pitch_knob.add_to_grid_layout(self.layout, 4)
        self.glide_knob = knob_control(
            a_size,
            _("Glide"),
            a_glide_port,
            a_rel_callback,
            a_val_callback,
            0,
            200,
            0,
            _shared.KC_TIME_DECIMAL,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Glide time.  Values greater than 0.0 causes consecutive '
                'MIDI notes to take that much time to glide to the next '
                'pitch'
            ),
        )
        self.glide_knob.add_to_grid_layout(self.layout, 5)
        self.pb_knob = knob_control(
            a_size,
            _("Pitchbend"),
            a_pitchbend_port,
            a_rel_callback,
            a_val_callback,
            a_pb_min,
            36,
            18,
            _shared.KC_INTEGER,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Pitchbend in semitones.  The amount that pitch should bend '
                'when the pitchbend wheel is fully up or down'
            ),
        )
        self.pb_knob.add_to_grid_layout(self.layout, 6)
        if a_poly_port is not None:
            self.mono_combobox = combobox_control(
                90,
                "Poly Mode",
                a_poly_port,
                a_rel_callback,
                a_val_callback,
                ["Retrig.", "Free", "Mono", "Mono2"],
                a_port_dict,
                0,
                a_preset_mgr,
                tooltip=(
                    'Polyphony mode. Retrig: Oscillators retrigger their '
                    'phase on a new note. Free: Oscillators do not retrigger'
                    'on a new note. Mono/2: For instruments that only play '
                    'one note at a time'
                )
            )
            self.mono_combobox.add_to_grid_layout(self.layout, 7)
        if a_min_note_port or a_max_note_port:
            assert(a_min_note_port and a_max_note_port)
            self.min_note = NoteSelectorWidget(
                a_min_note_port,
                a_rel_callback,
                a_val_callback,
                a_port_dict,
                0, a_preset_mgr,
            )
            self.max_note = NoteSelectorWidget(
                a_max_note_port,
                a_rel_callback,
                a_val_callback,
                a_port_dict,
                120,
                a_preset_mgr,
            )
            self.min_note.widget.setObjectName('transparent')
            self.max_note.widget.setObjectName('transparent')
            self.range_label = QLabel(_("Range"))
            self.range_label.setObjectName("plugin_name_label")
            self.layout.addWidget(
                self.range_label,
                0,
                9,
                alignment=QtCore.Qt.AlignmentFlag.AlignHCenter,
            )
            self.layout.addWidget(self.min_note.widget, 1, 9)
            self.layout.addWidget(self.max_note.widget, 2, 9)


