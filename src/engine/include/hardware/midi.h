#ifndef HARDWARE_MIDI_H
#define HARDWARE_MIDI_H

#ifndef NO_MIDI
    #include <portmidi.h>
#endif

#include "compiler.h"
#include "hardware/config.h"
#include "plugin.h"

#define SG_MAX_MIDI_DEVICE_COUNT 8

#define MIDI_EVENT_BUFFER_SIZE 1024
#define MIDI_CONTROLLER_COUNT 128

//low-level MIDI stuff
#define MIDI_NOTE_OFF       0x80
#define MIDI_NOTE_ON        0x90
#define MIDI_CC             0xB0
#define MIDI_PITCH_BEND     0xE0
#define MIDI_EOX            0xF7

typedef struct {
    int output_track;
    int channel;
    int on;
} t_midi_routing;


#ifdef NO_MIDI
    #define t_midi_device void
    #define t_midi_device_list void
#else
    typedef struct{
        int loaded;
        PmStream *f_midi_stream;
        PmError f_midi_err;
        PmDeviceID f_device_id;
        t_midi_routing* route;
        int instanceEventCounts;
        t_seq_event instanceEventBuffers[MIDI_EVENT_BUFFER_SIZE];
        PmEvent portMidiBuffer[MIDI_EVENT_BUFFER_SIZE];
        t_seq_event midiEventBuffer[MIDI_EVENT_BUFFER_SIZE];
        int midiEventReadIndex;
        int midiEventWriteIndex;
        char name[256];
    }t_midi_device;

    typedef struct{
        int count;
        t_midi_device devices[SG_MAX_MIDI_DEVICE_COUNT];
    }t_midi_device_list;
extern PmError f_midi_err;
#endif

void midiPoll(t_midi_device * self);

int midiDeviceInit(
    t_midi_device * self,
    char * f_midi_device_name
);
void midiDeviceClose(t_midi_device * self);
void midiReceive(
    t_midi_device * self,
    unsigned char status,
    unsigned char control,
    char value,
    int channel
);
void midiDeviceRead(
    t_midi_device* self,
    SGFLT sample_rate,
    unsigned long framesPerBuffer
);

void open_midi_devices(
    struct HardwareConfig* config
);
void close_midi_devices();

extern t_midi_device_list MIDI_DEVICES;
#endif
