from sglib.lib import *
from sglib.lib.util import *


class AudioInputTracks:
    def add_track(self, a_index, a_track):
        self.tracks[a_index] = a_track

    def __init__(self):
        self.tracks = {}

    def __str__(self):
        f_result = []
        for k, v in list(self.tracks.items()):
            f_result.append("{}|{}".format(k, v))
        f_result.append(terminating_char)
        return "\n".join(f_result)

    def reorder(self, a_dict):
        for f_track in self.tracks.values():
            if f_track.output in a_dict:
                print(
                    "AudioInputTracks.reorder : {} : {}".format(
                        f_track.output,
                        a_dict[f_track.output],
                    ),
                )
                f_track.output = a_dict[f_track.output]

    @staticmethod
    def from_str(a_str):
        f_result = AudioInputTracks()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line == terminating_char:
                break
            else:
                f_line_arr = f_line.split("|")
                f_result.add_track(
                    int(f_line_arr[0]),
                    AudioInputTrack(*f_line_arr[1:]),
                )
        return f_result

class AudioInputTrack:
    def __init__(
        self,
        a_rec=0,
        a_monitor=0,
        a_vol=0.0,
        a_output=0,
        a_stereo=-1,
        a_sidechain=0,
        a_name="",
    ):
        self.rec = int(a_rec)
        self.monitor = int(a_monitor)
        self.output = int(a_output)
        self.vol = float(a_vol)
        self.name = str(a_name)
        self.stereo = int(a_stereo)
        self.sidechain = int(a_sidechain)

    def __str__(self):
        return "|".join(
            str(x) for x in (
                self.rec,
                self.monitor,
                self.vol,
                self.output,
                self.stereo,
                self.sidechain,
                self.name,
            )
        )


