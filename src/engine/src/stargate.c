#include <string.h>
#include <time.h>

#include "compiler.h"
#include "globals.h"
#include "ipc.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/lmalloc.h"
#include "plugin.h"
#include "stargate.h"
#include "audio/input.h"
#include "audio/item.h"
#include "audio/sample_graph.h"
#include "audio/util.h"
#include "csv/1d.h"
#include "csv/kvp.h"
#include "csv/split.h"
#include "ds/list.h"
#include "files.h"
#include "hardware/config.h"
#include "unicode.h"

#ifdef NO_MIDI
#else
    #include "hardware/midi.h"
#endif

int SG_OFFLINE_RENDER = 0;

SGFLT MAIN_VOL = 1.0f;
struct SamplePair* pluginOutputBuffers;
t_stargate * STARGATE = NULL;
int ZERO = 0;


void v_ui_send(char * a_path, char * a_msg){
    int msg_len = strlen(a_path) + strlen(a_msg);
    sg_assert(
        msg_len < 60000,
        "Message exceeded 60,000 size limit: %s: %i",
        a_path,
        msg_len
    );
    char msg[60000];
    sg_snprintf(msg, 60000, "%s\n%s", a_path, a_msg);
    ipc_client_send(msg);
}

/* default generic t_sg_host->mix function pointer */
void v_default_mix(){
    int f_i;
    int framesPerBuffer = STARGATE->sample_count;
    float* out = STARGATE->out;

    if(OUTPUT_CH_COUNT > 2){
        int f_i2 = 0;
        memset(
            out,
            0,
            sizeof(float) * framesPerBuffer * OUTPUT_CH_COUNT
        );

        for(f_i = 0; f_i < framesPerBuffer; ++f_i){
            out[f_i2 + MAIN_OUT_L] = (float)pluginOutputBuffers[f_i].left;
            out[f_i2 + MAIN_OUT_R] = (float)pluginOutputBuffers[f_i].right;
            f_i2 += OUTPUT_CH_COUNT;
        }
    } else {
        for(f_i = 0; f_i < framesPerBuffer; ++f_i){
            *out = (float)pluginOutputBuffers[f_i].left;
            ++out;
            *out = (float)pluginOutputBuffers[f_i].right;
            ++out;
        }
    }
}

void g_sample_period_init(t_sample_period *self){
    int f_i;

    self->buffers = NULL;
    self->sc_buffers = NULL;
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
    v_sg_set_tempo(self, 128.0f, NULL);
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
    struct SamplePair* a_buffers,
    struct SamplePair* a_sc_buffers,
    int a_sample_count,
    double a_period_start_beat,
    double a_period_end_beat,
    double a_event1_beat,
    double a_event2_beat,
    long a_current_sample,
    SGFLT* a_input_buffer,
    int a_input_count
){
    self->periods[0].current_sample = a_current_sample;

    if(
        a_event1_beat <= a_period_start_beat
        || (
            a_event1_beat >= a_period_end_beat
            &&
            a_event2_beat >= a_period_end_beat
        )
    ){
        self->count = 1;
        self->periods[0].sample_count = a_sample_count;
        self->periods[0].buffers = a_buffers;

        if(a_sc_buffers){
            self->periods[0].sc_buffers = a_sc_buffers;
        }

        if(a_input_buffer){
            self->periods[0].input_buffer = a_input_buffer;
        }
    } else if(
        a_event1_beat >= a_period_start_beat
        &&
        a_event1_beat < a_period_end_beat
    ){
        if(a_event2_beat >= a_period_end_beat){
            self->count = 1;
            self->periods[0].sample_count = a_sample_count;

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_period_end_beat;

            self->periods[0].buffers = a_buffers;

            if(a_sc_buffers){
                self->periods[0].sc_buffers = a_sc_buffers;
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

            self->periods[0].buffers = a_buffers;

            if(a_sc_buffers){
                self->periods[0].sc_buffers = a_sc_buffers;
            }

            if(a_input_buffer){
                self->periods[0].input_buffer = a_input_buffer;
            }

            self->periods[1].buffers = &a_buffers[f_split];

            if(a_sc_buffers){
                self->periods[1].sc_buffers = &a_sc_buffers[f_split];
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

            self->periods[0].buffers = a_buffers;

            if(a_sc_buffers){
                self->periods[0].sc_buffers = a_sc_buffers;
            }

            if(a_input_buffer){
                self->periods[0].input_buffer = a_input_buffer;
            }

            f_distance = a_event2_beat - a_event1_beat;
            f_split +=
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[1].sample_count = f_split;
            self->periods[1].buffers = &a_buffers[f_split];

            if(a_sc_buffers){
                self->periods[1].sc_buffers = &a_sc_buffers[f_split];
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
            self->periods[2].buffers = &a_buffers[f_split];

            if(a_sc_buffers){
                self->periods[2].sc_buffers = &a_sc_buffers[f_split];
            }

            if(a_input_buffer){
                self->periods[2].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }
        } else {
            sg_abort("v_sample_period_split: else 1");
        }
    } else {
        sg_abort("v_sample_period_split: else 2");
    }
}

void g_stargate_get(
    SGFLT a_sr,
    t_midi_device_list* a_midi_devices
){
    clalloc((void**)&STARGATE, sizeof(t_stargate));
    pthread_mutex_init(&STARGATE->audio_inputs_mutex, NULL);
    STARGATE->audio_pool = g_audio_pool_get(a_sr);
    STARGATE->midi_devices = a_midi_devices;
    STARGATE->current_host = NULL;
    STARGATE->sample_count = 512;
    STARGATE->midi_learn = 0;
    STARGATE->is_offline_rendering = 0;
    pthread_spin_init(&STARGATE->main_lock, 0);

    STARGATE->preview_wav_item = 0;
    STARGATE->preview_audio_item = g_audio_item_get(a_sr);
    STARGATE->preview_start = 0.0f;
    STARGATE->preview_amp_lin = 1.0f;
    STARGATE->is_previewing = 0;
    STARGATE->preview_max_sample_count = ((int)(a_sr)) * 30;
    STARGATE->playback_mode = 0;

    int f_i;

    hpalloc(
        (void**)&STARGATE->audio_inputs,
        sizeof(t_audio_input) * AUDIO_INPUT_TRACK_COUNT
    );

    for(f_i = 0; f_i < AUDIO_INPUT_TRACK_COUNT; ++f_i){
        g_audio_input_init(
            &STARGATE->audio_inputs[f_i],
            a_sr
        );
    }

    t_sg_thread_storage* ts;
    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i){
        ts = &STARGATE->thread_storage[f_i];
        ts->sample_rate = a_sr;
        ts->sr_recip = 1.0 / a_sr;
        ts->five_ms = (int)(a_sr * 0.005);
        ts->five_ms_recip = 1. / (SGFLT)ts->five_ms;
        ts->current_host = SG_HOST_DAW;
    }

    /* Create OSC thread */

    pthread_spin_init(&STARGATE->ui_spinlock, 0);
    STARGATE->osc_queue_index = 0;

    for(f_i = 0; f_i < MAX_PLUGIN_POOL_COUNT; ++f_i){
        STARGATE->plugin_pool[f_i].active = 0;
    }
}

void v_set_control_from_atm(
    t_seq_event *event,
    int a_plugin_uid,
    t_track * f_track
){
    if(!STARGATE->is_offline_rendering){
        sg_snprintf(
            f_track->osc_cursor_message,
            128,
            "%i|%i|%f",
            a_plugin_uid,
            event->port,
            event->value
        );
        v_queue_osc_message("pc", f_track->osc_cursor_message);
    }
}

void v_set_control_from_cc(
    t_seq_event* event,
    t_track* f_track
){
    if(!STARGATE->is_offline_rendering){
        sg_snprintf(
            f_track->osc_cursor_message,
            128,
            "%i|%i|%i|%i",
            f_track->track_num,
            event->param,
            (int)event->value,
            event->channel
        );
        v_queue_osc_message("cc", f_track->osc_cursor_message);
    }
}

void v_set_host(int a_mode){
    int f_i;

    sg_assert(
        a_mode >= 0 && a_mode < SG_HOST_COUNT,
        "v_set_host: a_mode %i out of range 0 to %i",
        a_mode,
        SG_HOST_COUNT
    );

    pthread_spin_lock(&STARGATE->main_lock);

    STARGATE->current_host = &STARGATE->hosts[a_mode];

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i){
        STARGATE->thread_storage[f_i].current_host = a_mode;
    }

#ifndef NO_MIDI

    t_midi_device * f_device;

    if(STARGATE->midi_devices){
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

#if SG_OS == _OS_LINUX
/* Create a clock_t with clock() when beginning some work,
 * and use this function to print the completion time*/
double v_print_benchmark(
    char * a_message,
    struct timespec f_start,
    struct timespec f_finish
){
    double elapsed;
    elapsed = (double)(f_finish.tv_sec - f_start.tv_sec);
    elapsed += (double)(f_finish.tv_nsec - f_start.tv_nsec) / 1000000000.0;

    log_info("Completed %s in %lf seconds", a_message, elapsed);

    return elapsed;
}
#endif

void v_zero_buffer(struct SamplePair* a_buffers, int a_count){
    int i;

    for(i = 0; i < a_count; ++i){
        a_buffers[i].left = 0.0f;
        a_buffers[i].right = 0.0f;
    }
}

void track_free(t_track* track){
    shds_list_free(track->event_list, 1);
    free(track->peak_meter);
    free(track);
}

NO_OPTIMIZATION void v_open_track(
    t_track* a_track,
    SGPATHSTR* a_tracks_folder,
    int a_index
){
    int i, j;
    SGPATHSTR f_file_name[1024];
    int routes[MAX_PLUGIN_COUNT] = {};
    int routed_to[MAX_PLUGIN_COUNT + 1] = {};
    int plugin_active[MAX_PLUGIN_COUNT] = {};
    int audio_inputs[MAX_PLUGIN_COUNT];

    sg_path_snprintf(
        f_file_name,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/%i",
#else
        "%s/%i",
#endif
        a_tracks_folder,
        a_index
    );

    if(i_file_exists(f_file_name)){
#if SG_OS == _OS_WINDOWS
        log_info("%ls exists, opening track", f_file_name);
#else
        log_info("%s exists, opening track", f_file_name);
#endif
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
                v_iterate_2d_char_array(f_2d_array);  // mute
                v_iterate_2d_char_array(f_2d_array);  // solo
                v_iterate_2d_char_array(f_2d_array);
                int f_power = atoi(f_2d_array->current_str);
                int route = 0;
                int audio_input = 1;
                int midi_channel = 0;
                // TODO: Stargate v2: Remove if statements
                if(!f_2d_array->eol){
                    v_iterate_2d_char_array(f_2d_array);
                    route = atoi(f_2d_array->current_str);
                }
                if(!f_2d_array->eol){
                    v_iterate_2d_char_array(f_2d_array);
                    audio_input = atoi(f_2d_array->current_str);
                }
                if(!f_2d_array->eol){
                    v_iterate_2d_char_array(f_2d_array);
                    midi_channel = atoi(f_2d_array->current_str);
                }
                if(f_index < MAX_PLUGIN_COUNT){
                    route += + 1 + f_index;
                    sg_assert(
                        route >= 0 && route <= MAX_PLUGIN_COUNT,
                        "Route %i on plugin %i is out of range",
                        route,
                        f_index
                    );
                    routes[f_index] = route;
                    if(f_plugin_index && f_power){
                        plugin_active[f_index] = 1;
                    }
                    audio_inputs[f_index] = audio_input;
                }

                v_set_plugin_index(
                    a_track,
                    f_index,
                    f_plugin_index,
                    f_plugin_uid,
                    f_power,
                    midi_channel,
                    0
                );
            } else {
                sg_abort(
                    "v_open_track: invalid line identifier '%s'",
                    f_2d_array->current_str
                );
            }
        }
        // Fix the routes to empty plugin slots, determine which
        // plugins are routed to
        for(i = 0; i < MAX_PLUGIN_COUNT; ++i){
            int found = 0;
            if(!plugin_active[i]){
                continue;
            }
            for(j = routes[i]; j < MAX_PLUGIN_COUNT; ++j){
                if(plugin_active[j]){
                    found = 1;
                    routes[i] = j;
                    ++routed_to[j];
                    break;
                }
            }
            if(!found){
                routes[i] = MAX_PLUGIN_COUNT;  // master output of the track
                ++routed_to[MAX_PLUGIN_COUNT];
            }
        }
        // find the first active plugin
        int first_active_plugin = MAX_PLUGIN_COUNT;
        for(i = 0; i < MAX_PLUGIN_COUNT; ++i){
            if(plugin_active[i]){
                first_active_plugin = i;
                break;
            }
        }
        ++i;
        // Determine if there are multiple routing chains within this track
        int multiple_routes = 0;
        for(; i < MAX_PLUGIN_COUNT; ++i){
            if(plugin_active[i] && !routed_to[i]){
                multiple_routes = 1;
                break;
            }
        }


        struct PluginPlanStep* step;
        a_track->plugin_plan.step_count = 0;
        a_track->plugin_plan.zero_count = 0;
        if(multiple_routes){
            // Find buffers to be copied to
            a_track->plugin_plan.copy_count = 0;
            a_track->plugin_plan.input = a_track->input_buffer;
            for(i = first_active_plugin; i < MAX_PLUGIN_COUNT; ++i){
                if(plugin_active[i] && !routed_to[i] && audio_inputs[i]){
                    j = a_track->plugin_plan.copy_count;
                    a_track->plugin_plan.copies[j] = i;
                    ++a_track->plugin_plan.copy_count;
                }
            }

            // Find buffers to be zeroed
            for(i = 1; i < MAX_PLUGIN_COUNT + 1; ++i){
                if(
                    routed_to[i] > 1
                    || (
                        i < MAX_PLUGIN_COUNT
                        &&
                        plugin_active[i]
                        &&
                        !audio_inputs[i]
                    )
                ){
                    j = a_track->plugin_plan.zero_count;
                    a_track->plugin_plan.zeroes[j] = i;
                    ++a_track->plugin_plan.zero_count;
                }
            }
            // Set all to their respective plugin buffer
            // TODO: Optimize to consolidate buffers to individual chains
            a_track->plugin_plan.output = a_track->audio[MAX_PLUGIN_COUNT];
            for(i = 0; i < MAX_PLUGIN_COUNT; ++i){
                if(!plugin_active[i]){
                    continue;
                }
                j = a_track->plugin_plan.step_count;
                step = &a_track->plugin_plan.steps[j];
                step->plugin = a_track->plugins[i];
                step->input = a_track->audio[i];
                step->output = a_track->audio[routes[i]];
                if(routed_to[routes[i]] > 1){
                    step->run_mode = RunModeMixing;
                } else {
                    step->run_mode = RunModeReplacing;
                }
                ++a_track->plugin_plan.step_count;
            }
        } else {
            a_track->plugin_plan.copy_count = 0;
            // Set all to the first buffer if no routes exist.  Equivalent to
            // the previous behavior
            a_track->plugin_plan.input = a_track->audio[0];
            a_track->plugin_plan.output = a_track->audio[0];
            for(i = 0; i < MAX_PLUGIN_COUNT; ++i){
                if(!plugin_active[i]){
                    continue;
                }
                j = a_track->plugin_plan.step_count;
                a_track->plugin_plan.steps[j].plugin = a_track->plugins[i];
                a_track->plugin_plan.steps[j].input = a_track->audio[0];
                a_track->plugin_plan.steps[j].output = a_track->audio[0];
                a_track->plugin_plan.steps[j].run_mode = RunModeReplacing;
                ++a_track->plugin_plan.step_count;
            }
        }
        // Set the final step to the track output if not already there
        /*
        if(a_track->plugin_plan.step_count){
            a_track->plugin_plan.steps[
                a_track->plugin_plan.step_count - 1
            ].output = a_track->plugin_plan.output;
        }
        */

        g_free_2d_char_array(f_2d_array);
    } else {
#if SG_OS == _OS_WINDOWS
        log_info("%ls does not exist, resetting track", f_file_name);
#else
        log_info("%s does not exist, resetting track", f_file_name);
#endif
        int f_i;
        for(f_i = 0; f_i < MAX_PLUGIN_COUNT; ++f_i){
            v_set_plugin_index(a_track, f_i, 0, -1, 0, 0, 0);
        }

        a_track->plugin_plan.copy_count = 0;
        a_track->plugin_plan.step_count = 0;
        a_track->plugin_plan.zero_count = 0;
        a_track->plugin_plan.input = a_track->audio[0];
        a_track->plugin_plan.output = a_track->audio[0];
    }
}

t_track * g_track_get(int a_track_num, SGFLT a_sr){
    int f_i = 0;
    int i, j;

    t_track * f_result;
    clalloc((void**)&f_result, sizeof(t_track));

    f_result->track_num = a_track_num;
    f_result->channels = 2;
    f_result->extern_midi = 0;
    f_result->extern_midi_count = &ZERO;
    f_result->midi_device = 0;
    f_result->sc_buffers_dirty = 0;
    f_result->event_list = shds_list_new(MAX_EVENT_BUFFER_SIZE, NULL);

    f_result->plugin_plan.copy_count = 0;
    f_result->plugin_plan.step_count = 0;

    pthread_spin_init(&f_result->lock, 0);

    v_zero_buffer(f_result->input_buffer, FRAMES_PER_BUFFER);
    for(f_i = 0; f_i < MAX_PLUGIN_COUNT + 1; ++f_i){
        v_zero_buffer(f_result->audio[f_i], FRAMES_PER_BUFFER);
    }
    v_zero_buffer(f_result->sc_buffers, FRAMES_PER_BUFFER);

    f_result->mute = 0;
    f_result->solo = 0;

    f_result->bus_counter = 0;

    for(f_i = 0; f_i < MAX_EVENT_BUFFER_SIZE; ++f_i){
        v_ev_clear(&f_result->event_buffer[f_i]);
    }

    for(f_i = 0; f_i < MAX_PLUGIN_TOTAL_COUNT; ++f_i){
        f_result->plugins[f_i] = NULL;
    }

    for(i = 0; i < MIDI_CHANNEL_COUNT; ++i){
        for(j = 0; j < MIDI_NOTE_COUNT; ++j){
            f_result->note_offs[i][j] = -1;
        }
    }

    f_result->period_event_index = 0;

    f_result->peak_meter = g_pkm_get();

    g_rmp_init(&f_result->fade_env, a_sr);
    v_rmp_set_time(&f_result->fade_env, 0.03f);
    f_result->fade_state = 0;

    f_result->osc_cursor_message[0] = '\0';

    f_result->status = STATUS_NOT_PROCESSED;

    return f_result;
}

void v_set_preview_file(const char* a_file){
#if SG_OS == _OS_WINDOWS
    SGPATHSTR path[2048];
    utf8_to_utf16((const utf8_t*)a_file, strlen(a_file), path, 2048);
    t_audio_pool_item * f_result = g_audio_pool_item_get(
        0,
        path,
        STARGATE->thread_storage[0].sample_rate
    );
#else
    t_audio_pool_item * f_result = g_audio_pool_item_get(
        0,
        a_file,
        STARGATE->thread_storage[0].sample_rate
    );
#endif

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
            log_error(
                "i_audio_pool_item_load(f_result) failed in "
                "v_set_preview_file"
            );
        }
    } else {
        STARGATE->is_previewing = 0;
        log_error(
            "g_audio_pool_item_get returned zero. could not load "
            "preview item."
        );
    }
}

void stop_preview(){
    if(STARGATE->is_previewing){
        pthread_spin_lock(&STARGATE->main_lock);
        v_adsr_release(&STARGATE->preview_audio_item->adsrs[0]);
        pthread_spin_unlock(&STARGATE->main_lock);
    }
}

double f_bpm_to_seconds_per_beat(double a_tempo){
    return (60.0f / a_tempo);
}

double f_samples_to_beat_count(
    int a_sample_count,
    double a_tempo,
    SGFLT sr_recip
){
    if(a_sample_count <= 0){
        return 0.0;
    }
    double f_seconds_per_beat = f_bpm_to_seconds_per_beat(a_tempo);
    double f_seconds = (double)(a_sample_count) * sr_recip;
    return f_seconds / f_seconds_per_beat;
}

double f_samples_to_beat_count_sr(
    int a_sample_count,
    double a_tempo,
    SGFLT sr
){
    if(a_sample_count <= 0){
        return 0.0;
    }
    double f_seconds_per_beat = f_bpm_to_seconds_per_beat(a_tempo);
    double f_seconds = (double)(a_sample_count) / sr;
    return f_seconds / f_seconds_per_beat;
}

int i_beat_count_to_samples(
    double a_beat_count,
    SGFLT a_tempo,
    SGFLT a_sr
){
    if(a_beat_count <= 0.0){
        return 0;
    }
    double f_seconds = f_bpm_to_seconds_per_beat(a_tempo) * a_beat_count;
    return (int)(f_seconds * a_sr);
}


void v_buffer_mix(
    int a_count,
    struct SamplePair* a_buffer_src,
    struct SamplePair* a_buffer_dest
){
    int i;

    for(i = 0; i < a_count; ++i){
        a_buffer_dest[i].left += a_buffer_src[i].left;
        a_buffer_dest[i].right += a_buffer_src[i].right;
    }
}

NO_OPTIMIZATION void v_wait_for_threads(){
    int i;
    pthread_spinlock_t* lock;

    for(i = 1; i < (STARGATE->worker_thread_count); ++i){
        lock = &STARGATE->worker_threads[i].lock;
        pthread_spin_lock(lock);
        pthread_spin_unlock(lock);
    }
}

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
){
    f_result->type = EVENT_NOTEON;
    f_result->length = a_length;
    f_result->note = a_note;
    f_result->start = a_start;
    f_result->velocity = a_vel;
    f_result->pan = pan;
    f_result->attack = attack;
    f_result->decay = decay;
    f_result->sustain = sustain;
    f_result->release = release;
    f_result->channel = channel;
    f_result->pitch_fine = pitch_fine;
}

void g_cc_init(
    t_seq_event * f_result,
    int a_cc_num,
    SGFLT a_cc_val,
    SGFLT a_start,
    int channel
){
    f_result->type = EVENT_CONTROLLER;
    f_result->param = a_cc_num;
    f_result->value = a_cc_val;
    f_result->start = a_start;
    f_result->channel = channel;
}

t_seq_event * g_cc_get(
    int a_cc_num,
    SGFLT a_cc_val,
    SGFLT a_start,
    int channel
){
    t_seq_event * f_result = (t_seq_event*)malloc(sizeof(t_seq_event));
    g_cc_init(f_result, a_cc_num, a_cc_val, a_start, channel);
    return f_result;
}

void g_pitchbend_init(
    t_seq_event * f_result,
    SGFLT a_start,
    SGFLT a_value,
    int channel
){
    f_result->type = EVENT_PITCHBEND;
    f_result->start = a_start;
    f_result->value = a_value;
    f_result->channel = channel;
}

t_seq_event * g_pitchbend_get(SGFLT a_start, SGFLT a_value, int channel){
    t_seq_event * f_result = (t_seq_event*)malloc(sizeof(t_seq_event));
    g_pitchbend_init(f_result, a_start, a_value, channel);
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
        sg_assert(
            (int)self->atm_tick_count < ATM_TICK_BUFFER_SIZE,
            "v_sample_period_set_atm_events: atm tick count %i out of "
            "range 0 to %i",
            self->atm_tick_count,
            ATM_TICK_BUFFER_SIZE
        );

        pos = (a_event_list->atm_pos - current_sample);
        self->atm_ticks[self->atm_tick_count].sample = (int)(pos);

        self->atm_ticks[self->atm_tick_count].beat =
            self->start_beat +
            f_samples_to_beat_count(
                self->atm_ticks[self->atm_tick_count].sample + 1, // round up
                a_event_list->tempo,
                STARGATE->thread_storage[0].sr_recip
            );
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
    struct SamplePair* a_buffers,
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
    f_period->buffers = a_buffers;
    f_period->input_buffer = a_input_buffers;
}

void v_set_sample_period(
    t_sample_period * self,
    SGFLT a_playback_inc,
    struct SamplePair* a_buffers,
    struct SamplePair* a_sc_buffers,
    SGFLT * a_input_buffers,
    int a_sample_count,
    long a_current_sample
){
    self->period_inc_beats = a_playback_inc * ((SGFLT)(a_sample_count));

    self->current_sample = a_current_sample;
    self->sample_count = a_sample_count;

    if(a_sc_buffers){
        self->sc_buffers = a_sc_buffers;
    } else {
        self->sc_buffers = NULL;
    }

    self->buffers = a_buffers;
    self->input_buffer = a_input_buffers;
}

void v_sg_set_tempo(
    t_sg_seq_event_list* self,
    SGFLT a_tempo,
    t_sg_seq_event* event
){
    STARGATE->current_tsig = event;
    SGFLT f_sample_rate = STARGATE->thread_storage[0].sample_rate;
    self->tempo = a_tempo;
    self->playback_inc = (1.0f / f_sample_rate) / (60.0f / a_tempo);
    self->samples_per_beat = (f_sample_rate) / (a_tempo / 60.0f);
    self->atm_clock_samples =
        self->samples_per_beat * SG_AUTOMATION_RESOLUTION;
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
             v_sg_set_tempo(self, f_ev->tempo, f_ev);
             f_found_tempo = 1;
         }
    }

    sg_assert(f_found_tempo, "v_sg_set_playback_pos: did not find tempo");
}


void v_sg_seq_event_list_set(
    t_sg_seq_event_list * self,
    t_sg_seq_event_result* a_result,
    struct SamplePair* a_buffers,
    SGFLT* a_input_buffers,
    int a_input_count,
    int a_sample_count,
    long a_current_sample,
    int a_loop_mode
){
    int f_i;
    for(f_i = 0; f_i < 2; ++f_i){
        a_result->sample_periods[f_i].is_looping = 0;
        a_result->sample_periods[f_i].tempo = self->tempo;
    }

    if(self->pos >= self->count){
        v_sg_seq_event_result_set_default(
            a_result,
            self,
            a_buffers,
            a_input_buffers,
            a_input_count,
            a_sample_count,
            a_current_sample
        );
    } else {
        a_result->count = 0;

        double f_loop_start = -1.0f;

        t_sg_seq_event * f_ev = NULL;
        //The scratchpad sample period for iterating
        t_sample_period * f_tmp_period = NULL;
        //temp variable for the outputted sample period
        t_sg_seq_event_period * f_period = NULL;

        v_set_sample_period(
            &self->period,
            self->playback_inc,
            a_buffers,
            NULL,
            a_input_buffers,
            a_sample_count,
            a_current_sample
        );

        v_sg_set_time_params(&self->period);

        while(1){
            if(self->pos >= self->count){
                break;
            } else if(
                self->events[self->pos].beat >= self->period.start_beat
                &&
                self->events[self->pos].beat < self->period.end_beat
            ){
                f_ev = &self->events[self->pos];
                ++self->pos;
                //The period that is returned to the main loop
                if(f_ev->type == SEQ_EVENT_LOOP && a_loop_mode){
                    if(f_ev->beat > self->period.start_beat){
                        a_result->count = 2;
                    }
                    f_loop_start = f_ev->start_beat;
                    f_period = &a_result->sample_periods[a_result->count - 1];
                    f_period->is_looping = 1;
                } else if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE){
                    if(f_ev->beat > self->period.start_beat){
                        a_result->count = 2;
                        f_period = &a_result->sample_periods[0];
                        f_period->tempo = self->tempo;
                        f_period->playback_inc = self->playback_inc;
                        f_period->samples_per_beat = self->samples_per_beat;
                    }

                    v_sg_set_tempo(self, f_ev->tempo, f_ev);
                    f_period = &a_result->sample_periods[a_result->count - 1];
                    f_period->tempo = self->tempo;
                    f_period->playback_inc = self->playback_inc;
                    f_period->samples_per_beat = self->samples_per_beat;
                }
            } else if(self->events[self->pos].beat < self->period.start_beat){
                f_ev = &self->events[self->pos];
                ++self->pos;
                if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE){
                    v_sg_set_tempo(self, f_ev->tempo, f_ev);
                    f_period = &a_result->sample_periods[0];
                    f_period->tempo = self->tempo;
                    f_period->playback_inc = self->playback_inc;
                    f_period->samples_per_beat = self->samples_per_beat;
                }
            } else {
                break;
            }
        }

        if(a_result->count == 0){
            a_result->count = 1;

            f_period = &a_result->sample_periods[0];

            v_set_sample_period(
                &f_period->period,
                self->playback_inc,
                a_buffers,
                NULL,
                a_input_buffers,
                a_sample_count,
                a_current_sample
            );

            f_period->tempo = self->tempo;
            f_period->playback_inc = self->playback_inc;
            f_period->samples_per_beat = self->samples_per_beat;

            f_period->period.start_beat = self->period.start_beat;
            f_period->period.end_beat = self->period.end_beat;
        } else if(a_result->count == 1){
            f_tmp_period = &self->period;
            f_period = &a_result->sample_periods[0];

            v_set_sample_period(
                &f_period->period,
                self->playback_inc,
                f_tmp_period->buffers,
                NULL,
                f_tmp_period->input_buffer,
                f_tmp_period->sample_count,
                f_tmp_period->current_sample
            );

            f_period->period.period_inc_beats = ((f_period->playback_inc) *
                ((SGFLT)(f_tmp_period->sample_count)));

            if(f_loop_start >= 0.0){
                self->pos = 0;
                f_period->period.start_beat = f_loop_start;
            } else {
                f_period->period.start_beat = f_tmp_period->start_beat;
            }

            f_period->period.end_beat = f_period->period.start_beat +
                f_period->period.period_inc_beats;
            self->period.end_beat = f_period->period.end_beat;
        } else if(a_result->count == 2){
            f_period = &a_result->sample_periods[0];

            v_sample_period_split(
                &a_result->splitter,
                self->period.buffers,
                NULL,
                self->period.sample_count,
                self->period.start_beat,
                self->period.end_beat,
                f_ev->beat,
                f_ev->beat,
                self->period.current_sample,
                self->period.input_buffer,
                a_input_count
            );

            f_tmp_period = &a_result->splitter.periods[0];

            v_set_sample_period(
                &f_period->period,
                self->playback_inc,
                f_tmp_period->buffers,
                NULL,
                f_tmp_period->input_buffer,
                f_tmp_period->sample_count,
                f_tmp_period->current_sample
            );

            f_period->period.period_inc_beats = ((f_period->playback_inc) *
                ((SGFLT)(f_tmp_period->sample_count)));

            f_period->period.start_beat = f_tmp_period->start_beat;

            f_period->period.end_beat = f_tmp_period->end_beat;

            if(a_result->splitter.count == 2){
                f_period = &a_result->sample_periods[1];
                f_tmp_period = &a_result->splitter.periods[1];

                v_set_sample_period(
                    &f_period->period,
                    self->playback_inc,
                    f_tmp_period->buffers,
                    NULL,
                    f_tmp_period->input_buffer,
                    f_tmp_period->sample_count,
                    f_tmp_period->current_sample
                );

                if(f_loop_start >= 0.0){
                    self->pos = 0;
                    f_period->period.start_beat = f_loop_start;
                } else {
                    f_period->period.start_beat = f_tmp_period->start_beat;
                }

                f_period->period.period_inc_beats = ((f_period->playback_inc) *
                    ((SGFLT)(f_tmp_period->sample_count)));
                f_period->period.end_beat = f_period->period.start_beat +
                    f_period->period.period_inc_beats;
            } else if(a_result->splitter.count == 1){
                // TODO:  Debug how and why this happens
            } else {
                sg_abort("v_sg_seq_event_list_set: else 1");
            }

            self->period.end_beat = f_period->period.end_beat;
        } else {
            sg_abort("v_sg_seq_event_list_set: else 2");
        }
    }
}


void v_sg_configure(const char* a_key, const char* a_value){
    char buf[1024];
#if SG_OS == _OS_WINDOWS
    SGPATHSTR path_buf[2048];
#endif
    log_info("v_sg_configure:  key: \"%s\", value: \"%s\"", a_key, a_value);
    int has_error = 0;

    if(!strcmp(a_key, SG_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL)){
        a_value = str_split(a_value, buf, '|');
        int f_plugin_uid = atoi(buf);
        a_value = str_split(a_value, buf, '|');
        int f_port = atoi(buf);
        a_value = str_split(a_value, buf, '|');
        SGFLT f_value = atof(buf);

        t_plugin * f_instance;
        pthread_spin_lock(&STARGATE->main_lock);

        f_instance = &STARGATE->plugin_pool[f_plugin_uid];

        if(f_instance){
            f_instance->descriptor->set_port_value(
                f_instance->plugin_handle,
                f_port,
                f_value
            );
        } else {
            has_error = 1;
        }
        pthread_spin_unlock(&STARGATE->main_lock);
        if(has_error){
            log_error(
                "pc: no valid plugin instance: %i",
                f_plugin_uid
            );
        }
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
            log_error(
                "No valid plugin instance %i",
                f_plugin_uid
            );
        }

        g_free_1d_char_array(f_val_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_MAIN_VOL)){
        MAIN_VOL = atof(a_value);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_AUDIO_IN_VOL)){
        a_value = str_split(a_value, buf, '|');
        int f_index = atoi(buf);
        a_value = str_split(a_value, buf, '|');
        SGFLT f_vol = atof(buf);
        SGFLT f_vol_linear = f_db_to_linear_fast(f_vol);
        t_audio_input * f_input = &STARGATE->audio_inputs[f_index];
        f_input->vol = f_vol;
        f_input->vol_linear = f_vol_linear;
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_KILL_ENGINE)){
        log_warn("v_sg_configure: SG_CONFIGURE_KEY_KILL_ENGINE");
        pthread_spin_lock(&STARGATE->main_lock);
        exit(0);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_EXIT)){
        pthread_mutex_lock(&EXIT_MUTEX);
        exiting = 1;
        pthread_mutex_unlock(&EXIT_MUTEX);
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
#if SG_OS == _OS_WINDOWS
	utf8_to_utf16(
            (const utf8_t*)val_arr->array[2],
            strlen(val_arr->array[2]),
            path_buf,
            2048
        );
        t_audio_pool_item * result = v_audio_pool_add_item(
            STARGATE->audio_pool,
            uid,
            volume,
	    path_buf,
            STARGATE->audio_folder
        );
#else
        t_audio_pool_item * result = v_audio_pool_add_item(
            STARGATE->audio_pool,
            uid,
            volume,
            val_arr->array[2],
            STARGATE->audio_folder
        );
#endif
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
        stop_preview();
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_RATE_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(SMALL_STRING);
        char f_tmp_char[SMALL_STRING];
        sg_snprintf(f_tmp_char, SMALL_STRING, "%s", a_value);
        f_arr->array = f_tmp_char;
        SGPATHSTR * f_in_file = (SGPATHSTR*)malloc(sizeof(SGPATHSTR) * TINY_STRING);
        SGPATHSTR * f_out_file = (SGPATHSTR*)malloc(sizeof(SGPATHSTR) * TINY_STRING);
        v_iterate_2d_char_array(f_arr);
#if SG_OS == _OS_WINDOWS
	utf8_to_utf16(
            (const utf8_t*)f_arr->current_str,
            strlen(f_arr->current_str),
            f_in_file,
            TINY_STRING
        );
        v_iterate_2d_char_array(f_arr);
	utf8_to_utf16(
            (const utf8_t*)f_arr->current_str,
            strlen(f_arr->current_str),
            f_out_file,
            TINY_STRING
        );
#else
        strcpy(f_in_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
#endif
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
        sg_assert(
            (int)(f_val == 0 || f_val == 1),
            "SG_CONFIGURE_KEY_ENGINE: f_val %i out of range 0 to 1, %s",
            f_val,
            (char*)a_value
        );
        pthread_spin_lock(&STARGATE->main_lock);
        STARGATE->is_offline_rendering = f_val;
        pthread_spin_unlock(&STARGATE->main_lock);
    }
    else if(!strcmp(a_key, SG_CONFIGURE_KEY_PITCH_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(SMALL_STRING);
        char f_tmp_char[SMALL_STRING];
        sg_snprintf(f_tmp_char, SMALL_STRING, "%s", a_value);
        f_arr->array = f_tmp_char;
        SGPATHSTR * f_in_file = (SGPATHSTR*)malloc(sizeof(SGPATHSTR) * TINY_STRING);
        SGPATHSTR * f_out_file = (SGPATHSTR*)malloc(sizeof(SGPATHSTR) * TINY_STRING);
        v_iterate_2d_char_array(f_arr);
#if SG_OS == _OS_WINDOWS
        utf8_to_utf16(
            (const utf8_t*)f_arr->current_str,
            strlen(f_arr->current_str),
            f_in_file,
            TINY_STRING
        );
        v_iterate_2d_char_array(f_arr);
        utf8_to_utf16(
            (const utf8_t*)f_arr->current_str,
            strlen(f_arr->current_str),
            f_out_file,
            TINY_STRING
        );
#else
        strcpy(f_in_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
#endif
        v_iterate_2d_char_array(f_arr);
        SGFLT f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        SGFLT f_end = atof(f_arr->current_str);

        v_pitch_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_CLEAN_AUDIO_POOL)){
        t_2d_char_array * f_arr = g_get_2d_array(LARGE_STRING);
        int f_uid;
        strcpy(f_arr->array, a_value);

        while(!f_arr->eof){
            v_iterate_2d_char_array(f_arr);
            f_uid = atoi(f_arr->current_str);
            v_audio_pool_remove_item(STARGATE->audio_pool, f_uid);
        }

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    } else if(!strcmp(a_key, SG_CONFIGURE_KEY_AUDIO_POOL_ITEM_RELOAD)){
        int f_uid = atoi(a_value);
        t_audio_pool_item * f_old = g_audio_pool_get_item_by_uid(
            STARGATE->audio_pool,
            f_uid
        );
        t_audio_pool_item f_new = {
            .uid = f_uid,
            .host_sr = STARGATE->audio_pool->sample_rate,
        };
#if SG_OS == _OS_WINDOWS
        sg_path_snprintf(f_new.path, 2040, L"%ls", f_old->path);
#else
        sg_path_snprintf(f_new.path, 2040, "%s", f_old->path);
#endif

        i_audio_pool_item_load(&f_new, 0);

        SGFLT * f_old_samples[2];
        f_old_samples[0] = f_old->samples[0];
        f_old_samples[1] = f_old->samples[1];

        pthread_spin_lock(&STARGATE->main_lock);

        // memcpy(f_old, &f_new, sizeof(t_audio_pool_item));
        f_old->channels = f_new.channels;
        f_old->length = f_new.length;
        f_old->ratio_orig = f_new.ratio_orig;
        f_old->sample_rate = f_new.sample_rate;
        f_old->samples[0] = f_new.samples[0];
        f_old->samples[1] = f_new.samples[1];

        pthread_spin_unlock(&STARGATE->main_lock);

        // TODO: This will crash if using hugepages, find a way to free the
        // memory only if hugepages are not being used, maybe add as a field
        // to the audio pool item
        if(f_old_samples[0]){
            //free(f_old_samples[0]);
        }
        if(f_old_samples[1]){
            //free(f_old_samples[1]);
        }
    } else {
        log_info(
            "Unknown configure message key: %s, value %s",
            a_key,
            a_value
        );
    }

}

/*Function for passing to plugins that re-use the wav pool*/
t_audio_pool_item* g_audio_pool_item_get_plugin(int a_uid){
    return g_audio_pool_get_item_by_uid(STARGATE->audio_pool, a_uid);
}

void plugin_init(
    t_plugin* self,
    int a_plugin_index,
    int a_plugin_uid
){
    int i;
    struct SamplePair buffer[512] = {};
    struct SamplePair sc_buffer[512] = {};
    int sample_rate = (int)STARGATE->thread_storage[0].sample_rate;
    struct ShdsList midi_list, atm_list;
    shds_list_init(&midi_list, 0, NULL);
    shds_list_init(&atm_list, 0, NULL);

    if(!self->active){
        log_info("Initializing plugin");
        plugin_activate(
            self,
            sample_rate,
            a_plugin_index,
            g_audio_pool_item_get_plugin,
            a_plugin_uid,
            v_queue_osc_message
        );
        log_info("Finished initializing plugin");

        SGPATHSTR f_file_name[1024];
        sg_path_snprintf(
            f_file_name,
            1000,
#if SG_OS == _OS_WINDOWS
            L"%ls%i",
#else
            "%s%i",
#endif
            STARGATE->plugins_folder,
            a_plugin_uid
        );

        if(i_file_exists(f_file_name)){
            log_info("Loading plugin");
            self->descriptor->load(
                self->plugin_handle,
                self->descriptor,
                f_file_name
            );
        } else {
#if SG_OS == _OS_WINDOWS
            log_warn("No plugin state found at %ls", f_file_name);
#else
            log_warn("No plugin state found at %s", f_file_name);
#endif
        }

        // Warm up control smoothers and anything else by running for
        // one second, avoids strangeness at the beginning of playback
        // or render
        for(i = 0; i < (sample_rate / 512); ++i){
            self->descriptor->run(
                self->plugin_handle,
                RunModeReplacing,
                512,
                buffer,
                sc_buffer,
                buffer,
                &midi_list,
                &atm_list,
                NULL,
                0
            );
        }
    }
}

NO_OPTIMIZATION void v_set_plugin_index(
    t_track * f_track,
    int a_index,
    int a_plugin_index,
    int a_plugin_uid,
    int a_power,
    int midi_channel,
    int a_lock
){
    t_plugin * f_plugin = NULL;

    if(a_plugin_index){
        log_info("Plugin %i index set to %i", a_index, a_plugin_index);
        f_plugin = &STARGATE->plugin_pool[a_plugin_uid];
        plugin_init(
            f_plugin,
            a_plugin_index,
            a_plugin_uid
        );
    }

    if(a_lock){
        pthread_spin_lock(&STARGATE->main_lock);
    }

    if(f_plugin){
        f_plugin->power = a_power;
        f_plugin->midi_channel = midi_channel;
    }

    f_track->plugins[a_index] = f_plugin;

    if(a_lock){
        pthread_spin_unlock(&STARGATE->main_lock);
    }
}

void v_run(
    struct SamplePair* buffers,
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
            buffers[f_i].left = 0.0f;
            buffers[f_i].right = 0.0f;
        }
    }

    pthread_spin_unlock(&STARGATE->main_lock);
}

void preview_sample(
    int sample_count,
    struct SamplePair* a_buffers
){
    int f_i;
    t_audio_item * f_audio_item = STARGATE->preview_audio_item;
    t_audio_pool_item * f_wav_item = STARGATE->preview_wav_item;
    for(f_i = 0; f_i < sample_count; ++f_i){
        if(
            f_audio_item->sample_read_heads[0].whole_number
            >=
            f_wav_item->length
        ){
            STARGATE->is_previewing = 0;
            break;
        } else {
            v_adsr_run(&f_audio_item->adsrs[0]);
            if(f_wav_item->channels == 1){
                SGFLT f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                    (f_wav_item->samples[0]),
                    (f_audio_item->sample_read_heads[0].whole_number),
                    (f_audio_item->sample_read_heads[0].fraction)
                ) * f_audio_item->adsrs[0].output *
                    STARGATE->preview_amp_lin; // *
                    //(f_audio_item->fade_vol);

                a_buffers[f_i].left = f_tmp_sample;
                a_buffers[f_i].right = f_tmp_sample;
            } else if(f_wav_item->channels > 1){
                a_buffers[f_i].left = f_cubic_interpolate_ptr_ifh(
                    (f_wav_item->samples[0]),
                    (f_audio_item->sample_read_heads[0].whole_number),
                    (f_audio_item->sample_read_heads[0].fraction)
                ) * f_audio_item->adsrs[0].output *
                    STARGATE->preview_amp_lin; // *
                    //(f_audio_item->fade_vol);

                a_buffers[f_i].right = f_cubic_interpolate_ptr_ifh(
                    (f_wav_item->samples[1]),
                    (f_audio_item->sample_read_heads[0].whole_number),
                    (f_audio_item->sample_read_heads[0].fraction)
                ) * f_audio_item->adsrs[0].output *
                    STARGATE->preview_amp_lin; // *
                    //(f_audio_item->fade_vol);
            }

            v_ifh_run(
                &f_audio_item->sample_read_heads[0],
                f_audio_item->ratio
            );

            if(
                f_audio_item->sample_read_heads[0].whole_number
                >=
                STARGATE->preview_max_sample_count
            ){
                v_adsr_release(&f_audio_item->adsrs[0]);
            }

            if(f_audio_item->adsrs[0].stage == ADSR_STAGE_OFF){
                STARGATE->is_previewing = 0;
                break;
            }
        }
    }
}

void v_run_main_loop(
    int sample_count,
    struct SamplePair* a_buffers,
    PluginData* a_input_buffers
){
    STARGATE->current_host->run(sample_count, a_buffers, a_input_buffers);

    if(unlikely(STARGATE->is_previewing)){
        preview_sample(sample_count, a_buffers);
    }

    if(!STARGATE->is_offline_rendering && MAIN_VOL != 1.0f){
        int f_i;
        for(f_i = 0; f_i < sample_count; ++f_i){
            a_buffers[f_i].left *= MAIN_VOL;
            a_buffers[f_i].right *= MAIN_VOL;
        }
    }

    STARGATE->current_host->mix();
}
