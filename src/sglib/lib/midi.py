from sglib.log import LOG
try:
    import mido
except ImportError:
    from sg_py_vendor import mido


class MidiEvent:
    def __init__(self, a_ev, a_start_beat):
        self.ev = a_ev
        self.start_beat = a_start_beat
        self.type = a_ev.type

    def __lt__(self, other):
        return self.start_beat < other.start_beat

def load_midi_file(path: str):
    def pos_to_beat():
        return round(start_offset + (pos / sec_per_beat), 4)
    midi_file = mido.MidiFile(path)
    f_note_on_dict = {}
    f_item_list = []
    sec_per_beat = 0.5
    start_offset = 0.0  # in beats
    pos = 0.0
    for event in midi_file:
        LOG.debug(f'Event type: {event.type} is_meta: {event.is_meta}')
        pos += event.time
        if event.type == "set_tempo":
            start_offset = pos_to_beat()
            sec_per_beat = event.tempo / 1000000.0
            pos = 0.0
            LOG.info('Tempo change: {sec_per_beat} {start_offset}')
        elif event.type == "note_off" or (
            event.type == "note_on"
            and
            event.velocity == 0
        ):
            f_tuple = (event.channel, event.note)
            if f_tuple in f_note_on_dict:
                f_event = f_note_on_dict[f_tuple]
                LOG.debug(f'note-off {event.note} time: {event.time}')
                f_event.length = pos_to_beat() - f_event.start_beat
                f_item_list.append(f_event)
                f_note_on_dict.pop(f_tuple)
            else:
                LOG.warning(
                    "Error, note-off event does not correspond to a "
                    "note-on event, ignoring event:\n{}".format(event)
                )
        elif event.type == "note_on":
            LOG.debug(f'note-on {event.note} time: {event.time}')
            start_beat = pos_to_beat()
            f_event = MidiEvent(event, start_beat)
            f_tuple = (event.channel, event.note)
            if f_tuple in f_note_on_dict:
                LOG.warning(
                    'Truncating note-on that did not receive a note-off, '
                    'because another note-on event on the same note started'
                )
                f_note_on_dict[f_tuple].length = \
                    start_beat - f_event.start_beat
                f_item_list.append(f_note_on_dict[f_tuple])
            f_note_on_dict[f_tuple] = f_event
        elif event.type in ('control_change', 'pitchwheel'):
            start_beat = pos_to_beat()
            f_event = MidiEvent(event, start_beat)
            f_item_list.append(f_event)
        else:
            LOG.debug("Ignoring event: {}".format(event))

    f_item_list.sort()
    return f_item_list

