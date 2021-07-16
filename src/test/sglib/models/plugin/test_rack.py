from sglib.models.plugin.rack import PluginRack

def test_init():
    PluginRack(
        0,
        "name",
        [1, 2, 4],
    )

