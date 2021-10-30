#include "audio/paifx.h"
#include "audiodsp/modules/multifx//multifx3knob.h"
#include "csv/1d.h"
#include "daw.h"

void papifx_controls_init(t_papifx_controls* self){
    self->knobs[0] = 64.;
    self->knobs[1] = 64.;
    self->knobs[2] = 64.;
    self->fx_type = 0;
    self->func_ptr = v_mf3_run_off;
}

void file_fx_controls_init(t_file_fx_controls* self){
    int i;
    for(i = 0; i < 8; ++i){
        papifx_controls_init(&self->controls[i]);
    }
    self->loaded = 0;
}

void papifx_init(t_papifx* self, SGFLT sr){
    int i;
    for(i = 0; i < 8; ++i){
        self->fx[i] = g_mf3_get(sr);
    }
}

void papifx_free(t_papifx* self, int free_ptr){
    int i;
    for(i = 0; i < 8; ++i){
        v_mf3_free(self->fx[i]);
    }
    if(free_ptr){
        free(self);
    }
}

void papifx_reset(t_file_fx_controls* self){
    int i;
    for(i = 0; i < 8; ++i){
        self->controls[i].knobs[0] = 64.;
        self->controls[i].knobs[1] = 64.;
        self->controls[i].knobs[2] = 64.;
        self->controls[i].fx_type = 0;
        self->controls[i].func_ptr = v_mf3_run_off;
    }
    self->loaded = 0;
}

void papifx_paste(const char* _str){
    t_1d_char_array* arr = c_split_str(_str, '|', 34, 32);
    sg_assert(
        !strcmp(arr->array[0], "f"),
        "papifx_paste: Invalid first char: %s",
        (char*)_str
    );

    int ap_uid = atoi(arr->array[1]);
    SGFLT val;
    int i;
    for(i = 2; i < 34; ++i){
        val = atof(arr->array[i]);
        v_daw_papifx_set_control(
            ap_uid,
            i - 2,
            val
        );
    }
}

t_per_audio_item_fx * g_paif_get(SGFLT a_sr)
{
    t_per_audio_item_fx * f_result;
    lmalloc((void**)&f_result, sizeof(t_per_audio_item_fx));

    int f_i = 0;
    while(f_i < 3)
    {
        f_result->a_knobs[f_i] = 64.0f;
        ++f_i;
    }
    f_result->fx_type = 0;
    f_result->func_ptr = v_mf3_run_off;
    f_result->mf3 = g_mf3_get(a_sr);

    return f_result;
}

t_paif * g_paif8_get()
{
    t_paif * f_result;
    lmalloc((void**)&f_result, sizeof(t_paif));

    int f_i;
    for(f_i = 0; f_i < SG_PAIF_PER_ITEM; ++f_i)
    {
        f_result->items[f_i] = NULL;
    }

    f_result->loaded = 0;

    return f_result;
}

void v_paif_free(t_paif * self)
{
    int f_i2;
    for(f_i2 = 0; f_i2 < SG_PAIF_PER_ITEM; ++f_i2)
    {
        if(self->items[f_i2])
        {
            v_mf3_free(self->items[f_i2]->mf3);
            free(self->items[f_i2]);
            self->items[f_i2] = 0;
        }
    }
}
