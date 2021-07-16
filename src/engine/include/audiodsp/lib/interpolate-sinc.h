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

#ifndef INTERPOLATE_SINC_H
#define INTERPOLATE_SINC_H

#include <math.h>
#include <stdlib.h>
#include "interpolate-linear.h"
#include "lmalloc.h"
#include "compiler.h"

typedef struct
{
    SGFLT * sinc_table;
    int table_size;
    int points;
    int points_div2;
    int samples_per_point;
    int i;
    SGFLT result;
    SGFLT SGFLT_iterator_up;
    SGFLT SGFLT_iterator_down;
    int pos_int;
    SGFLT pos_frac;
}t_sinc_interpolator;

typedef struct
{
    SGFLT last_increment;
    SGFLT SGFLT_increment;
    int int_increment;
    SGFLT fraction;
    int whole_number;
}t_int_frac_read_head;

SGFLT f_sinc_interpolate(t_sinc_interpolator*,SGFLT*,SGFLT);
SGFLT f_sinc_interpolate2(t_sinc_interpolator*,SGFLT*,int,SGFLT);
t_sinc_interpolator * g_sinc_get(int, int, double, double, SGFLT);

t_int_frac_read_head * g_ifh_get();
void v_ifh_run(t_int_frac_read_head*, SGFLT);
void v_ifh_run_reverse(t_int_frac_read_head*, SGFLT);
void v_ifh_retrigger(t_int_frac_read_head*, int);
void g_ifh_init(t_int_frac_read_head * f_result);
void g_sinc_init(
    t_sinc_interpolator * f_result,
    int a_points,
    int a_samples_per_point,
    double a_fc,
    double a_sr,
    SGFLT a_normalize_to
);

#endif /* INTERPOLATE_SINC_H */

