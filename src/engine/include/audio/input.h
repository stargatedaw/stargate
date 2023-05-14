#ifndef AUDIO_INPUTS_H
#define AUDIO_INPUTS_H

#include <stdio.h>
#include <sndfile.h>

#include "compiler.h"

//1 megabyte interleaved buffer per audio input
#define AUDIO_INPUT_REC_BUFFER_SIZE (1024 * 1024)

typedef struct
{
    int rec;
    int monitor;
    int channels;
    int stereo_ch;
    int output_track;
    int output_mode;  //0=normal,1=sidechain,2=both
    SGFLT vol, vol_linear;
    SF_INFO sf_info;
    SNDFILE * sndfile;
    SGFLT rec_buffers[2][AUDIO_INPUT_REC_BUFFER_SIZE]
        ;
    int buffer_iterator[2];
    int current_buffer;
    int flush_last_buffer_pending;
    int buffer_to_flush;
}t_audio_input;

void g_audio_input_init(t_audio_input *, SGFLT);

void v_audio_input_run(
    int f_index,
    struct SamplePair* output,
    struct SamplePair* sc_output,
    SGFLT* a_input,
    int sample_count,
    int * a_sc_dirty
);
void v_update_audio_inputs(SGPATHSTR* a_project_folder);

void * v_audio_recording_thread(void* a_arg);
void v_stop_record_audio();
void v_prepare_to_record_audio();

#endif /* AUDIO_INPUTS_H */
