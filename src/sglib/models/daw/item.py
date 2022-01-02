from sglib.models.stargate import *
from sglib.lib.util import *

from . import _shared
from .audio_item import DawAudioItem
from sglib.math import clip_value
from sglib import constants
from sglib.log import LOG
from sglib.models.multifx_settings import multifx_settings
from sglib.lib.translate import _
import traceback


MAX_AUDIO_ITEM_COUNT = 256

class item:
    def __init__(self, a_uid):
        self.items = {}  # audio items:  TODO rename
        self.notes = []
        self.ccs = []
        self.pitchbends = []
        self.uid = int(a_uid)
        self.fx_list = {} #per-audio-item-fx

    def get_next_lane(self):
        f_lanes = set(x.lane_num for x in self.items.values())
        for f_i in range(24):
            if f_i not in f_lanes:
                return f_i
        return 0

    def get_length(self, a_tempo=None):
        f_result = 0.0

        for f_note in self.notes:
            f_end = f_note.start + f_note.length
            if f_end > f_result:
                f_result = f_end

        for f_ev in self.ccs + self.pitchbends:
            if f_ev.start > f_result:
                f_result = f_ev.start

        if a_tempo:
            f_spb = 60.0 / a_tempo
            for f_item in self.items.values():
                f_graph = constants.PROJECT.get_sample_graph_by_uid(
                    f_item.uid,
                )
                frac = (f_item.sample_end - f_item.sample_start) * 0.001
                f_end = (
                    (f_graph.length_in_seconds * frac) / f_spb
                ) + f_item.start_beat
                if f_end > f_result:
                    f_result = f_end

        return f_result

    def confine_audio_items(self, a_ref, a_tempo):
        f_to_delete = []
        f_start = a_ref.start_offset
        f_end = a_ref.length_beats + f_start

        f_spb = 60.0 / a_tempo
        f_min_len = f_spb / 16.0
        for k, v in self.items.items():
            f_item_start = v.start_beat
            if f_item_start > f_end:
                LOG.info("Delete after {} {}".format(f_item_start, f_end))
                f_to_delete.append(k)
                continue
            f_graph = constants.PROJECT.get_sample_graph_by_uid(v.uid)
            f_ss, f_se = (x * 0.001 for x in (v.sample_start, v.sample_end))
            f_diff = f_se - f_ss
            f_end_beat = ((f_graph.length_in_seconds / f_spb) *
                f_diff) + f_item_start
            if f_end_beat < f_start:
                LOG.info("Delete before {} {}".format(f_end_beat, f_start))
                f_to_delete.append(k)
                continue
            if f_item_start < f_start:
                f_beat_diff = f_start - f_item_start
                f_seconds = f_spb * f_beat_diff
                f_offset = (f_seconds / f_graph.length_in_seconds) * 1000.0
                v.sample_start += f_offset
                v.start_beat = f_start
                LOG.info("LT")
            if f_end_beat > f_end:
                f_beat_diff = f_end_beat - f_end
                f_seconds = f_spb * f_beat_diff
                f_offset = (f_seconds / f_graph.length_in_seconds) * 1000.0
                v.sample_end -= f_offset
                LOG.info("GT")
            f_new_length_seconds = ((v.sample_end - v.sample_start) *
                0.001) * f_graph.length_in_seconds
            if f_new_length_seconds < f_min_len:
                LOG.info("Popping item of length {}".format(f_new_length_seconds))
                f_to_delete.append(k)
            for f_tuple in locals().items():
                LOG.info(f_tuple)
        for k in f_to_delete:
            self.items.pop(k)

    def extend(self, a_new_ref, a_ref, a_item2, a_tempo):
        """ Glue 2 items together, adding f_offset to the
            event positions of a_item2
        """
        f_start_offset = a_ref.start_offset
        f_offset = (a_ref.start_beat - a_new_ref.start_beat -
            a_ref.start_offset)
        f_end_offset = a_ref.start_offset + a_ref.length_beats

        f_notes = [x.clone() for x in a_item2.notes
            if x.start >= f_start_offset and x.start < f_end_offset]

        for f_note in f_notes:
            f_note.start += f_offset
            self.add_note(f_note, False)
        self.notes.sort()

        f_ccs = [x.clone() for x in a_item2.ccs
            if x.start >= f_start_offset and x.start < f_end_offset]

        for f_cc in f_ccs:
            f_cc.start += f_offset
            self.add_cc(f_cc)
        self.ccs.sort()

        f_pbs = [x.clone() for x in a_item2.pitchbends
            if x.start >= f_start_offset and x.start < f_end_offset]

        for f_pb in f_pbs:
            f_pb.start += f_offset
            self.add_pb(f_pb)
        self.pitchbends.sort()

        a_item2.confine_audio_items(a_ref, a_tempo)
        for k, v in a_item2.items.items():
            f_index = self.get_next_index()
            if f_index == -1:
                LOG.info("Exceeded the max audio item count, dropping items")
                break
            v.start_beat += f_offset
            self.add_item(f_index, v)
            if k in a_item2.fx_list:
                self.set_row(f_index, a_item2.fx_list[k])

    #per-audio-item-fx

    def get_row_str(self, a_row_index):
        f_result = str(a_row_index)
        for f_item in self.fx_list[int(a_row_index)]:
            f_result += str(f_item)
        return f_result

    def set_row(self, a_row_index, a_fx_list):
        self.fx_list[int(a_row_index)] = a_fx_list

    def clear_row(self, a_row_index):
        self.fx_list.pop(a_row_index)

    def clear_row_if_exists(self, a_row_index):
        if a_row_index in self.fx_list:
            self.fx_list.pop(a_row_index)

    def get_row(self, a_row_index, a_return_none=False):
        if int(a_row_index) in self.fx_list:
            return self.fx_list[int(a_row_index)]
        else:
            # LOG.info("Index {} not found in "
            #     "DawAudioItem_fx_sequence".format(a_row_index))
            if a_return_none:
                return None
            else:
                f_result = []
                for f_i in range(8):
                    f_result.append(multifx_settings(64, 64, 64, 0))
                return f_result

    #end per-audio-item-fx

    def add_note(self, a_note, a_check=True):
        if a_check:
            for note in self.notes:
                if note.overlaps(a_note):
                    # TODO:  return -1 instead of True, and the
                    # offending editor_index when False
                    return False
        self.notes.append(a_note)
        self.notes.sort()
        if not a_check:
            self.fix_overlaps()
        return True

    def remove_note(self, a_note):
        try:
            self.notes.remove(a_note)
        except Exception as ex:
            LOG.exception(f"Exception in remove_note: {ex}")

    def velocity_mod(
        self,
        a_amt,
        a_start_beat=0.0,
        a_end_beat=4.0,
        a_line=False,
        a_end_amt=127,
        a_add=False,
        a_notes=None,
    ):
        """ velocity_mod
        (self, a_amt, #The amount to add or subtract
         a_start_beat=0.0, #modify values with a start at >= this, and...
         a_end_beat=4.0, # <= to this.
         a_line=False, # draw a line to a_end,
             otherwise all events are modified by a_amt
         a_end_amt=127, #not used unless a_line=True
         a_add=False, #True to add/subtract from each value, False to assign
         a_notes=None) #Process all notes if None, or
             selected if a list of notes is provided

         Modify the velocity of a range of notes
         """
        f_notes = []

        if a_notes is None:
            f_notes = self.notes
        else:
            for f_note in a_notes:
                for f_note2 in self.notes:
                    if f_note2 == f_note:
                        f_notes.append(f_note2)
                        break

        f_range_beats = a_end_beat - a_start_beat

        for note in f_notes:
            if note.start >= a_start_beat and note.start <= a_end_beat:
                if a_line:
                    f_frac = ((note.start - a_start_beat)/f_range_beats)
                    f_value = int(((a_end_amt - a_amt) * f_frac) + a_amt)
                else:
                    f_value = int(a_amt)
                if a_add:
                    note.velocity += f_value
                else:
                    note.velocity = f_value
                if note.velocity > 127:
                    note.velocity = 127
                elif note.velocity < 1:
                    note.velocity = 1

    def quantize(
        self,
        a_beat_frac,
        a_events_move_with_item=False,
        a_notes=None,
        a_selected_only=False,
    ):
        f_notes = []
        f_ccs = []
        f_pbs = []

        f_result = []

        if a_notes is None:
            f_notes = self.notes
            f_ccs = self.ccs
            f_pbs = self.pitchbends
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        if a_events_move_with_item:
                            f_start = f_note.start
                            f_end = f_note.start + f_note.length
                            for f_cc in self.ccs:
                                if f_cc.start >= f_start and \
                                f_cc.start <= f_end:
                                    f_ccs.append(f_cc)
                            for f_pb in self.pitchbends:
                                if f_pb.start >= f_start and \
                                f_pb.start <= f_end:
                                    f_pbs.append(f_pb)
                        f_notes.append(f_note)
                        break

        f_quantized_value = bar_frac_text_to_float(a_beat_frac)
        f_quantize_multiple = 1.0 / f_quantized_value

        for note in f_notes:
            if a_selected_only and not note.is_selected:
                continue
            f_new_start = round(note.start *
                f_quantize_multiple) * f_quantized_value
            note.start = f_new_start
            shift_adjust = note.start - f_new_start
            f_new_length = round(note.length *
                f_quantize_multiple) * f_quantized_value
            if f_new_length == 0.0:
                f_new_length = f_quantized_value
            note.set_length(f_new_length)
            f_result.append(str(note))

        self.fix_overlaps()

        if a_events_move_with_item:
            for cc in f_ccs:
                cc.start -= shift_adjust
            for pb in f_pbs:
                pb.start -= shift_adjust

        return f_result

    def transpose(
        self,
        a_semitones,
        a_octave=0,
        a_notes=None,
        a_selected_only=False,
        a_duplicate=False,
    ):
        f_total = a_semitones + (a_octave * 12)
        f_notes = []
        f_result = []

        if a_notes is None:
            f_notes = self.notes
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        f_notes.append(f_note)
                        break
        if a_duplicate:
            f_duplicates = []
        for note in f_notes:
            if a_selected_only and not note.is_selected:
                continue
            if a_duplicate:
                f_duplicates.append(note.from_str(str(note)))
            note.note_num += f_total
            note.note_num = clip_value(note.note_num, 0, 120)
            f_result.append(str(note))
        if a_duplicate:
            self.notes += f_duplicates
            self.notes.sort()
        return f_result

    def smooth_automation_points(self, a_is_cc, a_cc_num=-1):
        if a_is_cc:
            f_this_cc_arr = []
            f_result_arr = []
            f_cc_num = int(a_cc_num)
            for f_cc in self.ccs:
                if f_cc.cc_num == f_cc_num:
                    f_new_cc = cc(f_cc.start, f_cc_num, f_cc.cc_val)
                    f_this_cc_arr.append(f_new_cc)
            f_this_cc_arr.sort()
            for f_cc1, f_cc2 in zip(f_this_cc_arr, f_this_cc_arr[1:]):
                f_val_diff = abs(f_cc2.cc_val - f_cc1.cc_val)
                if f_val_diff == 0:
                    continue
                f_time_inc = .0625  #1/64th note
                f_start = f_cc1.start + f_time_inc

                f_start_diff = f_cc2.start - f_cc1.start
                if f_start_diff <= f_time_inc:
                    continue

                f_inc = (f_val_diff / (f_start_diff * 16.0))
                if (f_cc1.cc_val) > (f_cc2.cc_val):
                    f_inc *= -1.0
                f_new_val = clip_value(
                    f_cc1.cc_val + f_inc,
                    0.,
                    127.,
                )
                while True:
                    f_interpolated_cc = cc(f_start, f_cc_num, f_new_val)
                    f_new_val = clip_value(
                        f_new_val + f_inc,
                        0.,
                        127.,
                    )
                    f_result_arr.append(f_interpolated_cc)
                    f_start += f_time_inc
                    if f_start >= (f_cc2.start - 0.0625):
                        break

            self.ccs += f_result_arr
            self.ccs.sort()
        else:
            f_this_pb_arr = []
            f_result_arr = []

            for f_pb in self.pitchbends:
                f_new_pb = pitchbend(f_pb.start, f_pb.pb_val)
                f_this_pb_arr.append(f_new_pb)

            for f_pb1, f_pb2 in zip(f_this_pb_arr, f_this_pb_arr[1:]):
                f_val_diff = abs(
                    f_pb2.pb_val - f_pb1.pb_val)
                if f_val_diff == 0.0:
                    continue
                f_time_inc = 0.0625
                f_start = f_pb1.start + f_time_inc
                f_start_diff = f_pb2.start - f_pb1.start
                if f_start_diff <= f_time_inc:
                    continue
                f_val_inc = f_val_diff / (f_start_diff * 16.0)
                if f_pb1.pb_val > f_pb2.pb_val:
                    f_val_inc *= -1.0
                f_new_val = f_pb1.pb_val + f_val_inc

                while True:
                    f_interpolated_pb = pitchbend(f_start, f_new_val)
                    f_new_val += f_val_inc
                    f_result_arr.append(f_interpolated_pb)
                    f_start += f_time_inc
                    if f_start >= (f_pb2.start - 0.0625):
                        break
            self.pitchbends += f_result_arr
            self.pitchbends.sort()

    def fix_overlaps(self):
        """ Truncate the lengths of any notes that overlap
            the start of another note
        """
        f_to_delete = []
        for f_note in self.notes:
            if f_note not in f_to_delete:
                for f_note2 in self.notes:
                    if f_note != f_note2 and f_note2 not in f_to_delete:
                        if f_note.note_num == f_note2.note_num:
                            if f_note2.start == f_note.start:
                                if f_note2.length == f_note.length:
                                    f_to_delete.append(f_note2)
                                elif f_note2.length > f_note.length:
                                    f_note2.length = \
                                        f_note2.length - f_note.length
                                    f_note2.start = f_note.end
                                    f_note2.set_end()
                                else:
                                    f_note.length = \
                                        f_note.length - f_note2.length
                                    f_note.start = f_note2.end
                                    f_note.set_end()
                            elif f_note2.start > f_note.start:
                                if f_note.end > f_note2.start:
                                    f_note.length = \
                                        f_note2.start - f_note.start
                                    f_note.set_end()
        for f_note in self.notes:
            if f_note.length < _shared.min_note_length:
                f_to_delete.append(f_note)
        for f_note in f_to_delete:
            self.notes.remove(f_note)

    def get_next_default_note(self):
        pass

    def add_cc(self, a_cc):
        if a_cc in self.ccs:
            return False
        self.ccs.append(a_cc)
        self.ccs.sort()
        return True

    def remove_cc(self, a_cc):
        self.ccs.remove(a_cc)

    def remove_cc_range(self, a_cc_num, a_start_beat=0.0, a_end_beat=4.0):
        """ Delete all pitchbends greater than a_start_beat
            and less than a_end_beat
        """
        f_ccs_to_delete = []
        for cc in self.ccs:
            if cc.cc_num == a_cc_num and \
            cc.start >= a_start_beat and \
            cc.start <= a_end_beat:
                f_ccs_to_delete.append(cc)
        for cc in f_ccs_to_delete:
            self.remove_cc(cc)

    #TODO:  A maximum number of events per line?
    def draw_cc_line(
        self,
        a_cc,
        a_start,
        a_start_val,
        a_end,
        a_end_val,
        a_curve=0,
    ):
        f_cc = int(a_cc)
        f_start = float(a_start)
        f_start_val = int(a_start_val)
        f_end = float(a_end)
        f_end_val = int(a_end_val)
        #Remove any events that would overlap
        self.remove_cc_range(f_cc, f_start, f_end)

        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -1
        else:
            f_inc = 1
        f_time_inc = abs(f_start_diff / float(f_val_diff))
        for i in range(0, (f_val_diff + 1)):
            self.ccs.append(cc(f_start, f_cc, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        self.ccs.sort()

    def add_pb(self, a_pb):
        if a_pb in self.pitchbends:
            return False
        self.pitchbends.append(a_pb)
        self.pitchbends.sort()
        return True

    def remove_pb(self, a_pb):
        self.pitchbends.remove(a_pb)

    def remove_pb_range(self, a_start_beat=0.0, a_end_beat=4.0):
        """ Delete all pitchbends greater than
            a_start_beat and less than a_end_beat
        """
        f_pbs_to_delete = []
        for pb in self.pitchbends:
            if pb.start >= a_start_beat and \
            pb.start <= a_end_beat:
                f_pbs_to_delete.append(pb)
        for pb in f_pbs_to_delete:
            self.remove_pb(pb)

    def draw_pb_line(self, a_start, a_start_val, a_end, a_end_val, a_curve=0):
        f_start = float(a_start)
        f_start_val = float(a_start_val)
        f_end = float(a_end)
        f_end_val = float(a_end_val)
        #Remove any events that would overlap
        self.remove_pb_range(f_start, f_end)

        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -0.025
        else:
            f_inc = 0.025
        f_time_inc = abs(f_start_diff/(float(f_val_diff) * 40.0))
        for i in range(0, int((f_val_diff * 40) + 1)):
            self.pitchbends.append(pitchbend(f_start, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        #Ensure that the last value is what the user wanted it to be
        self.pitchbends[(len(self.pitchbends) - 1)].pb_val = f_end_val
        self.pitchbends.sort()

    def get_next_default_cc(self):
        pass

    @staticmethod
    def from_str(a_str, a_uid):
        f_result = item(a_uid)
        f_arr = a_str.split("\n")
        for f_event_str in f_arr:
            if f_event_str == terminating_char:
                break
            else:
                f_event_arr = f_event_str.split("|")
                if f_event_arr[0] == "n":
                    f_result.add_note(note.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "c":
                    f_result.add_cc(cc.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "p":
                    f_result.add_pb(pitchbend.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "a":
                    f_result.add_item(
                        int(f_event_arr[1]),
                        DawAudioItem.from_arr(f_event_arr[2:]),
                    )
                elif f_event_arr[0] == "f":
                    f_items_arr = []
                    f_item_index = f_event_arr[1]
                    f_vals_arr = f_event_arr[2:]
                    for f_i in range(8):
                        f_index = f_i * 4
                        f_index_end = f_index + 4
                        a_knob0, a_knob1, a_knob2, a_type = f_vals_arr[
                            f_index:f_index_end]
                        f_items_arr.append(
                            multifx_settings(
                                a_knob0, a_knob1, a_knob2, a_type))
                    f_result.set_row(f_item_index, f_items_arr)
                elif f_event_arr[0] == "U":
                    f_result.uid = int(f_event_arr[1])
                elif f_event_arr[0] == "M":
                    pass
                else:
                    LOG.error("Error: {}".format(f_event_arr))
                    assert False, "Invalid type '{}'".format(f_event_arr[0])
        return f_result

    def deduplicate(self):
        len_orig = len(self.notes)
        f_note_set = {str(x) for x in self.notes}
        note_diff = len_orig - len(f_note_set)
        if note_diff:
            LOG.info("Deduplicated {} notes".format(note_diff))
            self.notes = [note.from_str(x) for x in f_note_set]
            self.notes.sort()
        # TODO:  Others

    def __str__(self):
        self.deduplicate()
        f_result = []
        f_result.append("U|{}".format(self.uid))
        f_midi_count = len(self.notes) + len(self.ccs) + len(self.pitchbends)
        f_result.append("M|{}".format(f_midi_count))
        f_result += [str(x) for x in
            sorted(self.notes + self.ccs + self.pitchbends)]
        for k, f_item in list(self.items.items()):
            f_result.append("a|{}|{}".format(k, f_item))
        for k, v in self.fx_list.items():
            f_result.append("f|{}".format(self.get_row_str(k)))
        f_result.append(terminating_char)
        return "\n".join(f_result)

    def reorder(self, a_dict):
        for f_item in self.items.values():
            f_item.output_track = a_dict[f_item.output_track]
            if f_item.send1 != -1:
                f_item.send1 = a_dict[f_item.send1]
            if f_item.send2 != -1:
                f_item.send2 = a_dict[f_item.send2]

    def get_next_index(self):
        """ Return the next available index, or -1
            if none are available
        """
        for i in range(MAX_AUDIO_ITEM_COUNT):
            if not i in self.items:
                return i
        return -1

    def split(self, a_index):
        f_sequence0 = audio_sequence()
        f_sequence1 = audio_sequence()
        for k, v in list(self.items.items()):
            if v.start_bar >= a_index:
                v.start_bar -= a_index
                f_sequence1.items[k] = v
            else:
                f_sequence0.items[k] = v
        return f_sequence0, f_sequence1

    def add_item(self, a_index, a_item):
        self.items[int(a_index)] = a_item

    def remove_item(self, a_index):
        self.items.pop(int(a_index))

    def deduplicate_items(self):
        f_to_delete = []
        f_values = []
        for k, v in list(self.items.items()):
            f_str = str(v)
            if f_str in f_values:
                f_to_delete.append(k)
            else:
                f_values.append(f_str)
        for f_key in f_to_delete:
            LOG.info("Removing duplicate audio item at {}".format(f_key))
            self.items.pop(f_key)
            if f_key in self.fx_list:
                self.fx_list.pop(f_key)

