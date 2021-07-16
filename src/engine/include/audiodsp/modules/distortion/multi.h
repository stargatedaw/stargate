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

#ifndef MULTI_DIST_H
#define MULTI_DIST_H

#include "clipper.h"
#include "foldback.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "compiler.h"

typedef struct{
    SGFLT gain, in_db;
    t_clipper clipper1;
    t_audio_xfade dist_dry_wet;
}t_mds_multidist;

typedef SGFLT (*fp_multi_dist)(t_mds_multidist*, SGFLT, SGFLT);

SGFLT f_multi_dist_off(t_mds_multidist* self, SGFLT a_sample, SGFLT a_out);
SGFLT f_multi_dist_clip(t_mds_multidist* self, SGFLT a_sample, SGFLT a_out);
SGFLT f_multi_dist_foldback(
    t_mds_multidist* self,
    SGFLT a_sample,
    SGFLT a_out
);

//fp_multi_dist MULTI_DIST_FP[];

fp_multi_dist g_mds_get_fp(int index);
void v_mds_set_gain(t_mds_multidist * self, SGFLT a_db);
void g_mds_init(t_mds_multidist * self);

#endif /* MULTI_DIST_H */

