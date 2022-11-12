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
        self.item_list = load_midi_file(a_file)
        self.project = a_project
        self.result_dict = {}

    def single_item(self):
        uid = self.project.create_empty_item()
        item = self.project.get_item_by_uid(uid)
        for f_event in self.item_list:
            if f_event.length >= _shared.min_note_length:
                velocity = f_event.ev.velocity
                beat = f_event.start_beat
                LOG.info(f"beat : {beat}")
                pitch = f_event.ev.note
                length = f_event.length
                channel = f_event.ev.channel
                midi_note = note(
                    beat,
                    length,
                    pitch,
                    velocity,
                    channel=channel,
                )
                item.add_note(midi_note) #, a_check=False)
            else:
                LOG.warning(
                    "Ignoring note event with <= {} length".format(
                        _shared.min_note_length,
                    )
                )
        self.project.save_item_by_uid(uid, item)
        self.result_dict[0] = item

    def multi_item(self):
        for f_event in self.item_list:
            if f_event.length >= _shared.min_note_length:
                velocity = f_event.ev.velocity
                beat = f_event.start_beat
                LOG.info(f"beat : {beat}")
                pitch = f_event.ev.note
                length = f_event.length
                channel = f_event.ev.channel
                key = int(channel)
                if not f_key in self.result_dict:
                    uid = self.project.create_empty_item()
                    self.result_dict[key] = self.project.get_item_by_uid(uid)
                f_note = note(beat, length, pitch, velocity)
                self.result_dict[key].add_note(f_note) #, a_check=False)
            else:
                LOG.warning(
                    "Ignoring note event with <= {} length".format(
                        _shared.min_note_length,
                    )
                )
        for f_item in self.result_dict.values():
            self.project.save_item_by_uid(f_item.uid, f_item)


