from . import _shared
from .control import combobox_control, knob_control
from sgui.sgqt import QGridLayout, QGroupBox


class FreqSplitter:
    """ COntrols for splitting audio by frequency """
    def __init__(
            self,
            knob_size: int,
            combobox_width: int,
            first_port: int,
            combobox_items: list,
            a_rel_callback,
            a_val_callback,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs: dict={},
            title="Splitter",
        ):
        self.widget = QGroupBox(title)
        self.outputs = []
        self.freqs = []
        self.layout = QGridLayout(self.widget)
        port = first_port
        self.split_count_knob = knob_control(
            knob_size,
            "Splits",
            port,
            a_rel_callback,
            a_val_callback,
            0,
            3,
            0,
            _shared.KC_INTEGER,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs,
            tooltip=(
                'The number of splits in the frequency spectrum'
            )
        )
        self.split_count_knob.control.valueChanged.connect(self.show_splitters)
        port += 1
        self.split_count_knob.add_to_grid_layout(self.layout, 0)
        self.type_combobox = combobox_control(
            64,
            "Type",
            port,
            a_rel_callback,
            a_val_callback,
            ["SVF2", ],
            a_port_dict,
            a_preset_mgr=a_preset_mgr,
            tooltip='The frequency splitting algorithm',
        )
        port += 1
        # self.type_combobox.add_to_grid_layout(self.layout, 5)
        self.res_knob = knob_control(
            knob_size,
            "Res",
            port,
            a_rel_callback,
            a_val_callback,
            -360,
            -10,
            -120,
            _shared.KC_TENTH,
            a_port_dict,
            a_preset_mgr,
            knob_kwargs,
            tooltip=(
                'Filter resonance, how sharply the frequency bands are split'
            ),
        )
        port += 1
        self.res_knob.add_to_grid_layout(self.layout, 10)
        x = 20
        if combobox_items:
            combobox = combobox_control(
                combobox_width,
                "Output1",
                port,
                a_rel_callback,
                a_val_callback,
                combobox_items,
                a_port_dict,
                a_preset_mgr=a_preset_mgr,
                tooltip='The output for this frequency band',
            )
            self.outputs.append(combobox)
            combobox.add_to_grid_layout(self.layout, x)
            port += 1
            x += 1
        for i in range(3):
            knob = knob_control(
                knob_size,
                f"Freq{i + 1}",
                port,
                a_rel_callback,
                a_val_callback,
                30,
                120,
                51 + (i * 24),
                _shared.KC_PITCH,
                a_port_dict,
                a_preset_mgr,
                knob_kwargs,
                tooltip='The cutoff frequency for this frequency band',
            )
            self.freqs.append(knob)
            knob.add_to_grid_layout(self.layout,x)
            x += 1
            port += 1
            if combobox_items:
                combobox = combobox_control(
                    combobox_width,
                    f"Output{i + 2}",
                    port,
                    a_rel_callback,
                    a_val_callback,
                    combobox_items,
                    a_port_dict,
                    a_preset_mgr=a_preset_mgr,
                    tooltip='The output for this frequency band',
                )
                self.outputs.append(combobox)
                combobox.add_to_grid_layout(self.layout, x)
                port += 1
                x += 1
        self.next_port = port
        self.show_splitters()

    def show_splitters(self, value=None):
        value = self.split_count_knob.control.value()
        if value == 0:
            self.outputs[0].hide()
        else:
            self.outputs[0].show()

        for i, knob, combobox in zip(
            range(len(self.freqs)),
            self.freqs,
            self.outputs[1:],
        ):
            if i >= value:
                knob.hide()
                combobox.hide()
            else:
                knob.show()
                combobox.show()

