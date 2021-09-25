from .track import TrackSend
try:
    from sg_py_vendor.pymarshal import pm_assert
except ImportError:
    from pymarshal import pm_assert

MAX_TRACK_SENDS = 16

class RoutingGraph:
    def __init__(self, graph=None):
        """
            @graph:
                {int(track_num): {int(send_index): TrackSend}}
                , where send_index is an arbitrary number starting from zero.
                There may not be more than MAX_TRACK_SENDS track sends.
        """
        self.graph = graph if graph is not None else {}

    def reorder(self, a_dict):
        """
            @a_dict:
                {int: int}, A map of from index, to index
        """
        self.graph = {
            a_dict[k]: v
            for k, v in self.graph.items()
        }
        for k, f_dict in self.graph.items():
            for v in f_dict.values():
                v.track_num = k
                v.output = a_dict[v.output]

    def set_node(self, a_index, a_dict):
        """
            a_index: int, the index to set
            a_dict:  {0: TrackSend(...), ...}
        """
        self.graph[int(a_index)] = a_dict

    def find_all_paths(self, start, end=0, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        if not start in self.graph:
            return []
        paths = []
        for node in (x.output for x in sorted(self.graph[start].values())):
            if node not in path:
                newpaths = self.find_all_paths(node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def check_for_feedback(self, a_new, a_old):
        return self.find_all_paths(a_old, a_new)

    def toggle(
        self,
        a_src,
        a_dest,
        conn_type=0,
    ):
        """
            a_src:     int, The track number of the source
            a_dest:    int, The track number of the destination
            conn_type: int, 0: normal, 1 sidechain, 2: MIDI
        """
        f_connected = (
            a_src in self.graph
            and
            a_dest in [
                x.output
                for x in self.graph[a_src].values()
                if x.conn_type == conn_type
            ]
        )
        if f_connected:
            for k, v in self.graph[a_src].copy().items():
                if v.output == a_dest and v.conn_type == conn_type:
                    self.graph[a_src].pop(k)
        else:
            if self.check_for_feedback(a_src, a_dest):
                return "Can't make connection, it would create a feedback loop"
            if a_src in self.graph and len(self.graph[a_src]) >= MAX_TRACK_SENDS:
                return ("All available sends already in use for "
                    "track {}".format(a_src))
            if not a_src in self.graph:
                f_i = 0
                self.graph[a_src] = {}
            else:
                for f_i in range(MAX_TRACK_SENDS):
                    if f_i not in self.graph[a_src]:
                        break
            f_result = TrackSend(a_src, f_i, a_dest, conn_type)
            self.graph[a_src][f_i] = f_result
            self.set_node(a_src, self.graph[a_src])
        return None

    def set_default_output(
        self,
        a_track_num,
        a_output=0,
    ):
        """ Set a track to the default output (by default, track:0, main),
            only if the track has no other connections.

            @a_track_num: int, The track number to set a default output for
            @a_output:    int, The track number to connect @a_track_num to
        """
        assert(a_track_num != a_output)
        assert(a_track_num != 0)
        if (
            a_track_num not in self.graph
            or
            not self.graph[a_track_num]
        ):
            f_send = TrackSend(a_track_num, 0, a_output, 0)
            self.set_node(a_track_num, {0:f_send})
            return True
        else:
            return False

    def sort_all_paths(self):
        f_result = {}
        for f_path in self.graph:
            f_paths = self.find_all_paths(f_path, 0)
            if f_paths:
                f_result[f_path] = max(len(x) for x in f_paths)
            else:
                f_result[f_path] = 0
        return sorted(
            f_result,
            key=lambda x: f_result[x],
            reverse=True,
        )

    def __str__(self):
        f_result = []
        f_sorted = self.sort_all_paths()
        f_result.append("|".join(str(x) for x in ("c", len(f_sorted))))
        for f_index, f_i in zip(f_sorted, range(len(f_sorted))):
            f_result.append("|".join(str(x) for x in ("t", f_index, f_i)))
        for k in sorted(self.graph):
            for v in sorted(self.graph[k].values()):
                f_result.append(str(v))
        f_result.append("\\")
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_str = str(a_str)
        f_result = RoutingGraph()
        f_tracks = {}
        for f_line in f_str.split("\n"):
            if f_line == "\\":
                break
            f_line_arr = f_line.split("|")
            f_uid = int(f_line_arr[1])
            pm_assert(
                f_line_arr[0] in ('t', 's', 'c'),
                IndexError,
            )
            if f_line_arr[0] == "t":
                assert(f_uid not in f_tracks)
                f_tracks[f_uid] = {}
            elif f_line_arr[0] == "s":
                f_send = TrackSend(*f_line_arr[1:])
                f_tracks[f_uid][f_send.index] = f_send
            elif f_line_arr[0] == "c":
                pass
        for k, v in f_tracks.items():
            f_result.set_node(k, v)
        return f_result

