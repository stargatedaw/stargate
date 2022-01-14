#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/delay/chorus.h"


void g_crs_init(
    t_crs_chorus* f_result,
    SGFLT a_sr,
    int a_huge_pages
){
    int buffer_size = (int)(a_sr * 0.050f);
    SGFLT* buffer;

    if(a_huge_pages){
        hpalloc(
            (void**)&buffer,
            sizeof(SGFLT) * buffer_size
        );
    } else {
        lmalloc(
            (void**)&buffer,
            sizeof(SGFLT) * buffer_size
        );
    }

    int f_i;
    for(f_i = 0; f_i < buffer_size; ++f_i){
        buffer[f_i] = 0.0;
    }

    g_crs_init_buffer(
        f_result,
        a_sr,
        buffer,
        buffer_size
    );
}

void g_crs_init_buffer(
    t_crs_chorus* f_result,
    SGFLT a_sr,
    SGFLT* buffer,
    int buffer_size
){
    f_result->buffer = buffer;
    f_result->buffer_size = buffer_size;
    f_result->buffer_size_SGFLT = ((SGFLT)(f_result->buffer_size));
    f_result->pos_left = 0.0f;
    f_result->pos_right = 0.0f;
    f_result->buffer_ptr = 0;
    f_result->delay_offset_amt =  a_sr * 0.03f;
    f_result->delay_offset = 0.0f;
    g_lfs_init(&f_result->lfo, a_sr);
    f_result->wet_lin = 0.0f;
    f_result->wet_db = -99.99f;
    f_result->mod_amt = a_sr * 0.01f;
    f_result->freq_last = -99.99f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    g_svf2_init(&f_result->lp, a_sr);
    g_svf2_init(&f_result->hp, a_sr);
    v_svf2_set_res(&f_result->lp, -15.0f);
    v_svf2_set_res(&f_result->hp, -15.0f);
    v_svf2_set_cutoff_base(&f_result->hp, 50.0f);
    v_svf2_set_cutoff(&f_result->hp);
    v_svf2_set_cutoff_base(&f_result->lp, 90.0f);
    v_svf2_set_cutoff(&f_result->lp);
    v_lfs_sync(&f_result->lfo, 0.0f, 1);
}

void v_crs_chorus_set(t_crs_chorus* a_crs, SGFLT a_freq, SGFLT a_wet){
    if(a_wet != (a_crs->wet_db)){
        a_crs->wet_db = a_wet;
        a_crs->wet_lin = f_db_to_linear_fast(a_wet);
    }

    if(a_freq != (a_crs->freq_last)){
        a_crs->freq_last = a_freq;
        v_lfs_set(&a_crs->lfo, a_freq);
    }
}

void v_crs_chorus_run(t_crs_chorus* a_crs, SGFLT a_input0, SGFLT a_input1){
    a_crs->buffer[(a_crs->buffer_ptr)] = (a_input0 + a_input1) * 0.5f;

    a_crs->delay_offset = ((SGFLT)(a_crs->buffer_ptr)) -
            (a_crs->delay_offset_amt);

    v_lfs_run(&a_crs->lfo);

    a_crs->pos_left = ((a_crs->delay_offset) + ((a_crs->lfo.output) *
            (a_crs->mod_amt)));

    if((a_crs->pos_left) >= (a_crs->buffer_size_SGFLT)){
        a_crs->pos_left -= (a_crs->buffer_size_SGFLT);
    } else if((a_crs->pos_left) < 0.0f){
        a_crs->pos_left += (a_crs->buffer_size_SGFLT);
    }

    a_crs->pos_right = ((a_crs->delay_offset) + ((a_crs->lfo.output) *
            (a_crs->mod_amt) * -1.0f));

    if((a_crs->pos_right) >= (a_crs->buffer_size_SGFLT)){
        a_crs->pos_right -= (a_crs->buffer_size_SGFLT);
    } else if((a_crs->pos_right) < 0.0f){
        a_crs->pos_right += (a_crs->buffer_size_SGFLT);
    }

    SGFLT wet0, wet1;
    wet0 = f_cubic_interpolate_ptr_wrap(
        a_crs->buffer,
        a_crs->buffer_size,
        a_crs->pos_left
    ) * a_crs->wet_lin;
    wet1 = f_cubic_interpolate_ptr_wrap(
        a_crs->buffer,
        a_crs->buffer_size,
        a_crs->pos_right
    ) * a_crs->wet_lin;

    v_svf2_run_2_pole_hp(
        &a_crs->hp,
        wet0,
        wet1
    );
    v_svf2_run_2_pole_lp(
        &a_crs->lp,
        a_crs->hp.output0,
        a_crs->hp.output1
    );

    a_crs->output0 = a_input0 + a_crs->lp.output0;
    a_crs->output1 = a_input1 + a_crs->lp.output1;

    ++a_crs->buffer_ptr;
    if(a_crs->buffer_ptr >= a_crs->buffer_size){
        a_crs->buffer_ptr = 0;
    }
}

void v_crs_free(t_crs_chorus * a_crs){
    free(a_crs->buffer);
    //free(a_crs);
}

