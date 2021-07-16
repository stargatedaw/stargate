from sglib.models.plugin.plugin import (
    Plugin,
    PluginCCMapping,
    PluginControl,
    PluginCustomControl,
    PluginMeta,
)


def test_lookups_to_list():
    plugin = Plugin(
        PluginMeta(
            0,
            12,
            1,
        ),
        [
            PluginControl(0, 0),
        ],
        [
            PluginCustomControl('name', 'value'),
        ],
        [
            PluginCCMapping(21, 51, 100, 200),
        ],
    )
    control, custom = plugin.control_lookups()
    control[0].value = 120
    assert plugin.controls[0].value == 120, plugin.controls[0].value
    ccs_by_cc = plugin.ccs_by_cc()
    assert 21 in ccs_by_cc, ccs_by_cc
    ccs_by_port_num = plugin.ccs_by_port_num()
    assert 51 in ccs_by_port_num, ccs_by_port_num
    _list = list(plugin)
    assert len(_list) == 4, _list

