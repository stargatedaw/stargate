
class sequencer_item:
    __slots__ = [
        'track_num',
        'start_beat',
        'length_beats',
        'item_uid',
        'start_offset',
        'modified',
        'uid',
    ]
    def __init__(
        self,
        a_track_num,
        a_start_beat,
        a_length_beats,
        a_item_uid=-1,
        a_start_pos=0.0,
        modified=True,
    ):
        self.track_num = int(a_track_num)
        self.start_beat = float(a_start_beat)
        self.length_beats = float(a_length_beats)
        self.item_uid = int(a_item_uid)
        self.start_offset = float(a_start_pos)
        #self.sample_start = float(a_start_pos)
        self.modified = modified

    def clone(self):
        f_self = str(self).split("|")
        return sequencer_item(*f_self)

    def __str__(self):
        assert self.item_uid >= 0, "Negative UID"
        return "|".join(
            str(x) for x in (
                self.track_num,
                round(self.start_beat, 6),
                round(self.length_beats, 6),
                self.item_uid,
                round(self.start_offset, 6),
            )
        )

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other):
        if self.track_num == other.track_num:
            return ((self.start_beat < other.start_beat) or
                (self.start_beat == other.start_beat and not self.modified))
        else:
            return self.track_num < other.track_num

