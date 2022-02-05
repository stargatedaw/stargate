/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef VOICE_H
#define VOICE_H

#define VOICES_MAX_MIDI_NOTE_NUMBER 128
#define MIDI_NOTES  128
#define MAX_VOICES 32

#define POLY_MODE_RETRIG 0
#define POLY_MODE_FREE 1
#define POLY_MODE_MONO 2
#define POLY_MODE_MONO2 3

typedef enum {
    note_state_off = 0,
    note_state_running,
    /*Synths should iterate voices looking for any voice note_state
     * that is set to releasing, and  trigger a release event in
     * it's amplitude envelope*/
    note_state_releasing,
    note_state_killed
} note_state;

typedef struct {
    int voice_number;
    int note;
    note_state n_state;
    long on;
    long off;
} t_voc_single_voice;

typedef struct {
    t_voc_single_voice voices[MAX_VOICES];
    int count;
    int thresh;  //when to start aggressively killing voices
    int poly_mode;
} t_voc_voices;

void g_voc_single_init(t_voc_single_voice * f_result, int a_voice_number);

/* int i_pick_voice(
 * t_voc_voices *data,
 * int a_current_note)
 *
 */
int i_pick_voice(
    t_voc_voices* data,
    int a_current_note,
    long a_current_sample,
    long a_tick
);

/* void v_voc_note_off(t_voc_voices * a_voc, int a_note,
 * long a_current_sample, long a_tick)
 */
void v_voc_note_off(
    t_voc_voices * a_voc,
    int a_note,
    long a_current_sample,
    long a_tick
);
void g_voc_voices_init(
    t_voc_voices* voices,
    int a_count,
    int a_thresh
);

#endif /* VOICE_H */

