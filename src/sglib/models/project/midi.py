try:
    from sg_py_vendor.pymarshal import type_assert
except ImportError:
    from pymarshal import type_assert


class MIDIConfig:
    def __init__(
        self,
        default_key,
        default_scale,
    ):
        self.default_key = type_assert(
            default_key,
            str,
            desc="The default key to use in MIDI editors",
        )
        self.default_scale = type_assert(
            default_scale,
            str,
            desc="The default scale to use in MIDI editors",
        )

    @staticmethod
    def new():
        return MIDIConfig(
            "C",
            "Major",
        )

