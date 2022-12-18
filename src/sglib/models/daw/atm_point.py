from sglib.math import clip_value
from sglib.models.stargate import *
from sglib.lib.util import *
from sglib.lib.translate import _


class DawAtmPoint:
    __slots__ = [
        'beat',
        'port_num',
        'cc_val',
        'index',
        'plugin_index',
        'break_after',
        'curve',
    ]
    def __init__(
        self,
        a_beat,
        a_port_num,
        a_cc_val,
        a_index,
        a_plugin_index,
        a_break_after=0,
        a_curve=0.0,
    ):
        self.beat = round(float(a_beat), 4)
        self.port_num = int(a_port_num)
        self.cc_val = round(float(a_cc_val), 4)
        self.index = int(a_index) # Now means plugin pool UID
        self.plugin_index = int(a_plugin_index) # UID of the plugin
        self.break_after = int(a_break_after)
        assert self.break_after in (0, 1), str(a_break_after)
        # Doesn't do anything yet, just adding it to the file format now
        # so I don't have to code around it later
        self.curve = float(a_curve)

    def set_val(self, a_val):
        self.cc_val = clip_value(float(a_val), 0.0, 127.0, True)

    def __lt__(self, other):
        return self.beat < other.beat

#    def __eq__(self, other):
#        return (
#            (self.track == other.track) and
#            (self.beat == other.beat) and
#            (self.port_num == other.port_num) and
#            (self.cc_val == other.cc_val) and
#            (self.index == other.index) and
#            (self.plugin_index == other.plugin_index))

    def __str__(self):
        return "|".join(str(x) for x in (
            self.beat, self.port_num, self.cc_val,
            self.index, self.plugin_index, self.break_after, self.curve))

    @staticmethod
    def from_arr(a_arr):
        f_result = DawAtmPoint(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return DawAtmPoint.from_arr(f_arr)

    def clone(self):
        return DawAtmPoint.from_str(str(self))


