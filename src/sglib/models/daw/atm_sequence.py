from .atm_point import DawAtmPoint
from sglib.math import cosine_interpolate, linear_interpolate
from sglib.models.stargate import *
from sglib.lib.util import *
from sglib.lib.translate import _


class DawAtmRegion:
    def __init__(self):
        self.plugins = {}
        self.points = []

    def split(self, a_points, a_plugins=None, a_port=None):
        if a_points[0] != 0.0:
            a_points.insert(0, 0.0)
        assert(sorted(a_points) == a_points)
        f_result = []
        if not a_plugins:
            f_points = self.points[:]
        else:
            f_points = [x for x in self.points if x.index in a_plugins]
            if a_port is not None:
                f_points = [x for x in f_points if x.port == a_port]
        for f_p1, f_p2 in zip(a_points, a_points[1:]):
            f_list = [x for x in f_points if x >= f_p1 and x < f_p2]
            f_result.append(f_list)
        f_list = [x for x in f_points if x > a_points[-1]]
        f_result.append(f_list)
        return f_result

    def copy_range_all(self, a_start, a_end):
        return [
            x.clone()
            for x in self.points
            if x.beat >= a_start and x.beat < a_end
        ]

    def copy_range_by_plugins(self, a_start, a_end, a_plugins):
        f_result = [
            x.clone()
            for x in self.points
            if x.beat >= a_start and x.beat < a_end and x.index in a_plugins
        ]
        for x in f_result:
            x.beat -= a_start
        return f_result

    def add_port_list(self, a_point):
        if not a_point.index in self.plugins:
            self.plugins[a_point.index] = {}
        if not a_point.port_num in self.plugins[a_point.index]:
            self.plugins[a_point.index][a_point.port_num] = []

    def add_point(self, a_point):
        self.add_port_list(a_point)
        self.plugins[a_point.index][a_point.port_num].append(a_point)
        self.points.append(a_point)

    def remove_point(self, a_point):
        #self.add_port_list(a_point)
        self.plugins[a_point.index][a_point.port_num].remove(a_point)
        self.points.remove(a_point)

    def get_ports(self, a_index):
        a_index = int(a_index)
        if a_index not in self.plugins:
            return []
        else:
            return sorted(self.plugins[a_index])

    def get_points(self, a_index, a_port_num):
        a_port_num = int(a_port_num)
        a_index = int(a_index)
        if a_index not in self.plugins or \
        a_port_num not in self.plugins[a_index]:
            return []
        else:
            f_result = self.plugins[a_index][a_port_num]
            f_result.sort()
            return f_result

    def clear_range_by_plugins(self, a_start, a_end, a_plugins):
        f_result = [x for x in self.points
            if x.beat >= a_start and x.beat < a_end and x.index in a_plugins]
        for f_point in f_result:
            self.remove_point(f_point)

    def clear_plugins(self, a_plugin_uids):
        f_result = [x for x in self.points if x.index in a_plugin_uids]
        for f_point in f_result:
            self.remove_point(f_point)

    def clear_port(self, a_index, a_port_num):
        f_result = self.get_points(a_index, a_port_num)
        for f_point in f_result:
            self.remove_point(f_point)

    def clear_range(self, a_index, a_port_num, a_start_beat, a_end_beat):
        f_list = self.get_points(a_index, a_port_num)
        if f_list:
            f_new = [x for x in f_list if
                x.beat < a_start_beat or x.beat >= a_end_beat]
            f_result = [x for x in f_list if
                x.beat >= a_start_beat or x.beat < a_end_beat]
            self.plugins[a_index][a_port_num] = f_new
            return f_result

    def smooth_points(
            self, a_index, a_port_num, a_plugin_index, a_points, a_linear):
        """ The new points are appended to a_points so that they can be
            re-selected in the sequencer
        """
        if len(a_points) <= 1:
            return
        a_points.sort()
        f_start = a_points[0]
        f_end = a_points[-1]
        self.clear_range(a_index, a_port_num, f_start.beat, f_end.beat)
        f_inc = 0.0625 # 64th note
        f_result = self.plugins[a_index][a_port_num]
        f_smoother = util.OnePoleLP(f_start.cc_val)
        for f_point, f_next in zip(a_points, a_points[1:]):
            f_beat = f_point.beat + f_inc
            f_val = f_point.cc_val
            f_beat_next = f_next.beat
            f_val_next = f_next.cc_val
            f_result.append(f_point)
            if round(f_val, 3) == round(f_val_next, 3):
                continue
            f_beat_diff = f_beat_next - f_beat
            if f_beat_diff < f_inc:
                f_result.append(f_point)
                continue
            f_inc_count = int(round(f_beat_diff / f_inc))
            for f_i in range(1, f_inc_count + 1):
                if a_linear:
                    f_int_val = linear_interpolate(
                        f_val, f_val_next, (f_i / f_inc_count))
                else:
                    f_int_val = cosine_interpolate(
                        f_val,
                        f_val_next,
                        f_i / f_inc_count,
                    )
                f_int_val = f_smoother.process(f_int_val)
                f_point2 = DawAtmPoint(
                    f_beat, a_port_num, f_int_val, a_index, a_plugin_index)
                f_result.append(f_point2)
                a_points.append(f_point2)
                f_beat += f_inc
        f_result.append(f_end)

    def __str__(self):
        # New file format:
        # lines starting with 'p':  p|plugin_uid|port_count
        # lines starting with 'q':  n|port_num|point_count
        # other lines:  DawAtmPoint
        f_result = []
        for f_index in sorted(self.plugins):
            port_dict = {k:v for k, v in self.plugins[f_index].items() if v}
            if not port_dict:
                continue
            port_len = len(port_dict)
            f_result.append(
                "|".join(str(x) for x in
                ("p", f_index, port_len)))
            for port_num in sorted(port_dict):
                port_list = port_dict[port_num]
                port_list.sort()
                f_result.append(
                    "|".join(str(x) for x in
                    ("q", port_num, len(port_list))))
                for f_point in port_list:
                    f_result.append(str(f_point))
        f_result.append(terminating_char)
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_result = DawAtmRegion()
        for f_line in str(a_str).split("\n"):
            if f_line == terminating_char:
                break
            if f_line[0] in ("p", "q"):
                continue
            f_point = DawAtmPoint.from_str(f_line)
            f_result.add_point(f_point)
        return f_result

