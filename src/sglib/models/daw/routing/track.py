

class TrackSend:
    def __init__(
        self,
        a_track_num,
        a_index,
        a_output,
        conn_type,
    ):
        """
            @a_track_num: int, The source track
            @a_index:     int, The index of this TrackSend in the track
            @a_output:    int, The destination track
            conn_type:    int, 0: normal, 1 sidechain, 2: MIDI
        """
        self.track_num = int(a_track_num)
        self.index = int(a_index)
        self.output = int(a_output)
        self.conn_type = int(conn_type)

    def __str__(self):
        return "|".join(
            str(x) for x in (
                "s",
                self.track_num,
                self.index,
                self.output,
                self.conn_type,
            )
        )

    def __lt__(self, other):
        return self.index < other.index

