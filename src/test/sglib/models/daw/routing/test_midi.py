from sglib.models.daw.routing import MIDIRoute, MIDIRoutes


def test_to_from_str_reorder():
    routes = MIDIRoutes([
        MIDIRoute(1, 1, "name"),
    ])
    _str = str(routes)
    from_str = MIDIRoutes.from_str(_str)
    assert from_str.routings[0].__dict__ == {
        "on": 1,
        "track_num": 1,
        "device_name": "name",
    }, from_str.routings[0].__dict__
    from_str.reorder({1: 2})
    assert from_str.routings[0].__dict__ == {
        "on": 1,
        "track_num": 2,
        "device_name": "name",
    }, from_str.routings[0].__dict__

