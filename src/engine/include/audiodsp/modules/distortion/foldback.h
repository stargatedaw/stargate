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

#ifndef FOLDBACK_H
#define FOLDBACK_H

#include <math.h>

#include "audiodsp/lib/amp.h"
#include "compiler.h"


typedef struct
{
    SGFLT thresh, thresh_db, gain, gain_db, output[2];
} t_fbk_foldback;

void g_fbk_init(t_fbk_foldback * self);
void v_fbk_set(t_fbk_foldback * self, SGFLT a_thresh_db, SGFLT a_gain_db);
void v_fbk_run(t_fbk_foldback * self, SGFLT a_input0, SGFLT a_input1);
SGFLT f_fbk_mono(SGFLT a_val);

#endif /* FOLDBACK_H */

