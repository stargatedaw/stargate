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

#ifndef PANNER2_H
#define PANNER2_H

#include "compiler.h"

typedef struct {
    SGFLT gainL, gainR;
} t_pn2_panner2;


void g_pn2_init(t_pn2_panner2* self);
void v_pn2_set(t_pn2_panner2* self, SGFLT a_pan, SGFLT a_law);
// Normalize the volume at center to remain unchanged
void v_pn2_set_normalize(t_pn2_panner2* self, SGFLT a_pan, SGFLT a_law);

#endif /* PANNER2_H */

