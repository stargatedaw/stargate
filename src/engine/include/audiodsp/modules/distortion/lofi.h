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

#ifndef LOFI_H
#define LOFI_H

#include <math.h>
#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

typedef struct
{
    SGFLT bits, multiplier, recip;
    int val0, val1;
    SGFLT output0, output1;
} t_lfi_lofi;

t_lfi_lofi * g_lfi_lofi_get();
void v_lfi_lofi_set(t_lfi_lofi*, SGFLT);
void v_lfi_lofi_run(t_lfi_lofi*, SGFLT, SGFLT);
void g_lfi_init(t_lfi_lofi * f_result);
t_lfi_lofi * g_lfi_lofi_get();

#endif /* LOFI_H */

