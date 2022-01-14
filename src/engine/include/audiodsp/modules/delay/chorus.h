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

#ifndef CHORUS_H
#define CHORUS_H

#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "compiler.h"

typedef struct {
    SGFLT* buffer;
    SGFLT wet_lin, wet_db, freq_last, mod_amt;
    SGFLT output0, output1;
    SGFLT delay_offset_amt, delay_offset;
    SGFLT pos_left, pos_right;
    int buffer_size, buffer_ptr;
    SGFLT buffer_size_SGFLT;
    t_lfs_lfo lfo;
    t_svf2_filter hp;
    t_svf2_filter lp;
} t_crs_chorus;

void v_crs_free(t_crs_chorus*);
void v_crs_chorus_set(t_crs_chorus*, SGFLT, SGFLT);
void v_crs_chorus_run(t_crs_chorus*, SGFLT, SGFLT);
void g_crs_init(t_crs_chorus* f_result, SGFLT a_sr, int a_huge_pages);
void g_crs_init_buffer(
    t_crs_chorus* self,
    SGFLT a_sr,
    SGFLT* buffer,
    int buffer_size
);

#endif /* CHORUS_H */

