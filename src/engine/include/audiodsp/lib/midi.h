#ifndef STARGATE_LIB_MIDI_H
#define STARGATE_LIB_MIDI_H

#define MIDI_ALL_CHANNELS 16

struct MIDINoteOff {
    long sample;
    int channel;
};

// Check that a MIDI event is in the same channel as the plugin
int midi_event_is_in_channel(int note_channel, int instrument_channel);

#endif
