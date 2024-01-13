#ifndef SG_PLUGIN_H
#define SG_PLUGIN_H

#include "audio/paifx.h"
#include "audiodsp/lib/midi.h"
#include "audiodsp/lib/peak_meter.h"
#include "compiler.h"
#include "ds/list.h"

enum PluginEvent {
    EVENT_NOTEON = 0,
    EVENT_NOTEOFF = 1,
    EVENT_PITCHBEND = 2,
    EVENT_CONTROLLER = 3,
    EVENT_AUTOMATION = 4,
};

typedef void (*fp_queue_message)(char*, char*);

typedef int PluginPortDescriptor;

enum PluginRunMode {RunModeReplacing, RunModeMixing};

typedef struct _PluginPortRangeHint {
  PluginData DefaultValue;
  PluginData LowerBound;
  PluginData UpperBound;
} PluginPortRangeHint;

typedef void * PluginHandle;

struct MIDIEvent {
    enum PluginEvent type;
    int tick;
    int port;
    SGFLT value;
};

struct MIDIEvents {
    int count;
    struct MIDIEvent events[200];
};

// MIDI event
typedef struct {
    enum PluginEvent type;
    int tick;
    unsigned int tv_sec;
    unsigned int tv_nsec;
    int channel;
    int note;
    SGFLT pan;
    SGFLT attack;
    SGFLT decay;
    SGFLT sustain;
    SGFLT release;
    SGFLT pitch_fine;
    int velocity;
    int duration;

    int param;
    SGFLT value;
    SGFLT start;
    SGFLT length;
    int port;
} t_seq_event;

typedef struct {
    int uid;
    SGFLT* samples[2];
    SGFLT ratio_orig;
    SGFLT volume;  // Linear volume, not dB
    int channels;
    int length;
    SGFLT sample_rate;
    // audio files are loaded dynamically when they are first seen
    // in the project
    int is_loaded;
    // host sample-rate, cached here for easy access
    SGFLT host_sr;
    t_file_fx_controls fx_controls;
    SGPATHSTR path[2048];
} t_audio_pool_item;

typedef t_audio_pool_item * (*fp_get_audio_pool_item_from_host)(int);

/* For sorting a list by start time */
int seq_event_cmpfunc(void *self, void *other);

/* Descriptor for a Type of Plugin:

   This structure is used to describe a plugin type. It provides a
   number of functions to examine the type, instantiate it, link it to
   buffers and workspaces and to run it. */

typedef struct _PluginDescriptor {
    char pad1[CACHE_LINE_SIZE];
    int PortCount;

    PluginPortDescriptor * PortDescriptors;

    // This member indicates an array of range hints for each port (see
    // above). Valid indices vary from 0 to PortCount-1.
    PluginPortRangeHint * PortRangeHints;

    PluginHandle (*instantiate)(
        struct _PluginDescriptor * Descriptor,
        int SampleRate,
        fp_get_audio_pool_item_from_host a_host_audio_pool_func,
        int a_plugin_uid,
        fp_queue_message
    );

    void (*connect_port)(
        PluginHandle Instance,
        int Port,
        PluginData * DataLocation
    );

    void (*cleanup)(PluginHandle Instance);

    // Load the plugin state file at a_file_path
    void (*load)(
        PluginHandle Instance,
        struct _PluginDescriptor * Descriptor,
        SGPATHSTR* a_file_path
    );
    SGFLT* (*get_port_table)(PluginHandle instance);

    void (*set_port_value)(PluginHandle Instance, int a_port, SGFLT a_value);

    void (*set_cc_map)(PluginHandle Instance, char * a_msg);

    /* When a panic message is sent, do whatever it takes to fix any stuck
     notes. */
    void (*panic)(PluginHandle Instance);

    //For now all plugins must set it to 1.

    int API_Version;

    void (*configure)(
        PluginHandle Instance,
        char *Key,
        char *Value,
        pthread_spinlock_t * a_spinlock
    );

    void (*run)(
        PluginHandle Instance,
        enum PluginRunMode run_mode,
        int SampleCount,
        struct SamplePair* input_buffer,
        struct SamplePair* sc_buffer,
        struct SamplePair* output_buffer,
        struct ShdsList* midi_events,
        struct ShdsList* atm_events,
        t_pkm_peak_meter* peak_meter,
        int midi_channel
    );

    /* Do anything like warming up oscillators, etc...  in preparation
     * for offline rendering.  This must be called after loading
     * the project.
     */
    void (*offline_render_prep)(PluginHandle Instance, SGFLT sample_rate);

    /* Force any notes to off, etc...  and anything else you may want to
     * do when the transport stops
     */
    void (*on_stop)(PluginHandle Instance);

    char pad2[CACHE_LINE_SIZE];
} PluginDescriptor;

typedef PluginDescriptor* (*PluginDescriptor_Function)();

typedef struct {
    enum PluginEvent type;
    int tick;
    SGFLT value;
    int port;
} t_plugin_event_queue_item;

typedef struct {
    int count;
    int pos;
    t_plugin_event_queue_item items[200];
} t_plugin_event_queue;

typedef struct {
    int count;
    int ports[5];
    SGFLT lows[5];
    SGFLT highs[5];
} t_cc_mapping;

typedef struct {
    t_cc_mapping map[128];
} t_plugin_cc_map;

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    int active;
    int power;
    PluginDescriptor *descriptor;
    PluginHandle plugin_handle;
    int uid;
    int pool_uid;
    int atm_count;
    t_seq_event * atm_buffer;
    struct ShdsList * atm_list;
    PluginDescriptor_Function descfn;
    int mute;
    int solo;
    int route;
    int midi_channel;
    char pad2[CACHE_LINE_SIZE];
} t_plugin;

//PluginDescriptor_Function PLUGIN_DESC_FUNCS[];

void v_plugin_event_queue_add(t_plugin_event_queue*, int, int, SGFLT, int);
void v_plugin_event_queue_reset(t_plugin_event_queue*);
t_plugin_event_queue_item * v_plugin_event_queue_iter(
    t_plugin_event_queue*, int);
void v_plugin_event_queue_atm_set(t_plugin_event_queue*, int, SGFLT*);
SGFLT f_cc_to_ctrl_val(PluginDescriptor*, int, SGFLT);
void v_cc_mapping_init(t_cc_mapping*);
void v_cc_map_init(t_plugin_cc_map*);
void v_cc_map_translate(
    t_plugin_cc_map*,
    PluginDescriptor*,
    SGFLT*,
    int,
    SGFLT
);
void v_generic_cc_map_set(t_plugin_cc_map*, char*);
void v_ev_clear(t_seq_event * a_event);
void v_ev_set_atm(
    t_seq_event* a_event,
    int a_port_num,
    int a_value
);
void g_get_port_table(
    PluginHandle * handle,
    PluginDescriptor * descriptor
);
void generic_file_loader(
    PluginHandle Instance,
    PluginDescriptor * Descriptor,
    SGPATHSTR* a_path,
    SGFLT * a_table,
    t_plugin_cc_map * a_cc_map
);
void set_plugin_port(
    PluginDescriptor * a_desc,
    int a_port,
    SGFLT a_default,
    SGFLT a_min,
    SGFLT a_max
);
PluginDescriptor * get_plugin_descriptor(int a_port_count);
SGFLT f_atm_to_ctrl_val(
    PluginDescriptor *self,
    int a_port,
    SGFLT a_val
);
void v_ev_set_pitchbend(
    t_seq_event* a_event,
    int a_channel,
    int a_value
);
void v_ev_set_controller(
    t_seq_event* a_event,
    int a_channel,
    int a_cc_num,
    int a_value
);
void v_ev_set_noteon(
    t_seq_event* a_event,
    int a_channel,
    int a_note,
    int a_velocity,
    SGFLT pan,
    SGFLT attack,
    SGFLT decay,
    SGFLT sustain,
    SGFLT release,
    SGFLT pitch_fine
);
void v_ev_set_noteoff(
    t_seq_event* a_event,
    int a_channel,
    int a_note,
    int a_velocity
);

NO_OPTIMIZATION void plugin_activate(
    t_plugin * f_result,
    int a_sample_rate,
    int a_index,
    fp_get_audio_pool_item_from_host a_host_audio_pool_func,
    int a_plugin_uid,
    fp_queue_message a_queue_func
);

SGFLT set_pmn_adsr(SGFLT, SGFLT, SGFLT, SGFLT);

// Called once per sample period.  Does not process MIDI notes, only suitable
// for effects
void effect_translate_midi_events(
    struct ShdsList* source_events,
    struct MIDIEvents* dest_events,
    t_plugin_event_queue* atm_queue,
    struct ShdsList* atm_events,
    int midi_channel
);

// Called once per sample, does not process MIDI notes
void effect_process_events(
    int sample_num,
    struct MIDIEvents* midi_events,
    SGFLT* port_table,
    PluginDescriptor * descriptor,
    t_plugin_cc_map* cc_map,
    t_plugin_event_queue* atm_queue
);

void _plugin_mix(
    enum PluginRunMode run_mode,
    int pos,
    struct SamplePair* output_buffer,
    SGFLT left,
    SGFLT right
);

#endif
