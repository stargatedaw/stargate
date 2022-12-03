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

#ifndef DC_OFFSET_FILTER_H
#define DC_OFFSET_FILTER_H

#include "audiodsp/lib/denormal.h"
#include "compiler.h"


typedef struct {
    SGFLT in_n_m1, out_n_m1, coeff;
}t_dco_dc_offset_filter;

struct StereoDCFilter {
    t_dco_dc_offset_filter left;
    t_dco_dc_offset_filter right;
};

t_dco_dc_offset_filter * g_dco_get(SGFLT);
SGFLT f_dco_run(t_dco_dc_offset_filter*,SGFLT);
void v_dco_reset(t_dco_dc_offset_filter*);
void g_dco_init(t_dco_dc_offset_filter * f_result, SGFLT a_sr);

void stereo_dc_filter_init(struct StereoDCFilter* self, SGFLT sr);
void stereo_dc_filter_reset(struct StereoDCFilter* self);
struct SamplePair stereo_dc_filter_run(
    struct StereoDCFilter* self,
    struct SamplePair input
);

#endif /* DC_OFFSET_FILTER_H */

