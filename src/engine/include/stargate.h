#ifndef STARGATE_H
#define STARGATE_H

#include <pthread.h>

#include "audio/audio_pool.h"
#include "audio/input.h"
#include "audio/item.h"
#include "audiodsp/lib/midi.h"
#include "audiodsp/lib/peak_meter.h"
#include "audiodsp/modules/modulation/ramp_env.h"
#include "compiler.h"
#include "globals.h"
#include "hardware/midi.h"
#include "osc.h"
#include "plugin.h"

#define MAX_WORKER_THREADS 16

#define MAX_EVENT_BUFFER_SIZE 512

#define MIDI_CHANNEL_COUNT 17  // 16 + 1 for "All"
#define MIDI_NOTE_COUNT 128

#define MAX_PLUGIN_COUNT 10
#define MAX_ROUTING_COUNT 16
#define MAX_PLUGIN_TOTAL_COUNT (MAX_PLUGIN_COUNT + MAX_ROUTING_COUNT)

#define MAX_PLUGIN_POOL_COUNT 1000

#define MAX_AUDIO_INPUT_COUNT 128
#if SG_OS == _OS_LINUX
    #define FRAMES_PER_BUFFER 4096
#else
    // Lest no low-latency back-end is available
    #define FRAMES_PER_BUFFER 8192
#endif

enum TrackStatus {
    STATUS_NOT_PROCESSED = 0,
    STATUS_PROCESSING = 1,
    STATUS_PROCESSED = 2,
};

enum PlaybackMode {
    PLAYBACK_MODE_OFF = 0,
    PLAYBACK_MODE_PLAY = 1,
    PLAYBACK_MODE_REC = 2,
};

enum FadeState {
    FADE_STATE_OFF = 0,
    FADE_STATE_FADING = 1,
    FADE_STATE_FADED = 2,
    FADE_STATE_RETURNING = 3,
};

enum SequencerEventType {
    SEQ_EVENT_NONE = 0,
    SEQ_EVENT_LOOP = 1,
    SEQ_EVENT_TEMPO_CHANGE = 2,
    SEQ_EVENT_MARKER = 3,
};

#define SG_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL "pc"
#define SG_CONFIGURE_KEY_CONFIGURE_PLUGIN "co"
#define SG_CONFIGURE_KEY_EXIT "exit"
#define SG_CONFIGURE_KEY_PITCH_ENV "penv"
#define SG_CONFIGURE_KEY_RATE_ENV "renv"
#define SG_CONFIGURE_KEY_PREVIEW_SAMPLE "preview"
#define SG_CONFIGURE_KEY_STOP_PREVIEW "spr"
#define SG_CONFIGURE_KEY_KILL_ENGINE "abort"
#define SG_CONFIGURE_KEY_MAIN_VOL "mvol"
#define SG_CONFIGURE_KEY_LOAD_CC_MAP "cm"
#define SG_CONFIGURE_KEY_MIDI_LEARN "ml"
#define SG_CONFIGURE_KEY_ADD_TO_AUDIO_POOL "wp"
#define SG_CONFIGURE_KEY_AUDIO_POOL_ENTRY_VOL "apv"
#define SG_CONFIGURE_KEY_AUDIO_POOL_ITEM_RELOAD "wr"
#define SG_CONFIGURE_KEY_LOAD_AB_SET "abs"
#define SG_CONFIGURE_KEY_AUDIO_IN_VOL "aiv"
#define SG_CONFIGURE_KEY_ENGINE "engine"
#define SG_CONFIGURE_KEY_CLEAN_AUDIO_POOL "cwp"

enum StargateHosts {
    SG_HOST_DAW = 0,
    SG_HOST_WAVE_EDIT = 1,
};

#define SG_HOST_COUNT 2

// 1/128th note resolution, 0.03125f beats
#define SG_AUTOMATION_RESOLUTION (1.0f / 32.0f)
#define ATM_TICK_BUFFER_SIZE 16

enum TrackRouteTypes {
    ROUTE_TYPE_AUDIO = 0,
    ROUTE_TYPE_SIDECHAIN = 1,
    ROUTE_TYPE_MIDI = 2,
};


extern int SG_OFFLINE_RENDER;
extern SGFLT MAIN_VOL;
extern struct SamplePair* pluginOutputBuffers;
extern int ZERO;

/* An automation clock event */
typedef struct {
    /* (int)(song_pos_in_beats / SG_AUTOMATION_RESOLUTION) */
    int tick;
    /* the sample number in the current buffer that the event happens on */
    int sample;
    double beat;
} t_atm_tick;

typedef struct {
    int sample_count;
    long current_sample;
    double start_beat;
    double end_beat;
    SGFLT period_inc_beats;
    struct SamplePair* buffers;
    struct SamplePair* sc_buffers;
    SGFLT * input_buffer;
    int atm_tick_count;
    t_atm_tick atm_ticks[ATM_TICK_BUFFER_SIZE];
} t_sample_period;

typedef struct {
    int count;
    t_sample_period periods[3];
} t_sample_period_split;

typedef struct {
    enum SequencerEventType type;
    double beat;
    double start_beat;  //currently only for the loop event
    SGFLT tempo;
    struct {
        int num;
        int den;
    } tsig;
} t_sg_seq_event;

typedef struct {
    int is_looping;
    SGFLT tempo;
    SGFLT playback_inc;
    SGFLT samples_per_beat;
    t_sample_period period;
} t_sg_seq_event_period;

typedef struct {
    t_sample_period_split splitter;
    int count;
    t_sg_seq_event_period sample_periods[2];
} t_sg_seq_event_result;

typedef struct {
    int count;
    int pos;
    t_sg_seq_event * events;
    // Each tick of the automation clock happens in this many cycles
    double atm_clock_samples;
    double atm_pos;
    SGFLT tempo;
    SGFLT playback_inc;
    SGFLT samples_per_beat;
    t_sample_period period;
} t_sg_seq_event_list;


typedef struct {
    int thread_num;
    int stack_size;
} t_thread_args;

struct PluginPlan {
    struct SamplePair* input;
    struct SamplePair* output;

    int copy_count;
    int copies[MAX_PLUGIN_COUNT];  // array of f_track.audio[...] indices

    int zero_count;
    int zeroes[MAX_PLUGIN_COUNT];  // array of f_track.audio[...] indices

    int step_count;
    struct PluginPlanStep {
        t_plugin* plugin;
        struct SamplePair* input;
        struct SamplePair* output;
        enum PluginRunMode run_mode;
    } steps[MAX_PLUGIN_COUNT];
};

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    /*This is reset to bus_count each cycle and the
     * bus track processed when count reaches 0*/
    volatile int bus_counter;
    char bus_counter_padding[CACHE_LINE_SIZE];
    volatile enum TrackStatus status;
    char status_padding[CACHE_LINE_SIZE];
    t_sample_period_split splitter;
    int solo;
    int mute;
    int period_event_index;
    t_plugin * plugins[MAX_PLUGIN_TOTAL_COUNT];
    struct PluginPlan plugin_plan;
    int track_num;
    t_pkm_peak_meter * peak_meter;
    int sc_buffers_dirty;
    int channels;
    pthread_spinlock_t lock;
    t_ramp_env fade_env;
    int fade_state;
    /*When a note_on event is fired,
     * a sample number of when to release it is stored here*/
    long note_offs[MIDI_CHANNEL_COUNT][MIDI_NOTE_COUNT];
    int item_event_index;
    char osc_cursor_message[1024];
    int * extern_midi_count;
    t_midi_device * midi_device;
    t_seq_event * extern_midi;
    t_seq_event event_buffer[MAX_EVENT_BUFFER_SIZE];
    struct ShdsList * event_list;
    struct SamplePair sc_buffers[FRAMES_PER_BUFFER];
    struct SamplePair input_buffer[FRAMES_PER_BUFFER];
    struct SamplePair audio[MAX_PLUGIN_COUNT + 1][FRAMES_PER_BUFFER];
    char pad2[CACHE_LINE_SIZE];
} t_track;

typedef struct {
    void (*run)(
        int sample_count,
        struct SamplePair* output,
        SGFLT *a_input_buffers
    );
    void (*osc_send)(t_osc_send_data*);
    void (*audio_inputs)();
    void (*mix)();
} t_sg_host;

struct SgWorkerThread {
    char start_padding[CACHE_LINE_SIZE];
    //For broadcasting to the threads that it's time to process the tracks
    pthread_cond_t track_cond;
    //For preventing the main thread from continuing until the workers finish
    pthread_mutex_t track_block_mutex;
    pthread_spinlock_t lock;
    pthread_t thread;
    int track_thread_quit_notifier;
    char end_padding[CACHE_LINE_SIZE];
};

struct _t_stargate {
    t_sg_thread_storage thread_storage[MAX_WORKER_THREADS];
    t_sg_host * current_host;
    t_sg_host hosts[SG_HOST_COUNT];
    t_audio_pool * audio_pool;
    float* out;  // From Portaudio's callback
    int sample_count;
    pthread_spinlock_t main_lock;

    struct SgWorkerThread worker_threads[MAX_WORKER_THREADS];
    int worker_thread_count;

    t_sg_seq_event* current_tsig;
    int is_offline_rendering;
    //set from the audio device buffer size every time the main loop is called.
    t_audio_pool_item * preview_wav_item;
    t_audio_item * preview_audio_item;
    SGFLT preview_start; //0.0f to 1.0f
    int is_previewing;  //Set this to self->ab_mode on playback
    SGFLT preview_amp_lin;
    int preview_max_sample_count;
    t_audio_input * audio_inputs;
    pthread_mutex_t audio_inputs_mutex;
    pthread_t audio_recording_thread;
    int audio_recording_quit_notifier;
    enum PlaybackMode playback_mode;
    char osc_cursor_message[1024];
    int osc_queue_index;
    struct OscKeyPair osc_messages[OSC_SEND_QUEUE_SIZE];
    pthread_t osc_queue_thread;
    //Threads must hold this to write OSC messages
    pthread_spinlock_t ui_spinlock;
    t_midi_device_list * midi_devices;
    int midi_learn;
    t_plugin plugin_pool[MAX_PLUGIN_POOL_COUNT];
    SGPATHSTR project_folder[1024];
    SGPATHSTR audio_folder[1024];
    SGPATHSTR audio_tmp_folder[1024];
    SGPATHSTR samples_folder[1024];
    SGPATHSTR samplegraph_folder[1024];
    SGPATHSTR audio_pool_file[1024];
    SGPATHSTR plugins_folder[1024];
};

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    // index of the track to send to
    int output;
    // 1 if active, 0 if not active
    int active;
    int type;
    char pad2[CACHE_LINE_SIZE];
} t_track_routing;

void g_stargate_get(SGFLT, t_midi_device_list*);
t_track * g_track_get(int, SGFLT);
void v_zero_buffer(struct SamplePair*, int);
double v_print_benchmark(
    char * a_message,
    struct timespec a_start,
    struct timespec a_finish
);
void * v_audio_recording_thread(void* a_arg);
void v_queue_osc_message(char*, char*);
void v_set_plugin_index(t_track*, int, int, int, int, int, int);

t_track_routing * g_track_routing_get();
void v_set_host(int);

void v_sg_set_tempo(t_sg_seq_event_list*, SGFLT, t_sg_seq_event*);
void v_ui_send(char * a_path, char * a_msg);
void v_default_mix();

void v_sg_set_playback_pos(
    t_sg_seq_event_list * self,
    double a_beat,
    long a_current_sample
);
void g_pitchbend_init(
    t_seq_event * f_result,
    SGFLT a_start,
    SGFLT a_value,
    int channel
);
void g_cc_init(
    t_seq_event * f_result,
    int a_cc_num,
    SGFLT a_cc_val,
    SGFLT a_start,
    int channel
);
void g_note_init(
    t_seq_event* f_result,
    int a_note,
    int a_vel,
    SGFLT a_start,
    SGFLT a_length,
    SGFLT pan,
    SGFLT attack,
    SGFLT decay,
    SGFLT sustain,
    SGFLT release,
    int channel,
    SGFLT pitch_fine
);
void v_set_control_from_atm(
    t_seq_event *event,
    int a_plugin_uid,
    t_track * f_track
);
void v_open_track(
    t_track* a_track,
    SGPATHSTR* a_tracks_folder,
    int a_index
);
void v_buffer_mix(
    int a_count,
    struct SamplePair* a_buffer_src,
    struct SamplePair* a_buffer_dest
);
void g_sg_seq_event_list_init(t_sg_seq_event_list * self);
void v_sample_period_split(
    t_sample_period_split* self,
    struct SamplePair* a_buffers,
    struct SamplePair* a_sc_buffers,
    int a_sample_count,
    double a_period_start_beat,
    double a_period_end_beat,
    double a_event1_beat,
    double a_event2_beat,
    long a_current_sample,
    SGFLT * a_input_buffer,
    int a_input_count
);
NO_OPTIMIZATION void v_wait_for_threads();
void v_sample_period_set_atm_events(
    t_sample_period * self,
    t_sg_seq_event_list * a_event_list,
    long a_current_sample,
    int a_sample_count
);
void v_sg_seq_event_result_set_default(
    t_sg_seq_event_result * self,
    t_sg_seq_event_list * a_list,
    struct SamplePair* a_buffers,
    SGFLT * a_input_buffers,
    int a_input_count,
    int a_sample_count,
    long a_current_sample
);
void v_sg_seq_event_list_set(
    t_sg_seq_event_list * self,
    t_sg_seq_event_result* a_result,
    struct SamplePair* a_buffers,
    SGFLT* a_input_buffers,
    int a_input_count,
    int a_sample_count,
    long a_current_sample,
    int a_loop_mode
);
void g_seq_event_result_init(t_sg_seq_event_result * self);
int i_beat_count_to_samples(
    double a_beat_count,
    SGFLT a_tempo,
    SGFLT a_sr
);
double f_samples_to_beat_count(
    int a_sample_count,
    double a_tempo,
    SGFLT sr_recip
);
double f_samples_to_beat_count_sr(
    int a_sample_count,
    double a_tempo,
    SGFLT sr
);
double f_bpm_to_seconds_per_beat(double a_tempo);
void v_set_control_from_cc(
    t_seq_event* event,
    t_track* f_track
);
void v_sg_configure(const char* a_key, const char* a_value);
void v_run_main_loop(
    int sample_count,
    struct SamplePair* a_buffers,
    PluginData* a_input_buffers
);
void v_run(
    struct SamplePair* buffers,
    SGFLT* a_input,
    int sample_count
);
void stop_preview();
void track_free(t_track* track);

#endif
