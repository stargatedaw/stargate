#include "audiodsp/lib/midi.h"

int midi_event_is_in_channel(int note_channel, int instrument_channel){
    if(
        note_channel == instrument_channel
        ||
        note_channel == 16  // all channels
        ||
        instrument_channel == 16  // all channels
    ){
        return 1;
    }
    return 0;
}
