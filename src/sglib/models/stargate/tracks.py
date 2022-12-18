from sglib.lib import *
from sglib.lib.util import *


class tracks:
    __slots__ = [
        'tracks',
    ]
    def __init__(self):
        self.tracks = {}

    def reorder(self, a_dict):
        self.tracks = {
            a_dict[k]: self.tracks[k]
            for k in sorted(self.tracks)
        }
        for k, v in self.tracks.items():
            v.track_uid = v.track_pos = k

    def add_track(self, a_index, a_track):
        self.tracks[int(a_index)] = a_track

    def get_names(self):
        return [
            self.tracks[k].name
            for k in sorted(self.tracks)
        ]

    def __str__(self):
        f_result = "".join(
            str(self.tracks[k])
            for k in sorted(self.tracks)
        )
        f_result += terminating_char
        return f_result

    @staticmethod
    def from_str(a_str):
        f_result = tracks()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line != terminating_char:
                f_line_arr = f_line.split("|")
                f_result.add_track(
                    f_line_arr[0],
                    track(*f_line_arr)
                )
        return f_result

class track:
    __slots__ = [
        'track_uid',
        'name',
        'solo',
        'mute',
        'track_pos',
    ]
    def __init__(
        self,
        a_track_uid=-1,
        a_solo=False,
        a_mute=False,
        a_track_pos=-1,
        a_name="track",
    ):
        self.track_uid = int(a_track_uid)
        self.name = str(a_name)
        self.solo = int_to_bool(a_solo)
        self.mute = int_to_bool(a_mute)
        self.set_track_pos(a_track_pos)

    # TODO:  WTH does this do???  Was this supposed to be "show at pos?"
    def set_track_pos(self, a_track_pos):
        self.track_pos = int(a_track_pos)
        assert(self.track_pos >= 0)

    def __str__(self):
        return "{}\n".format(
            "|".join(
                proj_file_str(x) for x in (
                    self.track_uid,
                    bool_to_int(self.solo),
                    bool_to_int(self.mute),
                    self.track_pos,
                    self.name,
                )
            )
        )

