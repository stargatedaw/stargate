#ifndef UTIL_DAW_CONFIG_H
#define UTIL_DAW_CONFIG_H

#define DN_CONFIGURE_KEY_NOTE_ON "non"
#define DN_CONFIGURE_KEY_NOTE_OFF "noff"
#define DN_CONFIGURE_KEY_CS "cs"
#define DN_CONFIGURE_KEY_OS "os"
#define DN_CONFIGURE_KEY_SI "si"
#define DN_CONFIGURE_KEY_SR "sr"
#define DN_CONFIGURE_KEY_NS "ns"
#define DN_CONFIGURE_KEY_SAVE_ATM "sa"
#define DN_CONFIGURE_KEY_DN_PLAYBACK "enp"
#define DN_CONFIGURE_KEY_LOOP "loop"
#define DN_CONFIGURE_KEY_SOLO "solo"
#define DN_CONFIGURE_KEY_MUTE "mute"
#define DN_CONFIGURE_KEY_SET_OVERDUB_MODE "od"
#define DN_CONFIGURE_KEY_PANIC "panic"
#define DN_CONFIGURE_KEY_PER_FILE_FX "papifx"
#define DN_CONFIGURE_KEY_PER_FILE_FX_CLEAR "papifx_clear"
#define DN_CONFIGURE_KEY_PER_FILE_FX_PASTE "papifx_paste"
//Update a single control for a per-audio-item-fx
#define DN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX "paif"
#define DN_CONFIGURE_KEY_MIDI_DEVICE "md"
#define DN_CONFIGURE_KEY_SET_POS "pos"
#define DN_CONFIGURE_KEY_PLUGIN_INDEX "pi"
#define DN_CONFIGURE_KEY_UPDATE_SEND "ts"
#define DN_CONFIGURE_KEY_AUDIO_INPUTS "ai"
#define DN_CONFIGURE_KEY_METRONOME "met"

void v_daw_configure(const char* a_key, const char* a_value);
#endif
