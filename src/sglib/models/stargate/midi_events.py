from sglib.math import clip_value
from sglib.lib import *
from sglib.lib.util import *


class abstract_midi_event:
    """ Allows inheriting classes to be sorted by .start variable
    , which is left to the iheriter's to implement"""
    def __lt__(self, other):
        return self.start < other.start

class note(abstract_midi_event):
    def __init__(self, a_start, a_length, a_note_number, a_velocity):
        self.start = round(float(a_start), 6)
        self.length = round(float(a_length), 6)
        self.velocity = int(a_velocity)
        self.note_num = int(a_note_number)
        self.is_selected = False
        self.set_end()

    def __eq__(self, other):
        return(
            self.start == other.start
            and
            self.note_num == other.note_num
            and
            self.length == other.length
            and
            self.velocity == other.velocity
        )

    def set_start(self, a_start):
        self.start = round(float(a_start), 6)
        self.set_end()

    def set_length(self, a_length):
        self.length = round(float(a_length), 6)
        self.set_end()

    def set_end(self):
        self.end = round(self.length + self.start, 6)

    def overlaps(self, other):
        if self.note_num == other.note_num:
            if (
                other.start >= self.start
                and
                other.start < self.end
            ):
                return True
            elif (
                other.start < self.start
                and
                other.end > self.start
            ):
                return True
        return False

    @staticmethod
    def from_arr(a_arr):
        f_result = note(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return note.from_arr(f_arr[1:])

    def __str__(self):
        return "|".join(
            str(x) for x in (
                "n",
                round(self.start, 6),
                round(self.length, 6),
                self.note_num,
                self.velocity,
            )
        )

    def clone(self):
        return note.from_str(str(self))


class cc(abstract_midi_event):
    def __init__(self, a_start, a_cc_num, a_cc_val):
        self.start = round(float(a_start), 6)
        self.cc_num = int(a_cc_num)
        self.cc_val = round(float(a_cc_val), 6)

    def __eq__(self, other):
        return (
            self.start == other.start
            and
            self.cc_num == other.cc_num
            and
            self.cc_val == other.cc_val
        )

    def set_val(self, a_val):
        self.cc_val = clip_value(float(a_val), 0.0, 127.0, True)

    def __str__(self):
        return "|".join(
            str(x) for x in (
                "c",
                round(self.start, 6),
                self.cc_num,
                round(self.cc_val, 6),
            )
        )

    @staticmethod
    def from_arr(a_arr):
        f_result = cc(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return cc.from_arr(f_arr[1:])

    def clone(self):
        return cc.from_str(str(self))


class pitchbend(abstract_midi_event):
    def __init__(self, a_start, a_pb_val):
        self.start = round(float(a_start), 6)
        self.pb_val = round(float(a_pb_val), 6)

    def __eq__(self, other):
        #TODO:  get rid of the pb_val comparison?
        return (
            self.start == other.start
            and
            self.pb_val == other.pb_val
        )

    def set_val(self, a_val):
        self.pb_val = clip_value(float(a_val), -1.0, 1.0, True)

    def __str__(self):
        return "|".join(
            str(x) for x in (
                "p",
                self.start,
                round(self.pb_val, 6),
            )
        )

    @staticmethod
    def from_arr(a_arr):
        f_result = pitchbend(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pitchbend.from_arr(f_arr[1:])

    def clone(self):
        return pitchbend.from_str(str(self))

