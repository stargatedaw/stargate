from sglib.math import clip_value, db_to_lin, np_resample
from sglib.models.stargate import *
from sglib.lib.util import *
from sglib.lib.translate import _
import numpy


class DawAudioItem(SgAudioItem):
    def clip_at_sequence_end(
        self,
        a_sequence_length,
        a_tempo,
        a_sample_length_seconds,
        a_truncate=True
    ):
        f_sequence_length_beats = a_sequence_length
        f_seconds_per_beat = (60.0 / a_tempo)
        f_sequence_length_seconds = (
            f_seconds_per_beat * f_sequence_length_beats
        )
        f_item_start_beats = self.start_beat
        f_item_start_seconds = f_item_start_beats * f_seconds_per_beat
        f_sample_start_seconds = (
            self.sample_start * 0.001 * a_sample_length_seconds)
        f_sample_end_seconds = (
            self.sample_end * 0.001 * a_sample_length_seconds)
        f_actual_sample_length = f_sample_end_seconds - f_sample_start_seconds
        f_actual_item_end = f_item_start_seconds + f_actual_sample_length

        if a_truncate and f_actual_item_end > f_sequence_length_seconds:
            f_new_item_end_seconds = (f_sequence_length_seconds -
                f_item_start_seconds) + f_sample_start_seconds
            f_new_item_end = (
                f_new_item_end_seconds / a_sample_length_seconds) * 1000.0
            print("clip_at_sequence_end:  new end: {}".format(f_new_item_end))
            self.sample_end = f_new_item_end
            return True
        elif not a_truncate:
            f_new_start_seconds = \
                f_sequence_length_seconds - f_actual_sample_length
            f_beats_total = f_new_start_seconds / f_seconds_per_beat
            self.start_beat = f_beats_total
            return True
        else:
            return False

    def clone(self):
        return DawAudioItem.from_arr(str(self).strip("\n").split("|"))

    @staticmethod
    def from_str(f_str):
        return DawAudioItem.from_arr(f_str.split("|"))

    @staticmethod
    def from_arr(a_arr):
        f_result = DawAudioItem(*a_arr)
        return f_result


def envelope_to_automation(self, a_is_cc, a_tempo):
    " In the automation viewer clipboard format "
    f_list = [(x if x > y else y) for x, y in
        zip([abs(x) for x in self.high_peaks[0]],
            [abs(x) for x in reversed(self.low_peaks[0])])]
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_length_beats = self.length_in_seconds / f_seconds_per_beat
    f_point_count = int(f_length_beats * 16.0)
    print("Resampling {} to {}".format(len(f_list), f_point_count))
    f_result = []
    f_arr = numpy.array(f_list)
    #  Smooth the array by sampling smaller and then larger
    f_arr = np_resample(f_arr, int(f_length_beats * 4.0))
    f_arr = np_resample(f_arr, f_point_count)
    f_max = numpy.amax(f_arr)
    if f_max > 0.0:
        f_arr *= (1.0 / f_max)
    for f_point, f_pos in zip(f_arr, range(f_arr.shape[0])):
        f_start = (float(f_pos) / float(f_arr.shape[0])) * \
            f_length_beats
        f_index = int(f_start / 4.0)
        f_start = f_start % 4.0
        if a_is_cc:
            f_val = clip_value(f_point * 127.0, 0.0, 127.0)
            f_result.append((cc(f_start, 0, f_val), f_index))
        else:
            f_val = clip_value(f_point, 0.0, 1.0)
            f_result.append((pitchbend(f_start, f_val), f_index))
    return f_result

def envelope_to_notes(self, a_tempo):
    " In the piano roll clipboard format "
    f_list = [(x if x > y else y) for x, y in
        zip([abs(x) for x in self.high_peaks[0]],
            [abs(x) for x in reversed(self.low_peaks[0])])]
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_length_beats = self.length_in_seconds / f_seconds_per_beat
    f_point_count = int(f_length_beats * 16.0)  # 64th note resolution
    print("Resampling {} to {}".format(len(f_list), f_point_count))
    f_result = []
    f_arr = numpy.array(f_list)
    f_arr = np_resample(f_arr, f_point_count)
    f_current_note = None
    f_max = numpy.amax(f_arr)
    if f_max > 0.0:
        f_arr *= (1.0 / f_max)
    f_thresh = db_to_lin(-24.0)
    f_has_been_less = False

    for f_point, f_pos in zip(f_arr, range(f_arr.shape[0])):
        f_start = (float(f_pos) / float(f_arr.shape[0])) * \
            f_length_beats
        if f_point > f_thresh:
            if not f_current_note:
                f_has_been_less = False
                f_current_note = [f_start, 0.25, f_point, f_point]
            else:
                if f_point > f_current_note[2]:
                    f_current_note[2] = f_point
                else:
                    f_has_been_less = True
                if f_point < f_current_note[3]:
                    f_current_note[3] = f_point
                if f_has_been_less and \
                f_point >= f_current_note[3] * 2.0:
                    f_current_note[1] = f_start - f_current_note[0]
                    f_result.append(f_current_note)
                    f_current_note = [f_start, 0.25, f_point, f_point]
        else:
            if f_current_note:
                f_current_note[1] = f_start - f_current_note[0]
                f_result.append(f_current_note)
                f_current_note = None
    f_result2 = []
    for f_pair in f_result:
        f_index = int(f_pair[0] / 4.0)
        f_start = f_pair[0] % 4.0
        f_vel = clip_value((f_pair[2] * 70.0) + 40.0, 1.0, 127.0)
        f_result2.append(
            (str(note(f_start, f_pair[1], 60, f_vel)), f_index))
    return f_result2


