#ifndef AUDIO_PAIFX_H
#define AUDIO_PAIFX_H

#include "audiodsp/modules/multifx/multifx3knob.h"
#include "compiler.h"

#define SG_PAIF_PER_ITEM 8

// Per-audio-pool-item effects
typedef struct{
    SGFLT knobs[3];
    int fx_type;
    fp_mf3_run func_ptr;
}t_papifx_controls;

// Each audio pool entry has one of these
typedef struct{
    int loaded;
    t_papifx_controls controls[SG_PAIF_PER_ITEM];
}t_file_fx_controls;

// Each audio item has one of these
typedef struct{
    t_mf3_multi * fx[SG_PAIF_PER_ITEM];
}t_papifx;

void file_fx_controls_init(t_file_fx_controls*);
void papifx_controls_init(t_papifx_controls*);
void papifx_init(t_papifx*, SGFLT);
void papifx_free(t_papifx*, int);
void papifx_reset(t_file_fx_controls*);
void papifx_paste(const char* _str);

//Per-audio-item effects
typedef struct{
    SGFLT a_knobs[3];
    int fx_type;
    fp_mf3_run func_ptr;
    t_mf3_multi * mf3;
}t_per_audio_item_fx;

typedef struct{
    int loaded;
    t_per_audio_item_fx* items[SG_PAIF_PER_ITEM];
}t_paif;

t_per_audio_item_fx * g_paif_get(SGFLT);
t_paif * g_paif8_get();
void v_paif_free(t_paif * self);

#endif
