try:
    from sg_py_vendor.pymarshal import (
        type_assert,
        type_assert_dict,
        type_assert_iter,
    )
except ImportError:
    from pymarshal import (
        type_assert,
        type_assert_dict,
        type_assert_iter,
    )


__all__ = [
    "Preset",
    "PresetBank",
]

class Preset:
    def __init__(
        self,
        name,
        controls,
        custom,
    ):
        self.name = type_assert(
            name,
            str,
            check=lambda x: len(x) < 24,
            desc="The display name of the preset",
        )
        self.controls = type_assert_dict(
            controls,
            kcls=int,  # control number
            vcls=int,  # value
            desc="The control values for the plugin",
        )
        self.custom = type_assert_dict(
            custom,
            kcls=str,  # name
            vcls=str,  # value
            desc="The custom control values for the plugin",
        )

class PresetBank:
    def __init__(
        self,
        plugin_uid,
        presets,
    ):
        self.plugin_uid = type_assert(
            plugin_uid,
            int,
            desc="The uid of the plugin this preset bank is for",
        )
        self.presets = type_assert_iter(
            presets,
            Preset,
            desc="The presets in this bank",
        )

