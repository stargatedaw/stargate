from sglib.models.daw.routing import TrackSend


def test_lt():
    ts1 = TrackSend(1, 0, 0, 0)
    ts2 = TrackSend(1, 2, 0, 0)
    assert ts1 < ts2

