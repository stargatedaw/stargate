

class TrackSend:
    def __init__(
        self,
        a_track_num,
        a_index,
        a_output,
        a_sidechain,
    ):
        """
            @a_track_num: int, The source track
            @a_index:     int, The index of this TrackSend in the track
            @a_output:    int, The destination track
            @a_sidechain:
                int, Name is no longer accurate, is now ->type in the C struct
                0 == normal audio, 1 == sidechain audio, 2 == MIDI
        """
        self.track_num = int(a_track_num)
        self.index = int(a_index)
        self.output = int(a_output)
        self.sidechain = int(a_sidechain)

    def __str__(self):
        return "|".join(
            str(x) for x in (
                "s",
                self.track_num,
                self.index,
                self.output,
                self.sidechain,
            )
        )

    def __lt__(self, other):
        return self.index < other.index

