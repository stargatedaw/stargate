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

#ifndef SOFT_CLIPPER_H
#define SOFT_CLIPPER_H

#include "audiodsp/lib/amp.h"
#include "compiler.h"

typedef struct st_scl_soft_clipper
{
    SGFLT threshold_db;
    SGFLT threshold_linear, threshold_linear_neg;
    SGFLT amount;
    SGFLT output0;
    SGFLT output1;
    SGFLT temp;
}t_soft_clipper;

void v_scl_set(t_soft_clipper*,SGFLT,SGFLT);
void v_scl_run(t_soft_clipper*,SGFLT,SGFLT);
t_soft_clipper * g_scl_get();

#endif /* SOFT_CLIPPER_H */

