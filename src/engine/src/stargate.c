#include <assert.h>
#include <string.h>
#include <time.h>

#include "globals.h"
#include "ipc.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "plugin.h"
#include "stargate.h"
#include "audio/input.h"
#include "audio/item.h"
#include "audio/sample_graph.h"
#include "audio/util.h"
#include "csv/1d.h"
#include "csv/kvp.h"
#include "ds/list.h"
#include "files.h"
#include "hardware/config.h"

#ifdef NO_MIDI
    #define t_midi_device void
    #define t_midi_device_list void

    void midiPoll(void * arg){}
    void midiDeviceRead(void * arg1, SGFLT arg2, int arg3){}
#else
    #include "hardware/midi.h"
#endif

int SG_OFFLINE_RENDER = 0;

SGFLT MASTER_VOL = 1.0f;
SGFLT **pluginOutputBuffers;
t_stargate * STARGATE = NULL;
int ZERO = 0;

#ifdef SG_DLL
    v_ui_send_callback UI_SEND_CALLBACK = NULL;

    void v_set_ui_callback(v_ui_send_callback a_callback){
        UI_SEND_CALLBACK = a_callback;
    }

    void v_ui_send(char * a_path, char * a_msg){
        assert(UI_SEND_CALLBACK);
        UI_SEND_CALLBACK(a_path, a_msg);
    }
#elif defined(WITH_SOCKET_IPC)

    void v_ui_send(char * a_path, char * a_msg){
        int msg_len = strlen(a_path) + strlen(a_msg);
        assert(msg_len < 24576);
        char msg[24576];
        sprintf(msg, "%s\n%s", a_path, a_msg);
        ipc_client_send(msg);
    }

#else

    void v_ui_send(char * a_path, char * a_msg){
        printf("path: '%s', msg: '%s'\n", a_path, a_msg);
    }

#endif



/* default generic t_sg_host->mix function pointer */
void v_default_mix()
{
    int f_i;
    int framesPerBuffer = STARGATE->sample_count;
    float* out = STARGATE->out;

    if(OUTPUT_CH_COUNT > 2)
    {
        int f_i2 = 0;
        memset(
            out,
            0,
            sizeof(float) * framesPerBuffer * OUTPUT_CH_COUNT
        );

        for(f_i = 0; f_i < framesPerBuffer; ++f_i)
        {
            out[f_i2 + MASTER_OUT_L] = (float)pluginOutputBuffers[0][f_i];
            out[f_i2 + MASTER_OUT_R] = (float)pluginOutputBuffers[1][f_i];
            f_i2 += OUTPUT_CH_COUNT;
        }
    }
    else
    {
        for(f_i = 0; f_i < framesPerBuffer; ++f_i)
        {
            *out = (float)pluginOutputBuffers[0][f_i];  // left
            ++out;
            *out = (float)pluginOutputBuffers[1][f_i];  // right
            ++out;
        }
    }
}

void g_sample_period_init(t_sample_period *self)
{
    int f_i;

    self->buffers[0] = NULL;
    self->buffers[1] = NULL;
    self->sc_buffers[0] = NULL;
    self->sc_buffers[1] = NULL;
    self->input_buffer = NULL;
    self->current_sample = 0;
    self->sample_count = 0;
    self->end_beat = 0.0;
    self->start_beat = 0.0;
    self->atm_tick_count = 0;

    for(f_i = 0; f_i < ATM_TICK_BUFFER_SIZE; ++f_i)
    {
        self->atm_ticks[f_i].sample = -1;
        self->atm_ticks[f_i].tick = -1;
        self->atm_ticks[f_i].beat = -99999999999.999999;
    }
}

void g_sg_seq_event_list_init(t_sg_seq_event_list * self){
    self->count = 0;
    self->pos = 0;
    self->events = NULL;
    g_sample_period_init(&self->period);
    v_sg_set_tempo(self, 128.0f);
}

void g_seq_event_result_init(t_sg_seq_event_result * self){
    self->count = 0;
    int f_i = 0;
    for(f_i = 0; f_i < 2; ++f_i)
    {
        self->sample_periods[f_i].playback_inc = 0.0f;
        self->sample_periods[f_i].samples_per_beat = 0.0f;
        self->sample_periods[f_i].tempo = 0.0f;
        g_sample_period_init(&self->sample_periods[f_i].period);
    }
}

void v_sample_period_split(
    t_sample_period_split* self,
    SGFLT ** a_buffers,
    SGFLT ** a_sc_buffers,
    int a_sample_count,
    double a_period_start_beat,
    double a_period_end_beat,
    double a_event1_beat,
    double a_event2_beat,
    long a_current_sample,
    SGFLT * a_input_buffer,
    int a_input_count
){
    self->periods[0].current_sample = a_current_sample;

    if(a_event1_beat <= a_period_start_beat ||
    (a_event1_beat >= a_period_end_beat && a_event2_beat >= a_period_end_beat))
    {
        self->count = 1;
        self->periods[0].sample_count = a_sample_count;
        self->periods[0].buffers[0] = a_buffers[0];
        self->periods[0].buffers[1] = a_buffers[1];

        if(a_sc_buffers)
        {
            self->periods[0].sc_buffers[0] = a_sc_buffers[0];
            self->periods[0].sc_buffers[1] = a_sc_buffers[1];
        }

        if(a_input_buffer)
        {
            self->periods[0].input_buffer = a_input_buffer;
        }
    }
    else if(
        a_event1_beat >= a_period_start_beat
        &&
        a_event1_beat < a_period_end_beat
    ){
        if(a_event2_beat >= a_period_end_beat){
            self->count = 1;
            self->periods[0].sample_count = a_sample_count;

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_period_end_beat;

            self->periods[0].buffers[0] = a_buffers[0];
            self->periods[0].buffers[1] = a_buffers[1];

            if(a_sc_buffers){
                self->periods[0].sc_buffers[0] = a_sc_buffers[0];
                self->periods[0].sc_buffers[1] = a_sc_buffers[1];
            }

            if(a_input_buffer){
                self->periods[0].input_buffer = a_input_buffer;
            }
        } else if(
            a_event1_beat == a_event2_beat
            ||
            a_event2_beat >= a_period_end_beat
        ){
            self->count = 2;

            double f_diff = (a_period_end_beat - a_period_start_beat);
            double f_distance = a_event1_beat - a_period_start_beat;
            int f_split =
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_event1_beat;

            self->periods[1].start_beat = a_event1_beat;
            self->periods[1].end_beat = a_period_end_beat;

            self->periods[0].sample_count = f_split;
            self->periods[1].sample_count = a_sample_count - f_split;

            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[0].buffers[0] = a_buffers[0];
            self->periods[0].buffers[1] = a_buffers[1];

            if(a_sc_buffers){
                self->periods[0].sc_buffers[0] = a_sc_buffers[0];
                self->periods[0].sc_buffers[1] = a_sc_buffers[1];
            }

            if(a_input_buffer){
                self->periods[0].input_buffer = a_input_buffer;
            }

            self->periods[1].buffers[0] = &a_buffers[0][f_split];
            self->periods[1].buffers[1] = &a_buffers[1][f_split];

            if(a_sc_buffers){
                self->periods[1].sc_buffers[0] = &a_sc_buffers[0][f_split];
                self->periods[1].sc_buffers[1] = &a_sc_buffers[1][f_split];
            }

            if(a_input_buffer){
                self->periods[1].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }
        } else if(a_event2_beat < a_period_end_beat){
            self->count = 3;

            double f_diff = (a_period_end_beat - a_period_start_beat);

            double f_distance = a_event1_beat - a_period_start_beat;
            int f_split =
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_event1_beat;

            self->periods[1].start_beat = a_event1_beat;
            self->periods[1].end_beat = a_event2_beat;

            self->periods[2].start_beat = a_event2_beat;
            self->periods[2].end_beat = a_period_end_beat;

            self->periods[0].sample_count = f_split;
            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[0].buffers[0] = a_buffers[0];
            self->periods[0].buffers[1] = a_buffers[1];

            if(a_sc_buffers){
                self->periods[0].sc_buffers[0] = a_sc_buffers[0];
                self->periods[0].sc_buffers[1] = a_sc_buffers[1];
            }

            if(a_input_buffer){
                self->periods[0].input_buffer = a_input_buffer;
            }

            f_distance = a_event2_beat - a_event1_beat;
            f_split +=
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[1].sample_count = f_split;
            self->periods[1].buffers[0] = &a_buffers[0][f_split];
            self->periods[1].buffers[1] = &a_buffers[1][f_split];

            if(a_sc_buffers){
                self->periods[1].sc_buffers[0] = &a_sc_buffers[0][f_split];
                self->periods[1].sc_buffers[1] = &a_sc_buffers[1][f_split];
            }

            if(a_input_buffer){
                self->periods[1].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }

            f_distance = a_period_end_beat - a_event2_beat;
            f_split +=
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            f_split = a_sample_count - f_split;
            self->periods[2].sample_count = f_split;
            self->periods[2].buffers[0] = &a_buffers[0][f_split];
            self->periods[2].buffers[1] = &a_buffers[1][f_split];

            if(a_sc_buffers){
                self->periods[2].sc_buffers[0] = &a_sc_buffers[0][f_split];
                self->periods[2].sc_buffers[1] = &a_sc_buffers[1][f_split];
            }

            if(a_input_buffer){
                self->periods[2].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }
        } else {
            assert(0);
        }
    } else {
        assert(0);
    }
}

void g_stargate_get(SGFLT a_sr, t_midi_device_list * a_midi_devices)
{
    clalloc((void**)&STARGATE, sizeof(t_stargate));
    STARGATE->audio_pool = g_audio_pool_get(a_sr);
    STARGATE->midi_devices = a_midi_devices;
    STARGATE->current_host = NULL;
    STARGATE->sample_count = 512;
    STARGATE->midi_learn = 0;
    STARGATE->is_offline_rendering = 0;
    pthread_spin_init(&STARGATE->main_lock, 0);
    STARGATE->project_folder = (char*)malloc(sizeof(char) * 1024);
    STARGATE->audio_folder = (char*)malloc(sizeof(char) * 1024);
    STARGATE->audio_tmp_folder = (char*)malloc(sizeof(char) * 1024);
    STARGATE->samples_folder = (char*)malloc(sizeof(char) * 1024);
    STARGATE->samplegraph_folder = (char*)malloc(sizeof(char) * 1024);
    STARGATE->audio_pool_file = (char*)malloc(sizeof(char) * 1024);
    STARGATE->plugins_folder = (char*)malloc(sizeof(char) * 1024);

    STARGATE->preview_wav_item = 0;
    STARGATE->preview_audio_item = g_audio_item_get(a_sr);
    STARGATE->preview_start = 0.0f;
    STARGATE->preview_amp_lin = 1.0f;
    STARGATE->is_previewing = 0;
    STARGATE->preview_max_sample_count = ((int)(a_sr)) * 30;
    STARGATE->playback_mode = 0;

    pthread_mutex_init(&STARGATE->audio_inputs_mutex, NULL);
    pthread_mutex_init(&STARGATE->exit_mutex, NULL);

    int f_i;

    hpalloc(
        (void**)&STARGATE->audio_inputs,
        sizeof(t_pyaudio_input) * AUDIO_INPUT_TRACK_COUNT
    );

    for(f_i = 0; f_i < AUDIO_INPUT_TRACK_COUNT; ++f_i){
        g_pyaudio_input_init(
            &STARGATE->audio_inputs[f_i],
            a_sr
        );
    }

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i){
        STARGATE->thread_storage[f_i].sample_rate = a_sr;
        STARGATE->thread_storage[f_i].current_host = SG_HOST_DAW;
    }

    /* Create OSC thread */

    pthread_spin_init(&STARGATE->ui_spinlock, 0);
    STARGATE->osc_queue_index = 0;
    STARGATE->osc_cursor_message = (char*)malloc(sizeof(char) * 1024);

    for(f_i = 0; f_i < MAX_PLUGIN_POOL_COUNT; ++f_i){
        STARGATE->plugin_pool[f_i].active = 0;
    }
}

void v_set_control_from_atm(
    t_seq_event *event,
    int a_plugin_uid,
    t_pytrack * f_track
){
    if(!STARGATE->is_offline_rendering)
    {
        sprintf(
            f_track->osc_cursor_message, "%i|%i|%f",
            a_plugin_uid, event->port, event->value);
        v_queue_osc_message("pc", f_track->osc_cursor_message);
    }
}

void v_set_control_from_cc(
    t_seq_event* event,
    t_pytrack* f_track
){
    if(!STARGATE->is_offline_rendering){
        sprintf(
            f_track->osc_cursor_message,
            "%i|%i|%i",
            f_track->track_num, event->param,
            (int)(event->value)
        );
        v_queue_osc_message("cc", f_track->osc_cursor_message);
    }
}

void v_set_host(int a_mode){
    int f_i;

    assert(a_mode >= 0 && a_mode < SG_HOST_COUNT);

    pthread_spin_lock(&STARGATE->main_lock);

    STARGATE->current_host = &STARGATE->hosts[a_mode];

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i){
        STARGATE->thread_storage[f_i].current_host = a_mode;
    }

#ifndef NO_MIDI

    t_midi_device * f_device;

    if(STARGATE->midi_devices)
    {
        for(f_i = 0; f_i < STARGATE->midi_devices->count; ++f_i){
            f_device = &STARGATE->midi_devices->devices[f_i];
            if(f_device->loaded){
                midiPoll(f_device);
                f_device->midiEventReadIndex = f_device->midiEventWriteIndex;
            }

        }
    }
#endif

    pthread_spin_unlock(&STARGATE->main_lock);

    if(STARGATE->current_host->audio_inputs){
        STARGATE->current_host->audio_inputs();
    }
}

#ifdef __linux__
/* Create a clock_t with clock() when beginning some work,
 * and use this function to print the completion time*/
double v_print_benchmark(
    char * a_message,
    struct timespec f_start,
    struct timespec f_finish
){
    double elapsed;
    elapsed = (f_finish.tv_sec - f_start.tv_sec);
    elapsed += (f_finish.tv_nsec - f_start.tv_nsec) / 1000000000.0;

    printf ( "\n\nCompleted %s in %lf seconds\n", a_message, elapsed);

    return elapsed;
}
#endif

void v_zero_buffer(SGFLT ** a_buffers, int a_count)
{
    int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffers[0][f_i2] = 0.0f;
        a_buffers[1][f_i2] = 0.0f;
        ++f_i2;
    }
}

NO_OPTIMIZATION void v_open_track(
    t_pytrack* a_track,
    char* a_tracks_folder,
    int a_index
){
    char f_file_name[1024];

    sprintf(f_file_name, "%s%s%i", a_tracks_folder, PATH_SEP, a_index);

    if(i_file_exists(f_file_name)){
        printf("%s exists, opening track\n", f_file_name);
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
            f_file_name,
            LARGE_STRING
        );

        while(1){
            v_iterate_2d_char_array(f_2d_array);

            if(f_2d_array->eof){
                break;
            }

            //plugin
            if(f_2d_array->current_str[0] == 'p'){
                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                int f_plugin_index = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                int f_plugin_uid = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array); //mute
                v_iterate_2d_char_array(f_2d_array); //solo
                v_iterate_2d_char_array(f_2d_array);
                int f_power = atoi(f_2d_array->current_str);

                v_set_plugin_index(
                    a_track,
                    f_index,
                    f_plugin_index,
                    f_plugin_uid,
                    f_power,
                    0
                );
            } else {
                printf(
                    "Invalid track identifier '%c'\n",
                    f_2d_array->current_str[0]
                );
                assert(0);
            }
        }

        g_free_2d_char_array(f_2d_array);
    } else {
        printf("%s does not exist, resetting track\n", f_file_name);
        int f_i;
        for(f_i = 0; f_i < MAX_PLUGIN_COUNT; ++f_i){
            v_set_plugin_index(a_track, f_i, 0, -1, 0, 0);
        }
    }
}

t_pytrack * g_pytrack_get(int a_track_num, SGFLT a_sr)
{
    int f_i = 0;

    t_pytrack * f_result;
    clalloc((void**)&f_result, sizeof(t_pytrack));

    f_result->track_num = a_track_num;
    f_result->channels = 2;
    f_result->extern_midi = 0;
    f_result->extern_midi_count = &ZERO;
    f_result->midi_device = 0;
    f_result->sc_buffers_dirty = 0;
    f_result->event_list = shds_list_new(MAX_EVENT_BUFFER_SIZE, NULL);

    pthread_spin_init(&f_result->lock, 0);

    hpalloc((void**)&f_result->buffers, (sizeof(SGFLT*) * f_result->channels));
    hpalloc((void**)&f_result->sc_buffers,
        (sizeof(SGFLT*) * f_result->channels));

    for(f_i = 0; f_i < f_result->channels; ++f_i){
        clalloc(
            (void**)&f_result->buffers[f_i],
            sizeof(SGFLT) * FRAMES_PER_BUFFER
        );
        clalloc(
            (void**)&f_result->sc_buffers[f_i],
            sizeof(SGFLT) * FRAMES_PER_BUFFER
        );
    }

    v_zero_buffer(f_result->buffers, FRAMES_PER_BUFFER);
    v_zero_buffer(f_result->sc_buffers, FRAMES_PER_BUFFER);

    f_result->mute = 0;
    f_result->solo = 0;

    f_result->bus_counter = 0;

    for(f_i = 0; f_i < MAX_EVENT_BUFFER_SIZE; ++f_i){
        v_ev_clear(&f_result->event_buffer[f_i]);
    }

    for(f_i = 0; f_i < MAX_PLUGIN_TOTAL_COUNT; ++f_i)
    {
        f_result->plugins[f_i] = NULL;
    }

    for(f_i = 0; f_i < MIDI_NOTE_COUNT; ++f_i){
        f_result->note_offs[f_i] = -1;
    }

    f_result->period_event_index = 0;

    f_result->peak_meter = g_pkm_get();

    g_rmp_init(&f_result->fade_env, a_sr);
    v_rmp_set_time(&f_result->fade_env, 0.03f);
    f_result->fade_state = 0;

    hpalloc((void**)&f_result->osc_cursor_message, sizeof(char) * 1024);

    f_result->status = STATUS_NOT_PROCESSED;

    return f_result;
}

void v_set_preview_file(const char * a_file){
    t_audio_pool_item * f_result = g_audio_pool_item_get(
        0,
        a_file,
        STARGATE->thread_storage[0].sample_rate
    );

    if(f_result){
        if(i_audio_pool_item_load(f_result, 0)){
            t_audio_pool_item * f_old = STARGATE->preview_wav_item;

            pthread_spin_lock(&STARGATE->main_lock);

            STARGATE->preview_wav_item = f_result;

            STARGATE->preview_audio_item->ratio =
                    STARGATE->preview_wav_item->ratio_orig;

            STARGATE->is_previewing = 1;

            v_ifh_retrigger(
                &STARGATE->preview_audio_item->sample_read_heads[0],
                AUDIO_ITEM_PADDING_DIV2
            );
            v_adsr_retrigger(
                &STARGATE->preview_audio_item->adsrs[0]
            );

            pthread_spin_unlock(&STARGATE->main_lock);

            if(f_old){
                v_audio_pool_item_free(f_old);
            }
        } else {
            fprintf(
                stderr,
                "i_audio_pool_item_load(f_result) failed in "
                "v_set_preview_file\n"
            );
        }
    } else {
        STARGATE->is_previewing = 0;
        fprintf(
            stderr,
            "g_audio_pool_item_get returned zero. could not load "
            "preview item.\n"
        );
    }
}

double f_bpm_to_seconds_per_beat(double a_tempo){
    return (60.0f / a_tempo);
}

double f_samples_to_beat_count(
    int a_sample_count,
    double a_tempo,
    SGFLT a_sr
){
    double f_seconds_per_beat = f_bpm_to_seconds_per_beat(a_tempo);
    double f_seconds = (double)(a_sample_count) / a_sr;
    return f_seconds / f_seconds_per_beat;
}

int i_beat_count_to_samples(
    double a_beat_count,
    SGFLT a_tempo,
    SGFLT a_sr
){
    double f_seconds = f_bpm_to_seconds_per_beat(a_tempo) * a_beat_count;
    return (int)(f_seconds * a_sr);
}


void v_buffer_mix(
    int a_count,
    SGFLT ** __restrict__ a_buffer_src,
    SGFLT ** __restrict__ a_buffer_dest
){
    int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffer_dest[0][f_i2] += a_buffer_src[0][f_i2];
        a_buffer_dest[1][f_i2] += a_buffer_src[1][f_i2];
        ++f_i2;
    }
}

void v_wait_for_threads(){
    int f_i;

    for(f_i = 1; f_i < (STARGATE->worker_thread_count); ++f_i){
        pthread_spin_lock(&STARGATE->thread_locks[f_i]);
        pthread_spin_unlock(&STARGATE->thread_locks[f_i]);
    }
}

void g_pynote_init(
    t_seq_event* f_result,
    int a_note,
    int a_vel,
    SGFLT a_start,
    SGFLT a_length
){
    f_result->type = EVENT_NOTEON;
    f_result->length = a_length;
    f_result->note = a_note;
    f_result->start = a_start;
    f_result->velocity = a_vel;
}

t_seq_event * g_pynote_get(
    int a_note,
    int a_vel,
    SGFLT a_start,
    SGFLT a_length
){
    t_seq_event * f_result =
        (t_seq_event*)malloc(sizeof(t_seq_event));
    g_pynote_init(f_result, a_note, a_vel, a_start, a_length);
    return f_result;
}

void g_pycc_init(
    t_seq_event * f_result,
    int a_cc_num,
    SGFLT a_cc_val,
    SGFLT a_start
){
    f_result->type = EVENT_CONTROLLER;
    f_result->param = a_cc_num;
    f_result->value = a_cc_val;
    f_result->start = a_start;
}

t_seq_event * g_pycc_get(int a_cc_num, SGFLT a_cc_val, SGFLT a_start){
    t_seq_event * f_result =
        (t_seq_event*)malloc(sizeof(t_seq_event));
    g_pycc_init(f_result, a_cc_num, a_cc_val, a_start);
    return f_result;
}

void g_pypitchbend_init(
    t_seq_event * f_result,
    SGFLT a_start,
    SGFLT a_value
){
    f_result->type = EVENT_PITCHBEND;
    f_result->start = a_start;
    f_result->value = a_value;
}

t_seq_event * g_pypitchbend_get(SGFLT a_start, SGFLT a_value)
{
    t_seq_event * f_result =
        (t_seq_event*)malloc(sizeof(t_seq_event));
    g_pypitchbend_init(f_result, a_start, a_value);
    return f_result;
}

void v_sample_period_set_atm_events(
    t_sample_period * self,
    t_sg_seq_event_list * a_event_list,
    long a_current_sample,
    int a_sample_count
){
    double pos;
    double current_sample = (double)(a_current_sample);
    double next_sample = (double)(a_current_sample + (long)a_sample_count);
    self->atm_tick_count = 0;

    for(
        ;
        a_event_list->atm_pos < next_sample;
        a_event_list->atm_pos += a_event_list->atm_clock_samples
    ){
        assert(self->atm_tick_count < ATM_TICK_BUFFER_SIZE);

        pos = (a_event_list->atm_pos - current_sample);
        self->atm_ticks[self->atm_tick_count].sample = (int)(pos);

        self->atm_ticks[self->atm_tick_count].beat =
            self->start_beat +
            f_samples_to_beat_count(
                self->atm_ticks[self->atm_tick_count].sample + 1, // round up
                a_event_list->tempo,
                STARGATE->thread_storage[0].sample_rate);
        // BUG:  This doesn't quite line up... the result can be off by one
        self->atm_ticks[self->atm_tick_count].tick =
            (int)((self->atm_ticks[self->atm_tick_count].beat /
                SG_AUTOMATION_RESOLUTION) + 0.5f);

        ++self->atm_tick_count;
    }
}

void v_sg_set_time_params(t_sample_period * self)
{
    self->start_beat = self->end_beat;
    self->end_beat = self->start_beat + self->period_inc_beats;
}

void v_sg_seq_event_result_set_default(
    t_sg_seq_event_result * self,
    t_sg_seq_event_list * a_list,
    SGFLT** a_buffers,
    SGFLT * a_input_buffers,
    int a_input_count,
    int a_sample_count,
    long a_current_sample
){
    self->count = 1;
    t_sample_period * f_period = &self->sample_periods[0].period;
    f_period->period_inc_beats =
        ((a_list->playback_inc) * ((SGFLT)(a_sample_count)));
    v_sg_set_time_params(f_period);
    f_period->current_sample = a_current_sample;
    f_period->sample_count = a_sample_count;
    f_period->buffers[0] = a_buffers[0];
    f_period->buffers[1] = a_buffers[1];
    f_period->input_buffer = a_input_buffers;
}

void v_set_sample_period(
    t_sample_period * self,
    SGFLT a_playback_inc,
    SGFLT ** a_buffers,
    SGFLT ** a_sc_buffers,
    SGFLT * a_input_buffers,
    int a_sample_count,
    long a_current_sample
){
    self->period_inc_beats = a_playback_inc * ((SGFLT)(a_sample_count));

    self->current_sample = a_current_sample;
    self->sample_count = a_sample_count;

    if(a_sc_buffers)
    {
        self->sc_buffers[0] = a_sc_buffers[0];
        self->sc_buffers[1] = a_sc_buffers[1];
    }
    else
    {
        self->sc_buffers[0] = NULL;
        self->sc_buffers[1] = NULL;
    }

    self->buffers[0] = a_buffers[0];
    self->buffers[1] = a_buffers[1];
    self->input_buffer = a_input_buffers;
}

void v_sg_set_tempo(t_sg_seq_event_list * self, SGFLT a_tempo){
    SGFLT f_sample_rate = STARGATE->thread_storage[0].sample_rate;
    self->tempo = a_tempo;
    self->playback_inc = (1.0f / f_sample_rate) / (60.0f / a_tempo);
    self->samples_per_beat = (f_sample_rate) / (a_tempo / 60.0f);
    self->atm_clock_samples = self->samples_per_beat * SG_AUTOMATION_RESOLUTION;
}

void v_sg_set_playback_pos(
    t_sg_seq_event_list * self,
    double a_beat,
    long a_current_sample
){
    t_sg_seq_event * f_ev;
    self->period.start_beat = a_beat;
    self->period.end_beat = a_beat;
    self->atm_pos = (double)a_current_sample;
    int f_found_tempo = 0;
    int f_i;
    self->pos = 0;

    for(f_i = 0; f_i < self->count; ++f_i){
         f_ev = &self->events[f_i];

         if(f_ev->beat > a_beat){
             break;
         }

         if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE){
             v_sg_set_tempo(self, f_ev->tempo);
             f_found_tempo = 1;
         }
    }

    assert(f_found_tempo);
}


void v_sg_seq_event_list_set(
    t_sg_seq_event_list * self,
    t_sg_seq_event_result* a_result,
    SGFLT** a_buffers,
    SGFLT* a_input_buffers,
    int a_input_count,
    int a_sample_count,
    long a_current_sample,
    int a_loop_mode
){
    int f_i;
    for(f_i = 0; f_i < 2; ++f_i)
    {
        a_result->sample_periods[f_i].is_looping = 0;
        a_result->sample_periods[f_i].tempo = self->tempo;
    }

    if(self->pos >= self->count)
    {
        v_sg_seq_event_result_set_default(a_result, self,
            a_buffers, a_input_buffers, a_input_count,
            a_sample_count, a_current_sample);
    }
    else
    {
        a_result->count = 0;

        double f_loop_start = -1.0f;

        t_sg_seq_event * f_ev = NULL;
        //The scratchpad sample period for iterating
        t_sample_period * f_tmp_period = NULL;
        //temp variable for the outputted sample period
        t_sg_seq_event_period * f_period = NULL;

        v_set_sample_period(&self->period, self->playback_inc,
            a_buffers, NULL, a_input_buffers,
            a_sample_count, a_current_sample);

        v_sg_set_time_params(&self->period);

        while(1)
        {
            if(self->pos >= self->count)
            {
                break;
            }
            else if(self->events[self->pos].beat >= self->period.start_beat &&
                    self->events[self->pos].beat < self->period.end_beat)
            {
                if(self->events[self->pos].beat == self->period.start_beat)
                {
                    a_result->count = 1;
                }
                else
                {
                    a_result->count = 2;
                }

                f_ev = &self->events[self->pos];
                //The period that is returned to the main loop

                if(f_ev->type == SEQ_EVENT_LOOP && a_loop_mode)
                {
                    f_loop_start = f_ev->start_beat;
                    f_period = &a_result->sample_periods[a_result->count - 1];
                    f_period->is_looping = 1;
                }
                else if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE)
                {
                    if(a_result->count == 2)
                    {
                        f_period = &a_result->sample_periods[0];

                        f_period->tempo = self->tempo;
                        f_period->playback_inc = self->playback_inc;
                        f_period->samples_per_beat = self->samples_per_beat;
                    }

                    v_sg_set_tempo(self, f_ev->tempo);

                    f_period = &a_result->sample_periods[a_result->count - 1];

                    f_period->tempo = self->tempo;
                    f_period->playback_inc = self->playback_inc;
                    f_period->samples_per_beat = self->samples_per_beat;
                }
                ++self->pos;
            }
            else if(self->events[self->pos].beat < self->period.start_beat)
            {
                f_ev = &self->events[self->pos];

                if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE)
                {
                    v_sg_set_tempo(self, f_ev->tempo);
                }

                ++self->pos;
            }
            else
            {
                break;
            }
        }

        if(a_result->count == 0)
        {
            a_result->count = 1;

            f_period = &a_result->sample_periods[0];

            v_set_sample_period(&f_period->period, self->playback_inc,
                a_buffers, NULL, a_input_buffers,
                a_sample_count, a_current_sample);

            f_period->tempo = self->tempo;
            f_period->playback_inc = self->playback_inc;
            f_period->samples_per_beat = self->samples_per_beat;

            f_period->period.start_beat = self->period.start_beat;
            f_period->period.end_beat = self->period.end_beat;
        }
        else if(a_result->count == 1)
        {
            f_tmp_period = &self->period;
            f_period = &a_result->sample_periods[0];

            v_set_sample_period(&f_period->period, self->playback_inc,
                f_tmp_period->buffers, NULL,
                f_tmp_period->input_buffer,
                f_tmp_period->sample_count,
                f_tmp_period->current_sample);

            f_period->period.period_inc_beats = ((f_period->playback_inc) *
                ((SGFLT)(f_tmp_period->sample_count)));

            if(f_loop_start >= 0.0)
            {
                self->pos = 0;
                f_period->period.start_beat = f_loop_start;
            }
            else
            {
                f_period->period.start_beat = f_tmp_period->start_beat;
            }

            f_period->period.end_beat = f_period->period.start_beat +
                f_period->period.period_inc_beats;
            self->period.end_beat = f_period->period.end_beat;
        }
        else if(a_result->count == 2)
        {
            f_period = &a_result->sample_periods[0];

            v_sample_period_split(
                &a_result->splitter, self->period.buffers, NULL,
                self->period.sample_count,
                self->period.start_beat,
                self->period.end_beat,
                f_ev->beat, f_ev->beat,
                self->period.current_sample,
                self->period.input_buffer, a_input_count);

            f_tmp_period = &a_result->splitter.periods[0];

            v_set_sample_period(&f_period->period, self->playback_inc,
                f_tmp_period->buffers, NULL,
                f_tmp_period->input_buffer,
                f_tmp_period->sample_count,
                f_tmp_period->current_sample);

            f_period->period.period_inc_beats = ((f_period->playback_inc) *
                ((SGFLT)(f_tmp_period->sample_count)));

            f_period->period.start_beat = f_tmp_period->start_beat;

            f_period->period.end_beat = f_tmp_period->end_beat;

            if(a_result->splitter.count == 2)
            {
                f_period = &a_result->sample_periods[1];
                f_tmp_period = &a_result->splitter.periods[1];

                v_set_sample_period(
                    &f_period->period, self->playback_inc,
                    f_tmp_period->buffers, NULL,
                    f_tmp_period->input_buffer,
                    f_tmp_period->sample_count,
                    f_tmp_period->current_sample);

                if(f_loop_start >= 0.0)
                {
                    self->pos = 0;
                    f_period->period.start_beat = f_loop_start;
                }
                else
                {
                    f_period->period.start_beat = f_tmp_period->start_beat;
                }

                f_period->period.period_inc_beats = ((f_period->playback_inc) *
                    ((SGFLT)(f_tmp_period->sample_count)));
                f_period->period.end_beat = f_period->period.start_beat +
                    f_period->period.period_inc_beats;
            }
            else if(a_result->splitter.count == 1)
            {
                // TODO:  Debug how and why this happens
            }
            else
            {
                assert(0);
            }

            self->period.end_beat = f_period->period.end_beat;
        }
        else
        {
            assert(0);
        }
    }
}


void v_sg_configure(const char* a_key, const char* a_value){
    printf("v_sg_configure:  key: \"%s\", value: \"%s\"\n", a_key, a_value);

    if(!strcmp(a_key, SG_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL)){
        t_1d_char_array * f_val_arr = c_split_str(
            a_value,
            '|',
            3,
            TINY_STRING
        );

        int f_plugin_uid = atoi(f_val_arr->array[0]);
        int f_port = atoi(f_val_arr->array[1]);
        SGFLT f_value = atof(f_val_arr->array[2]);

        t_plugin * f_instance;
        pthread_spin_lock(&STARGATE->main_lock);

        f_instance = &STARGATE->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->set_port_value(
                f_instance->plugin_handle, f_port, f_value);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }
        pthread_spin_unlock(&STARGATE->main_lock);
        g_free_1d_char_array(f_val_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_CONFIGURE_PLUGIN)){
        t_1d_char_array * f_val_arr = c_split_str_remainder(
            a_value,
            '|',
            3,
            LARGE_STRING
        );
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        char * f_key = f_val_arr->array[1];
        char * f_message = f_val_arr->array[2];

        t_plugin * f_instance = &STARGATE->plugin_pool[f_plugin_uid];

        if(f_instance){
            f_instance->descriptor->configure(
                f_instance->plugin_handle,
                f_key,
                f_message,
                &STARGATE->main_lock
            );
        } else {
            printf("Error, no valid plugin instance\n");
        }

        g_free_1d_char_array(f_val_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_MASTER_VOL)){
        MASTER_VOL = atof(a_value);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_AUDIO_IN_VOL)){
        t_1d_char_array * f_val_arr = c_split_str(
            a_value,
            '|',
            2,
            SMALL_STRING
        );
        int f_index = atoi(f_val_arr->array[0]);
        SGFLT f_vol = atof(f_val_arr->array[1]);
        SGFLT f_vol_linear = f_db_to_linear_fast(f_vol);

        g_free_1d_char_array(f_val_arr);

        t_pyaudio_input * f_input = &STARGATE->audio_inputs[f_index];

        f_input->vol = f_vol;
        f_input->vol_linear = f_vol_linear;
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_KILL_ENGINE)){
        pthread_spin_lock(&STARGATE->main_lock);
        assert(0);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_EXIT)){
        pthread_mutex_lock(&STARGATE->exit_mutex);
        exiting = 1;
        pthread_mutex_unlock(&STARGATE->exit_mutex);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_LOAD_CC_MAP)){
        t_1d_char_array * f_val_arr = c_split_str_remainder(
            a_value,
            '|',
            2,
            SMALL_STRING
        );
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        STARGATE->plugin_pool[f_plugin_uid].descriptor->set_cc_map(
            STARGATE->plugin_pool[f_plugin_uid].plugin_handle,
            f_val_arr->array[1]
        );
        g_free_1d_char_array(f_val_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_MIDI_LEARN)){
        STARGATE->midi_learn = 1;
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_ADD_TO_AUDIO_POOL)){
        t_1d_char_array* val_arr = c_split_str_remainder(
            a_value,
            '|',
            3,
            SMALL_STRING
        );
        int uid = atoi(val_arr->array[0]);
        SGFLT volume = atof(val_arr->array[1]);
        volume = f_db_to_linear(volume);
        t_audio_pool_item * result = v_audio_pool_add_item(
            STARGATE->audio_pool,
            uid,
            volume,
            val_arr->array[2]
        );
        i_audio_pool_item_load(result, 1);
        v_create_sample_graph(result);
        g_free_1d_char_array(val_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_AUDIO_POOL_ENTRY_VOL)){
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        int uid = atoi(f_kvp->key);
        SGFLT vol = f_db_to_linear(
            atof(f_kvp->value)
        );
        pthread_spin_lock(&STARGATE->main_lock);
        STARGATE->audio_pool->items[uid].volume = vol;
        pthread_spin_unlock(&STARGATE->main_lock);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_PREVIEW_SAMPLE)){
        v_set_preview_file(a_value);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_STOP_PREVIEW)){
        if(STARGATE->is_previewing)
        {
            pthread_spin_lock(&STARGATE->main_lock);
            v_adsr_release(&STARGATE->preview_audio_item->adsrs[0]);
            pthread_spin_unlock(&STARGATE->main_lock);
        }
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_RATE_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(SMALL_STRING);
        char f_tmp_char[SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = (char*)malloc(sizeof(char) * TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_in_file, f_arr->current_str);
        char * f_out_file = (char*)malloc(sizeof(char) * TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        SGFLT f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        SGFLT f_end = atof(f_arr->current_str);

        v_rate_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_LOAD_AB_SET))
    {
        int f_mode = atoi(a_value);
        v_set_host(f_mode);
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_ENGINE))
    {
        int f_val = atoi(a_value);
        assert(f_val == 0 || f_val == 1);
        pthread_spin_lock(&STARGATE->main_lock);
        STARGATE->is_offline_rendering = f_val;
        pthread_spin_unlock(&STARGATE->main_lock);
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_PITCH_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(SMALL_STRING);
        char f_tmp_char[SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = (char*)malloc(sizeof(char) * TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_in_file, f_arr->current_str);
        char * f_out_file = (char*)malloc(sizeof(char) * TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        SGFLT f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        SGFLT f_end = atof(f_arr->current_str);

        v_pitch_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_CLEAN_AUDIO_POOL))
    {
        t_2d_char_array * f_arr = g_get_2d_array(LARGE_STRING);
        int f_uid;
        strcpy(f_arr->array, a_value);

        while(!f_arr->eof)
        {
            v_iterate_2d_char_array(f_arr);
            f_uid = atoi(f_arr->current_str);
            v_audio_pool_remove_item(STARGATE->audio_pool, f_uid);
        }

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_AUDIO_POOL_ITEM_RELOAD))
    {
        int f_uid = atoi(a_value);
        t_audio_pool_item * f_old =
                g_audio_pool_get_item_by_uid(STARGATE->audio_pool, f_uid);
        t_audio_pool_item * f_new =
                g_audio_pool_item_get(f_uid, f_old->path,
                STARGATE->audio_pool->sample_rate);

        SGFLT * f_old_samples[2];
        f_old_samples[0] = f_old->samples[0];
        f_old_samples[1] = f_old->samples[1];

        pthread_spin_lock(&STARGATE->main_lock);

        f_old->channels = f_new->channels;
        f_old->length = f_new->length;
        f_old->ratio_orig = f_new->ratio_orig;
        f_old->sample_rate = f_new->sample_rate;
        f_old->samples[0] = f_new->samples[0];
        f_old->samples[1] = f_new->samples[1];

        pthread_spin_unlock(&STARGATE->main_lock);

        if(f_old_samples[0])
        {
            free(f_old_samples[0]);
        }

        if(f_old_samples[1])
        {
            free(f_old_samples[1]);
        }

        free(f_new);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }

}


/*Function for passing to plugins that re-use the wav pool*/
t_audio_pool_item * g_audio_pool_item_get_plugin(int a_uid)
{
    return g_audio_pool_get_item_by_uid(STARGATE->audio_pool, a_uid);
}


/* Disable the optimizer for this function because it causes a
 * SEGFAULT on ARM (which could not be reproduced on x86)
 * This is not a performance-critical function. */
NO_OPTIMIZATION void v_set_plugin_index(
    t_pytrack * f_track,
    int a_index,
    int a_plugin_index,
    int a_plugin_uid,
    int a_power,
    int a_lock
){
    int f_i = 0;
    t_plugin * f_plugin = NULL;

    if(a_plugin_index){
        printf("Plugin %i index set to %i\n", a_index, a_plugin_index);
        f_plugin = &STARGATE->plugin_pool[a_plugin_uid];

        if(!f_plugin->active){
            printf("Initializing plugin\n");
            g_plugin_init(
                f_plugin,
                (int)STARGATE->thread_storage[0].sample_rate,
                a_plugin_index,
                g_audio_pool_item_get_plugin,
                a_plugin_uid,
                v_queue_osc_message
            );
            printf("Finished initializing plugin\n");

            char f_file_name[1024];
            snprintf(
                f_file_name,
                1024,
                "%s%i",
                STARGATE->plugins_folder,
                a_plugin_uid
            );

            if(i_file_exists(f_file_name)){
                printf("Loading plugin\n");
                f_plugin->descriptor->load(
                    f_plugin->plugin_handle,
                    f_plugin->descriptor,
                    f_file_name
                );
            }
        }
    }

    if(a_lock){
        printf("Locking main_lock\n");
        pthread_spin_lock(&STARGATE->main_lock);
    }

    if(f_plugin){
        f_plugin->power = a_power;

        printf("Connecting buffers\n");
        for(f_i = 0; f_i < f_track->channels; ++f_i){
            f_plugin->descriptor->connect_buffer(
                f_plugin->plugin_handle,
                f_i, f_track->buffers[f_i],
                0
            );
            f_plugin->descriptor->connect_buffer(
                f_plugin->plugin_handle,
                f_i,
                f_track->sc_buffers[f_i],
                1
            );
        }
    }

    f_track->plugins[a_index] = f_plugin;

    if(a_lock){
        printf("Unlocking main_lock\n");
        pthread_spin_unlock(&STARGATE->main_lock);
    }
}

void v_run(
    SGFLT** buffers,
    SGFLT* a_input,
    int sample_count
){
    pthread_spin_lock(&STARGATE->main_lock);

    if(likely(!STARGATE->is_offline_rendering)){
        v_run_main_loop(sample_count, buffers, a_input);
    } else {
        /*Clear the output buffer*/
        int f_i;

        for(f_i = 0; f_i < sample_count; ++f_i){
            buffers[0][f_i] = 0.0f;
            buffers[1][f_i] = 0.0f;
        }
    }

    pthread_spin_unlock(&STARGATE->main_lock);
}

void v_run_main_loop(
    int sample_count,
    SGFLT** a_buffers,
    PluginData* a_input_buffers
){
    STARGATE->current_host->run(sample_count, a_buffers, a_input_buffers);

    if(unlikely(STARGATE->is_previewing))
    {
        int f_i;
        t_audio_item * f_audio_item = STARGATE->preview_audio_item;
        t_audio_pool_item * f_wav_item = STARGATE->preview_wav_item;
        for(f_i = 0; f_i < sample_count; ++f_i)
        {
            if(f_audio_item->sample_read_heads[0].whole_number >=
                f_wav_item->length)
            {
                STARGATE->is_previewing = 0;
                break;
            }
            else
            {
                v_adsr_run(&f_audio_item->adsrs[0]);
                if(f_wav_item->channels == 1)
                {
                    SGFLT f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[0]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)) *
                        (f_audio_item->adsrs[0].output) *
                        (STARGATE->preview_amp_lin); // *
                        //(f_audio_item->fade_vol);

                    a_buffers[0][f_i] = f_tmp_sample;
                    a_buffers[1][f_i] = f_tmp_sample;
                }
                else if(f_wav_item->channels > 1)
                {
                    a_buffers[0][f_i] = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[0]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)
                    ) * f_audio_item->adsrs[0].output *
                        STARGATE->preview_amp_lin; // *
                        //(f_audio_item->fade_vol);

                    a_buffers[1][f_i] = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[1]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)
                    ) * f_audio_item->adsrs[0].output *
                        STARGATE->preview_amp_lin; // *
                        //(f_audio_item->fade_vol);
                }

                v_ifh_run(&f_audio_item->sample_read_heads[0],
                        f_audio_item->ratio);

                if((f_audio_item->sample_read_heads[0].whole_number)
                    >= (STARGATE->preview_max_sample_count))
                {
                    v_adsr_release(&f_audio_item->adsrs[0]);
                }

                if(f_audio_item->adsrs[0].stage == ADSR_STAGE_OFF)
                {
                    STARGATE->is_previewing = 0;
                    break;
                }
            }
        }
    }

    if(!STARGATE->is_offline_rendering && MASTER_VOL != 1.0f){
        int f_i;
        for(f_i = 0; f_i < sample_count; ++f_i){
            a_buffers[0][f_i] *= MASTER_VOL;
            a_buffers[1][f_i] *= MASTER_VOL;
        }
    }

    STARGATE->current_host->mix();
}
