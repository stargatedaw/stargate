#ifndef UTIL_AUDIO_ITEM
#define UTIL_AUDIO_ITEM

#include "audiodsp/lib/interpolate-sinc.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/adsr.h"
#include "audio/paifx.h"
#include "audio/audio_pool.h"
#include "compiler.h"
#include "csv/2d.h"
#include "daw/limits.h"

#define MAX_AUDIO_ITEM_COUNT 256
#define AUDIO_ITEM_PADDING 64
#define AUDIO_ITEM_PADDING_DIV2 32
#define AUDIO_ITEM_PADDING_DIV2_FLOAT 32.0f
#define SG_AUDIO_ITEM_SEND_COUNT 3

typedef struct{
    t_audio_pool_item * audio_pool_item;  //pointer assigned when playing
    int audio_pool_uid;
    SGFLT ratio;
    int uid;
    int start_bar;
    double start_beat;
    double adjusted_start_beat;
    int timestretch_mode;  //tentatively: 0 == none, 1 == pitch, 2 == time+pitch
    SGFLT pitch_shift;
    SGFLT sample_start;
    SGFLT sample_end;
    int sample_start_offset;
    int sample_end_offset;
    //The audio track whose MultiFX instance to write the samples to
    int outputs[SG_AUDIO_ITEM_SEND_COUNT];
    int sidechain[SG_AUDIO_ITEM_SEND_COUNT];
    SGFLT vols[SG_AUDIO_ITEM_SEND_COUNT];
    SGFLT vols_linear[SG_AUDIO_ITEM_SEND_COUNT];
    t_int_frac_read_head sample_read_heads[SG_AUDIO_ITEM_SEND_COUNT];
    t_adsr adsrs[SG_AUDIO_ITEM_SEND_COUNT];
    int is_linear_fade_in;
    int is_linear_fade_out;
    SGFLT fade_vols[SG_AUDIO_ITEM_SEND_COUNT];
    //fade smoothing
    t_state_variable_filter lp_filters[SG_AUDIO_ITEM_SEND_COUNT];

    int index;

    SGFLT timestretch_amt;
    SGFLT sample_fade_in;
    SGFLT sample_fade_out;
    int sample_fade_in_end;
    int sample_fade_out_start;
    SGFLT sample_fade_in_divisor;
    SGFLT sample_fade_out_divisor;

    t_pit_ratio pitch_ratio_ptr;

    SGFLT pitch_shift_end;
    SGFLT timestretch_amt_end;
    int is_reversed;
    SGFLT fadein_vol;
    SGFLT fadeout_vol;
    int paif_automation_uid;  //TODO:  This was never used, delete
    t_paif * paif;
    t_papifx papifx;
} t_audio_item;

typedef struct
{
    int item_num;
    int send_num;
}t_audio_item_index;

typedef struct
{
    t_audio_item * items[MAX_AUDIO_ITEM_COUNT];
    t_audio_item_index indexes[DN_TRACK_COUNT][MAX_AUDIO_ITEM_COUNT];
    int index_counts[DN_TRACK_COUNT];
    int sample_rate;
    int uid;
} t_audio_items;

t_audio_item * g_audio_item_get(SGFLT);
t_audio_items * g_audio_items_get(int);
void v_audio_item_free(t_audio_item *);
/* t_audio_item * g_audio_item_load_single(SGFLT a_sr,
 * t_2d_char_array * f_current_string,
 * t_audio_items * a_items)
 *
 */
t_audio_item * g_audio_item_load_single(
    SGFLT a_sr,
    t_2d_char_array * f_current_string,
    t_audio_items * a_items,
    t_audio_pool * a_audio_pool,
    t_audio_pool_item * a_wav_item
);

void v_audio_item_set_fade_vol(
    t_audio_item *self,
    int a_send_num,
    t_sg_thread_storage* sg_ts
);
void v_audio_items_free(t_audio_items *a_audio_items);
#endif
