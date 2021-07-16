from sglib.log import LOG
from sglib.models.stargate import *
from sglib.lib.util import *
from sglib.lib.midi import load_midi_file
from sglib.lib.translate import _

from sglib.models.daw import _shared

class DawMidiFile:
    """ Convert the MIDI file at a_file to a dict of channel#:item
        @a_file:  The path to the MIDI file
        @a_project:  An instance of DawProject
    """
    def __init__(
        self,
        a_file,
        a_project,
    ):
        f_item_list = load_midi_file(a_file)
        self.result_dict = {}

        for f_event in f_item_list:
            if f_event.length >= _shared.min_note_length:
                f_velocity = f_event.ev.velocity
                f_beat = f_event.start_beat
                print("f_beat : {}".format(f_beat))
                f_pitch = f_event.ev.note
                f_length = f_event.length
                f_channel = f_event.ev.channel
                f_key = int(f_channel)
                if not f_key in self.result_dict:
                    f_uid = a_project.create_empty_item()
                    self.result_dict[f_key] = a_project.get_item_by_uid(f_uid)
                f_note = note(f_beat, f_length, f_pitch, f_velocity)
                self.result_dict[f_key].add_note(f_note) #, a_check=False)
            else:
                LOG.warning(
                    "Ignoring note event with <= {} length".format(
                        _shared.min_note_length,
                    )
                )
        for f_item in self.result_dict.values():
            a_project.save_item_by_uid(f_item.uid, f_item)
        self.channel_count = self.get_channel_count()

    def get_channel_count(self):
        return max(self.result_dict) if self.result_dict else 0


