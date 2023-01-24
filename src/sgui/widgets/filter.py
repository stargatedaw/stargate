from . import _shared
from .control import *
from sglib.lib.translate import _
from sgui.sgqt import *

_FILTER_LOOKUP = {
    "LP2": (0, '2 pole lowpass filter'),
    "LP4": (1, '4 pole lowpass filter'),
    "HP2": (2, '2 pole highpass filter'),
    "HP4": (3, '4 pole highpass filter'),
    "BP2": (4, '2 pole bandpass filter'),
    "BP4": (5, '4 pole bandpass filter'),
    "Notch2": (6, '2 pole notch filter'),
    "Notch4": (7, '4 pole notch filter'),
    "Off": (8, 'No filter'),
    'Ladder4': (9, '4 pole ladder lowpass filter'),
}

_FILTER_TYPES = [
    "BP2",
    "BP4",
    "HP2",
    "HP4",
    "LP2",
    "LP4",
    "Notch2",
    "Notch4",
    'Ladder4',
    "Off",
]

class filter_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_port_dict,
        a_cutoff_port,
        a_res_port,
        a_type_port=None,
        a_label=_("Filter"),
        a_preset_mgr=None,
        knob_kwargs={},
    ):
        self.groupbox = QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.cutoff_knob = knob_control(
            a_size,
            _("Cutoff"),
            a_cutoff_port,
            a_rel_callback,
            a_val_callback,
            20,
            124,
            124,
            _shared.KC_PITCH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Filter cutoff frequency, the frequency to begin '
                'reducing volume at'
            ),
        )
        self.cutoff_knob.add_to_grid_layout(self.layout, 0)
        self.res_knob = knob_control(
            a_size,
            _("Res"),
            a_res_port,
            a_rel_callback,
            a_val_callback,
            -300,
            0,
            -120,
            _shared.KC_TENTH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Filter resonance.  Low values result in a smooth cutoff '
                'after the filter frequency, high values result in a sharp '
                'cutoff and a peak at the cutoff frequency'
            ),
        )
        self.res_knob.add_to_grid_layout(self.layout, 1)
        if a_type_port is not None:
            self.type_combobox = combobox_control(
                90,
                _("Type"),
                a_type_port,
                a_rel_callback,
                a_val_callback,
                [
                    "LP2",
                    "LP4",
                    "HP2",
                    "HP4",
                    "BP2",
                    "BP4",
                    "Notch2",
                    "Notch4",
                    "Off",
                    'Ladder4',
                ],
                a_port_dict,
                a_preset_mgr=a_preset_mgr,
                tooltip=(
                    'Filter type.  LP = Lowpass, HP = Highpass, '
                    'BP = Bandpass, 2 = 2 pole, 4 = 4 pole'
                ),
            )
            self.type_combobox = NestedComboboxControl(
                90,
                "Type",
                a_type_port,
                a_rel_callback,
                a_val_callback,
                _FILTER_LOOKUP,
                _FILTER_TYPES,
                a_port_dict=a_port_dict,
                a_preset_mgr=a_preset_mgr,
                a_default_index=0,
            )
            self.layout.addWidget(self.type_combobox.name_label, 0, 2)
            self.layout.addWidget(self.type_combobox.control, 1, 2)


