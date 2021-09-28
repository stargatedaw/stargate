from sglib.models.daw.routing import RoutingGraph, TrackSend


def test_to_from_str():
    graph = RoutingGraph()
    graph.set_node(1, {0: TrackSend(1, 0, 0, 0)})
    _str = str(graph)
    from_str = RoutingGraph.from_str(_str)
    node = from_str.graph[1][0]
    assert node.__dict__ == {
        "track_num": 1,
        "index": 0,
        "output": 0,
        "conn_type": 0,
    }, node.__dict__

def test_toggle():
    graph = RoutingGraph()
    graph.toggle(1, 0)
    # Attempt to create feedback
    msg = graph.toggle(0, 1)
    assert msg is not None, msg

    node = graph.graph[1][0]
    assert node.__dict__ == {
        "track_num": 1,
        "index": 0,
        "output": 0,
        "conn_type": 0,
    }, node.__dict__
    graph.toggle(1, 0)
    assert not graph.graph[1]

def test_toggle_too_many_sends():
    graph = RoutingGraph()
    for i in range(18):
        msg = graph.toggle(20, i)
    assert msg is not None, msg

def test_sort_all_paths_no_master():
    graph = RoutingGraph()
    graph.toggle(6, 3)
    result = graph.sort_all_paths()
    assert result == [6], result

def test_set_default_output():
    graph = RoutingGraph()
    graph.set_default_output(1)
    assert not graph.set_default_output(1)
    node = graph.graph[1][0]
    assert node.__dict__ == {
        "track_num": 1,
        "index": 0,
        "output": 0,
        "conn_type": 0,
    }, node.__dict__

def test_reorder():
    graph = RoutingGraph()
    graph.set_node(1, {0: TrackSend(1, 0, 0, 0)})
    graph.reorder({0: 0, 1: 2})
    node = graph.graph[2][0]
    assert node.__dict__ == {
        "track_num": 2,
        "index": 0,
        "output": 0,
        "conn_type": 0,
    }, node.__dict__

