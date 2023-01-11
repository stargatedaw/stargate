from sglib.log import LOG
from sglib.models.stargate import *
from sglib.lib.util import *
from sglib.lib.midi import load_midi_file
from sglib.models.daw import _shared

from typing import List

try:
    import mido
except ImportError:
    from sg_py_vendor import mido

import math


class MIDIFileAnalysis:
    """ Provide insight into the characteristics of a MIDI file
        Mostly around how many channels/topology, and the types of
        events it contains
    """
    def __init__(
        self,
        events,
        has_notes: bool,
        has_ccs: bool,
        has_pbs: bool,
        channels: List,
        length: int,
    ):
        self.events = events
        self.has_notes = has_notes
        self.has_ccs = has_ccs
        self.has_pbs = has_pbs
        self.channels = channels
        self.length = length

    def channels_for_types(self, notes: bool, ccs: bool, pbs: bool):
        return sorted({
            x.channel for x in self.events
            if (
                (x.type == 'note_on' and notes)
                or
                (x.type == 'control_change' and ccs)
                or
                (x.type == 'pitchwheel' and pbs)
            )
        })

    def channels_are_compressed(self) -> bool:
        """ Check if there are multiple channels and they are
            sequential starting from zero.
            ie:
                0,1,2,3 == True
                0 == True
                6 == True
                0,4 == False
                2,4,6 == False
        """
        if len(self.channels) <= 1:
            return True
        if self.channels[0] != 0:
            return False
        for channel, _next in zip(self.channels, self.channels[1:]):
            if _next - channel != 1:
                return False
        return True

    @staticmethod
    def factory(path: str):
        def pos_to_beat():
            return round(start_offset + (pos / sec_per_beat), 4)
        midi_file = mido.MidiFile(path)
        has_notes = False
        has_ccs = False
        has_pbs = False
        channels = set()
        length = 0
        sec_per_beat = 0.5
        start_offset = 0.0  # in beats
        pos = 0.0
        events = []
        for event in (x for x in midi_file if not x.is_meta):
            LOG.debug(f'Event type: {event.type} is_meta: {event.is_meta}')
            pos += event.time
            channels.add(event.channel)
            if event.type == "set_tempo":
                start_offset = pos_to_beat()
                sec_per_beat = event.tempo / 1000000.0
                pos = 0.0
                LOG.info('Tempo change: {sec_per_beat} {start_offset}')
            elif event.type == "note_on":
                events.append(event)
                has_notes = True
            elif event.type == 'control_change':
                events.append(event)
                has_ccs = True
            elif event.type == 'pitchwheel':
                events.append(event)
                has_pbs = True
        length = math.ceil(pos_to_beat())

        return MIDIFileAnalysis(
            events,
            has_notes,
            has_ccs,
            has_pbs,
            sorted(channels),
            int(length),
        )


class DawMidiFile:
    """ Convert the MIDI file at a_file to a dict of channel#:item
        @a_file:  The path to the MIDI file
        @a_project:  An instance of DawProject
    """
    def __init__(
        self,
        a_file,
        a_project,
        name,
        channel,
        notes,
        ccs,
        pbs,
    ):
        self.item_list = load_midi_file(a_file)
        self.project = a_project
        self.result_dict = {}
        self.name = name
        self.channel = channel
        self.notes = notes
        self.ccs = ccs
        self.pbs = pbs

    def get_used_channels(self):
        return {
            x.ev.channel for x in self.item_list
            if (
                (x.ev.type in ('note_on', 'note_off') and self.notes)
                or
                (x.ev.type == 'control_change' and self.ccs)
                or
                (x.ev.type == 'pitchwheel' and self.pbs)
            )
        }

    def single_item(self):
        uid = self.project.create_empty_item(self.name)
        item = self.project.get_item_by_uid(uid)
        _channel = None
        channels = self.get_used_channels()
        if len(channels) == 1:
            _channel = self.channel
        for f_event in self.item_list:
            if (
                self.notes
                and
                f_event.type == 'note_on'
                and
                f_event.length >= _shared.min_note_length
            ):
                velocity = f_event.ev.velocity
                beat = f_event.start_beat
                pitch = f_event.ev.note
                length = f_event.length
                channel = f_event.ev.channel if _channel is None else _channel
                midi_note = MIDINote(
                    beat,
                    length,
                    pitch,
                    velocity,
                    channel=channel,
                )
                item.add_note(midi_note) #, a_check=False)
            elif (
                self.ccs
                and
                f_event.type == 'control_change'
            ):
                beat = f_event.start_beat
                cc_num = f_event.ev.control
                value = f_event.ev.value
                channel = f_event.ev.channel if _channel is None else _channel
                cc = MIDIControl(beat, cc_num, value, channel)
                item.add_cc(cc)
            elif (
                self.pbs
                and
                f_event.type == 'pitchwheel'
            ):
                beat = f_event.start_beat
                pitch = f_event.ev.pitch
                value = round(
                    pitch / 8192. if pitch < 0. else pitch / 8191,
                    5,
                )
                channel = f_event.ev.channel if _channel is None else _channel
                pb = MIDIPitchbend(beat, value, channel)
                item.add_pb(pb)
            else:
                LOG.warning(f"Ignoring event {f_event.ev}")
        self.project.save_item_by_uid(uid, item)
        self.result_dict[0] = item

    def multi_item(self):
        _channel = None
        channels = self.get_used_channels()
        if len(channels) == 1:
            _channel = self.channel
        for f_event in self.item_list:
            channel = f_event.ev.channel
            key = int(channel)
            if not key in self.result_dict:
                uid = self.project.create_empty_item(self.name)
                self.result_dict[key] = self.project.get_item_by_uid(uid)
            if (
                self.notes
                and
                f_event.type == 'note_on'
                and
                f_event.length >= _shared.min_note_length
            ):
                velocity = f_event.ev.velocity
                beat = f_event.start_beat
                pitch = f_event.ev.note
                length = f_event.length
                f_note = MIDINote(
                    beat,
                    length,
                    pitch,
                    velocity,
                    channel=channel if self.channel is None else self.channel,
                )
                self.result_dict[key].add_note(f_note) #, a_check=False)
            elif (
                self.ccs
                and
                f_event.type == 'control_change'
            ):
                beat = f_event.start_beat
                cc_num = f_event.ev.control
                value = f_event.ev.value
                channel = f_event.ev.channel if _channel is None else _channel
                cc = MIDIControl(beat, cc_num, value, channel)
                self.result_dict[key].add_cc(cc)
            elif (
                self.pbs
                and
                f_event.type == 'pitchwheel'
            ):
                beat = f_event.start_beat
                pitch = f_event.ev.pitch
                value = round(
                    pitch / 8192. if pitch < 0. else pitch / 8191,
                    5,
                )
                channel = f_event.ev.channel if _channel is None else _channel
                pb = MIDIPitchbend(beat, value, channel)
                self.result_dict[key].add_pb(pb)
            else:
                LOG.warning(f"Ignoring event {f_event.ev}")
        for f_item in self.result_dict.values():
            self.project.save_item_by_uid(f_item.uid, f_item)

