#ifndef DAW_H
#define DAW_H

#include "stargate.h"
#include "audio/item.h"
#include "compiler.h"
#include "daw/limits.h"
#include "osc.h"


#define DN_LOOP_MODE_OFF 0
#define DN_LOOP_MODE_SEQUENCE 1
#define DAW_MAX_SONG_COUNT 20

typedef struct
{
    t_midi_routing routes[DN_TRACK_COUNT];
}t_daw_midi_routing_list;

typedef struct
{
    t_seq_event * events;
    int event_count;
    t_audio_items * audio_items;
    int uid;
}t_daw_item;

typedef struct
{
    int item_uid;
    double start;
    double start_offset;
    double length;
    double end;
}t_daw_item_ref;

typedef struct
{
    int pos;
    int count;
    t_daw_item_ref * refs;
}t_daw_track_seq;

typedef struct
{
    t_daw_track_seq tracks[DN_TRACK_COUNT];
    t_sg_seq_event_list events;
}t_daw_sequence;

typedef struct
{
    double beat;      // the beat position within the song 0-N
    double recip;     // 1.0 / self->beat - next->beat
    int tick;         // self->beat / SG_AUTOMATION_RESOLUTION
    int port;         // the port number for this control in this plugin 0-N
    SGFLT val;        // control value, 0-127
    int index;        // the plugin type, not used by the engine
    int plugin;       // plugin uid 0-N
    int break_after;  // Don't smooth to the next point
}t_daw_atm_point;

typedef struct
{
    int atm_pos;  //position within the automation sequence
    t_daw_atm_point * points;
    int point_count;
    int port;
    SGFLT last_val;
}t_daw_atm_port;

typedef struct
{
    t_daw_atm_port * ports;
    int port_count;
    char padding[CACHE_LINE_SIZE - sizeof(int) - sizeof(void*)];
}t_daw_atm_plugin;

typedef struct
{
    t_daw_atm_plugin plugins[MAX_PLUGIN_POOL_COUNT];
}t_daw_atm_sequence;

typedef struct
{
    t_daw_sequence * sequences;
    t_daw_atm_sequence * sequences_atm;
}t_daw_song;

typedef struct
{
    int track_pool_sorted[MAX_WORKER_THREADS][DN_TRACK_COUNT]
        ;
    t_pytrack_routing routes[DN_TRACK_COUNT][MAX_ROUTING_COUNT]
        ;
    int bus_count[DN_TRACK_COUNT];
    int track_pool_sorted_count;
}t_daw_routing_graph;

typedef struct
{
    double ml_sample_period_inc_beats;
    double ml_current_beat;
    double ml_next_beat;
    long current_sample;
    long f_next_current_sample;
    int is_looping;
    int is_first_period;   //since playback started
    int playback_mode;
    int suppress_new_audio_items;
    int sample_count;
    SGFLT tempo;
    SGFLT playback_inc;
    //The number of samples per beat, for calculating length
    SGFLT samples_per_beat;
    SGFLT * input_buffer;
    int input_count;
    int * input_index;
    int atm_tick_count;
    // This also pads the cache line, since most of these
    // bytes will never be used
    t_atm_tick atm_ticks[ATM_TICK_BUFFER_SIZE];
}t_daw_thread_storage;

typedef struct
{
    t_daw_thread_storage ts[MAX_WORKER_THREADS];
    t_sg_seq_event_result seq_event_result;
    t_daw_song* en_song;
    t_daw_sequence* seq_pool[DAW_MAX_SONG_COUNT];
    t_pytrack* track_pool[DN_TRACK_COUNT];
    t_daw_routing_graph * routing_graph;

    int loop_mode;  //0 == Off, 1 == On
    int overdub_mode;  //0 == Off, 1 == On

    t_daw_item* item_pool[DN_MAX_ITEM_COUNT];

    int is_soloed;

    int audio_glue_indexes[MAX_AUDIO_ITEM_COUNT];

    t_daw_midi_routing_list midi_routing;

    char* project_folder;
    char* item_folder;
    char* sequence_folder;
    char* tracks_folder;
    char* seq_event_file;
}t_daw;


void g_daw_song_get(t_daw*, int);
t_daw_routing_graph * g_daw_routing_graph_get(t_daw*);
void v_daw_routing_graph_free(t_daw_routing_graph*);
/* Return the specified t_daw_sequence
 * @daw: The main DAW object
 * @uid: The uid of the t_daw_sequence to fetch
 */
t_daw_sequence * g_daw_sequence_get(t_daw* daw, int uid);
t_daw_atm_sequence * g_daw_atm_sequence_get(t_daw*);
void v_daw_atm_sequence_free(t_daw_atm_sequence*);
void g_daw_item_get(t_daw*, int);

t_daw* g_daw_get();
int i_daw_get_sequence_index_from_name(t_daw *, int);
void v_daw_set_is_soloed(t_daw * self);
void v_daw_set_loop_mode(t_daw * self, int a_mode);
void v_daw_set_playback_cursor(t_daw*, double);
int i_daw_song_index_from_sequence_uid(t_daw*, int);
void v_daw_update_track_send(t_daw * self, int a_lock);
void v_daw_process_external_midi(
    t_daw * data,
    t_pytrack * a_track,
    int sample_count,
    int a_thread_num,
    t_daw_thread_storage * a_ts
);
void v_daw_offline_render(t_daw*, double, double, char*, int, int, int);
void v_daw_audio_items_run(
    t_daw*,
    t_daw_item_ref*,
    int,
    SGFLT**,
    SGFLT**,
    int*,
    t_daw_thread_storage*
);

void v_daw_paif_set_control(t_daw*, int, int, int, SGFLT);
void v_daw_papifx_set_control(int, int, SGFLT);

void v_daw_song_free(t_daw_song *);
void v_daw_process_note_offs(t_daw * self, int f_i, t_daw_thread_storage*);
void v_daw_process_midi(
    t_daw *,
    t_daw_item_ref*,
    int,
    int,
    int,
    long,
    t_daw_thread_storage*
);
void v_daw_zero_all_buffers(t_daw * self);
void v_daw_panic(t_daw * self);

void v_daw_process_atm(
    t_daw * self,
    int f_track_num,
    int f_index,
    int sample_count,
    int a_playback_mode,
    t_daw_thread_storage * a_ts
);

void v_daw_set_midi_device(int, int, int);
void v_daw_set_midi_devices();

void g_daw_midi_routing_list_init(t_daw_midi_routing_list*);

void g_daw_item_free(t_daw_item*);
void v_daw_update_audio_inputs();
void v_daw_set_playback_mode(
    t_daw * self,
    int a_mode,
    double a_beat,
    int a_lock
);

/*
 * @output: The track number to output to
 * @type:   ROUTE_TYPE_AUDIO 0, ROUTE_TYPE_SIDECHAIN 1, ROUTE_TYPE_MIDI 2
*/
void v_pytrack_routing_set(t_pytrack_routing*, int, int);
void v_pytrack_routing_free(t_pytrack_routing*);
void v_daw_run_engine(
    int a_sample_count,
    SGFLT** a_output,
    SGFLT* a_input_buffers
);
void v_daw_osc_send(t_osc_send_data * a_buffers);
void g_daw_instantiate();
void v_daw_wait_for_bus(t_pytrack * a_track);
void v_daw_sum_track_outputs(
    t_daw * self,
    t_pytrack * a_track,
    int a_sample_count,
    int a_playback_mode,
    t_daw_thread_storage * a_ts
);
void v_daw_open_project(int a_first_load);
void v_daw_reset_audio_item_read_heads(
    t_daw * self,
    t_audio_items * f_audio_items,
    double a_start_offset
);
void v_daw_process(t_thread_args * f_args);
void v_daw_process_track(
    t_daw * self,
    int a_global_track_num,
    int a_thread_num,
    int a_sample_count,
    int a_playback_mode,
    t_daw_thread_storage * a_ts
);
void v_daw_open_tracks();
void v_daw_configure(const char* a_key, const char* a_value);
void v_daw_offline_render_prep(t_daw * self);
//* Load the sequence pool at start up
void g_daw_seq_pool_load(t_daw*);
/* Set the active sequence
 * @uid: THe UID of the sequence to play
 */
void daw_set_sequence(t_daw* self, int uid);

extern t_daw * DAW;

#endif