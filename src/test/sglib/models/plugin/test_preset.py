from sglib.models.plugin.preset import *


def test_preset_bank():
    PresetBank(
        0,
        [
            Preset(
                "test",
                {0: 123, 1: 45},
                {"custom": "control"}
            ),
        ],
    )
