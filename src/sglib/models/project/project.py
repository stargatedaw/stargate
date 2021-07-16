from .midi import MIDIConfig
try:
    from sg_py_vendor.pymarshal import type_assert, type_assert_iter
except ImportError:
    from pymarshal import type_assert, type_assert_iter


class GlobalProject:
    """ Contains settings global to all sub-projects  """
    def __init__(
        self,
        midi_config,
    ):
        self.midi_config = type_assert(
            midi_config,
            MIDIConfig,
        )

    @staticmethod
    def new():
        return GlobalProject(
            MIDIConfig.new(),
        )

