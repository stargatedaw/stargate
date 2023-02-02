from sglib.math import clip_value
from sglib.lib import *
from sglib.lib.util import *


class SgAudioItem:
    def __init__(
        self,
        a_uid,  # The audio pool uid
        a_sample_start=0.0,
        a_sample_end=1000.0,
        a_start_bar=0,
        a_start_beat=0.0,
        a_timestretch_mode=7,
        a_pitch_shift=0.0,
        a_output_track=0,
        a_vol=0.0,
        a_timestretch_amt=1.0,
        a_fade_in=0.0,
        a_fade_out=999.0,
        a_lane_num=0,
        a_pitch_shift_end=0.0,
        a_timestretch_amt_end=1.0,
        a_reversed=False,
        a_crispness=5,
        a_fadein_vol=-18,
        a_fadeout_vol=-18,
        a_paif_automation_uid=0,
        a_send1=-1,
        a_s1_vol=0.0,
        a_send2=-1,
        a_s2_vol=0.0,
        a_s0_sc=False,
        a_s1_sc=False,
        a_s2_sc=False,
    ):
        self.uid = int(a_uid)
        self.sample_start = float(a_sample_start)
        self.sample_end = float(a_sample_end)
        self.start_bar = int(a_start_bar)
        self.start_beat = float(a_start_beat)
        self.time_stretch_mode = int(a_timestretch_mode)
        self.pitch_shift = float(a_pitch_shift)
        self.output_track = int(a_output_track)
        self.vol = round(float(a_vol), 1)
        self.timestretch_amt = float(a_timestretch_amt)
        self.fade_in = float(a_fade_in)
        self.fade_out = float(a_fade_out)
        self.lane_num = int(a_lane_num)
        self.pitch_shift_end = float(a_pitch_shift_end)
        self.timestretch_amt_end = float(a_timestretch_amt_end)
        if isinstance(a_reversed, bool):
            self.reversed = a_reversed
        else:
            self.reversed = int_to_bool(a_reversed)
        self.crispness = int(a_crispness) #This is specific to Rubberband
        self.fadein_vol = int(a_fadein_vol)
        self.fadeout_vol = int(a_fadeout_vol)
        self.paif_automation_uid = int(a_paif_automation_uid)
        self.send1 = int(a_send1)
        self.s1_vol = round(float(a_s1_vol), 1)
        self.send2 = int(a_send2)
        self.s2_vol = round(float(a_s2_vol), 1)
        self.s0_sc = int_to_bool(a_s0_sc)
        self.s1_sc = int_to_bool(a_s1_sc)
        self.s2_sc = int_to_bool(a_s2_sc)

    def set_pos(self, a_bar, a_beat):
        self.start_bar = int(a_bar)
        self.start_beat = float(a_beat)

    def set_fade_in(self, a_value):
        f_value = clip_value(a_value, 0.0, self.fade_out - 1.0)
        self.fade_in = f_value

    def set_fade_out(self, a_value):
        f_value = clip_value(a_value, self.fade_in + 1.0, 999.0)
        self.fade_out = f_value

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return "|".join(
            proj_file_str(x) for x in (
                self.uid,
                self.sample_start,
                self.sample_end,
                self.start_bar,
                self.start_beat,
                self.time_stretch_mode,
                self.pitch_shift,
                self.output_track,
                self.vol,
                self.timestretch_amt,
                self.fade_in,
                self.fade_out,
                self.lane_num,
                self.pitch_shift_end,
                self.timestretch_amt_end,
                bool_to_int(self.reversed),
                int(self.crispness),
                int(self.fadein_vol),
                int(self.fadeout_vol),
                int(self.paif_automation_uid),
                self.send1,
                self.s1_vol,
                self.send2,
                self.s2_vol,
                bool_to_int(self.s0_sc),
                bool_to_int(self.s1_sc),
                bool_to_int(self.s2_sc),
            )
        )


