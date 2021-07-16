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


class PluginRack:
    def __init__(
        self,
        uid,
        name,
        plugin_uids,
        tags=None,
    ):
        self.uid = type_assert(uid, int)
        self.name = type_assert(name, str)
        self.plugin_uids = type_assert_iter(
            plugin_uids,
            int,
            desc="""
                The plugin uids associated with this rack, or -1 for empty
                slots.
            """
        )
        self.tags = type_assert_dict(
            tags,
            kcls=str,
            vcls=str,
            dynamic={},
            desc="Tags used for categorizing plugin racks",
        )

    @staticmethod
    def new(
        uid,
        name,
        tags,
    ):
        return PluginRack(
            uid,
            name,
            [-1] * 10,
            tags,
        )

