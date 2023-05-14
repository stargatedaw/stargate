#ifndef WAVE_EDIT_H
#define WAVE_EDIT_H

#include "compiler.h"
#include "osc.h"
#include "stargate.h"

#define WN_CONFIGURE_KEY_LOAD_AB_OPEN "abo"
#define WN_CONFIGURE_KEY_WE_SET "we"
#define WN_CONFIGURE_KEY_WE_EXPORT "wex"
#define WN_CONFIGURE_KEY_WN_PLAYBACK "wnp"
#define WN_CONFIGURE_KEY_PLUGIN_INDEX "pi"
#define WN_CONFIGURE_KEY_AUDIO_INPUTS "ai"
#define WN_CONFIGURE_KEY_PLUGIN_RACK "fx"


typedef struct{
    t_audio_pool_item* ab_wav_item;
    t_audio_item* ab_audio_item;
    t_track* track_pool[1];
    int fx_enabled;
    SGPATHSTR tracks_folder[1024];
    SGPATHSTR project_folder[1024];
}t_wave_edit;

extern t_wave_edit * wave_edit;

void g_wave_edit_get();
void v_set_ab_mode(int a_mode);
void v_set_we_file(t_wave_edit * self, const char * a_file);
void v_set_wave_editor_item(t_wave_edit * self, const char * a_string);
void v_run_wave_editor(
    int sample_count,
    struct SamplePair* output,
    SGFLT * a_input
);
/* Set the plaaback mode
 * @self:   The wave editor to set playback mode for
 * @a_mode: The mode to set it to, one of PLAYBACK_MODE_{OFF,PLAY,REC}
 * @a_lock: 1 to lock the main_lock, 0 to not
 */
void v_we_set_playback_mode(
    t_wave_edit * self,
    int a_mode,
    int a_lock
);
void v_we_export(t_wave_edit * self, const SGPATHSTR* a_file_out);
void v_we_open_tracks();
void v_we_open_project();

void v_we_osc_send(t_osc_send_data * a_buffers);
void v_we_update_audio_inputs();
void v_we_configure(const char* a_key, const char* a_value);
void we_track_reload();
#endif /* WAVE_EDIT_H */
