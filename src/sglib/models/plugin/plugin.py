from collections import defaultdict
try:
    from sg_py_vendor.pymarshal import type_assert, type_assert_iter
except ImportError:
    from pymarshal import type_assert, type_assert_iter


class PluginControl:
    def __init__(
        self,
        num,
        value,
    ):
        self.num = type_assert(
            num,
            int,
            desc="The controller number",
        )
        self.value = type_assert(
            value,
            int,
            desc="The controller value",
        )

class PluginCustomControl:
    _marshal_list_row_header = 'c'
    def __init__(
        self,
        name,
        value,
    ):
        self.name = type_assert(
            name,
            str,
            check=lambda x: all(y not in x for y in ('|', '\\')),
            desc="The name of the custom control",
        )
        self.value = type_assert(
            value,
            str,
            # TODO: Fully switch the engine to csv to make this not necessary
            check=lambda x: '\\' not in x,
            desc="The value of the custom control",
        )

class PluginCCMapping:
    def __init__(
        self,
        cc_num,
        port_num,
        min_value,
        max_value,
    ):
        self.cc_num = type_assert(
            cc_num,
            int,
            desc="The MIDI CC# that maps to @port_num",
        )
        self.port_num = type_assert(
            port_num,
            int,
            desc="The control port# that is controlled by @cc_num",
        )
        self.min_value = type_assert(
            min_value,
            int,
            desc="The port value when CC value == 0",
        )
        self.max_value = type_assert(
            max_value,
            int,
            desc="The port value when CC value == 127",
        )

class PluginMeta:
    """ Metadata for a plugin  """
    _marshal_list_row_header = 'm'
    def __init__(
        self,
        uid,
        plugin_id,
        power=False,
    ):
        self.uid = type_assert(uid, int)
        self.plugin_id = type_assert(
            plugin_id,
            int,
            desc="The numeric plugin ID",
        )
        self.power = type_assert(
            power,
            int,
            cast_from=bool,
            choices=(0, 1),
            desc="0 to power off the rack, 1 to power on",
        )

class Plugin:
    def __init__(
        self,
        meta,
        controls,
        custom,
        cc_map,
    ):
        self.meta = type_assert(
            meta,
            PluginMeta,
            desc="Metadata about this plugin instance",
        )
        self.controls = type_assert_iter(
            controls,
            PluginControl,
            desc="The control numbers and values associated with this plugin",
        )
        self.custom = type_assert_iter(
            custom,
            PluginCustomControl,
            desc="The custom plugin controls associated with this plugin",
        )
        self.cc_map = type_assert_iter(
            cc_map,
            PluginCCMapping,
            desc="The CC mappings associated with this plugin instance",
        )

    def control_lookups(self):
        control = {x.num: x for x in self.controls}
        custom = {x.name: x for x in self.custom}
        return control, custom

    def ccs_by_cc(self):
        result = defaultdict(list)
        for cc in self.cc_map:
            result[cc.cc_num].append(cc)
        return result

    def ccs_by_port_num(self):
        result = defaultdict(list)
        for cc in self.cc_map:
            result[cc.port_num].append(cc)
        return result

    def __iter__(self):
        yield self.meta
        for x in self.cc_map:
            yield x
        for x in self.custom:
            yield x
        for x in self.controls:
            yield x

