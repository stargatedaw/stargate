from sglib.log import LOG
import mido

class MidiEvent:
    def __init__(self, a_ev, a_start_beat):
        self.ev = a_ev
        self.start_beat = a_start_beat
        self.type = a_ev.type

    def __lt__(self, other):
        return self.start_beat < other.start_beat

def load_midi_file(a_file):
    f_midi_text_arr = mido.MidiFile(str(a_file))
    #First fix the lengths of events that have note-off events
    f_note_on_dict = {}
    f_item_list = []
    f_pos = 0
    f_sec_per_beat = 0.5
    for f_ev in f_midi_text_arr:
        if f_ev.type == "set_tempo":
            f_sec_per_beat = f_ev.tempo / 1000000.0
        elif f_ev.type == "note_off" or (
        f_ev.type == "note_on" and f_ev.velocity == 0):
            f_tuple = (f_ev.channel, f_ev.note)
            if f_tuple in f_note_on_dict:
                f_event = f_note_on_dict[f_tuple]
                f_event.length = f_pos - f_event.start_beat
                f_item_list.append(f_event)
                f_note_on_dict.pop(f_tuple)
            else:
                LOG.warning(
                    "Error, note-off event does not correspond to a "
                    "note-on event, ignoring event:\n{}".format(f_ev)
                )
        elif f_ev.type == "note_on":
            f_event = MidiEvent(f_ev, f_pos)
            f_tuple = (f_ev.channel, f_ev.note)
            if f_tuple in f_note_on_dict:
                f_note_on_dict[f_tuple].length = f_pos - f_event.start_beat
            f_note_on_dict[f_tuple] = f_event
        else:
            LOG.warning("Ignoring event: {}".format(f_ev))
        f_pos += f_ev.time / f_sec_per_beat

    f_item_list.sort()
    return f_item_list

