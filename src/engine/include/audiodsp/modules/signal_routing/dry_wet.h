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

#ifndef DRY_WET_H
#define DRY_WET_H

#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/amp.h"
#include "compiler.h"

typedef struct {
    SGFLT wet_db;
    SGFLT wet_linear;
    SGFLT dry_db;
    SGFLT dry_linear;
    SGFLT output;
} t_dw_dry_wet;

/*void v_dw_set_dry_wet(
 * t_dw_dry_wet* a_dw,
 * SGFLT a_dry_db, //dry value in decibels, typically -50 to 0
 * SGFLT a_wet_db) //wet value in decibels, typically -50 to 0
 */
void v_dw_set_dry_wet(t_dw_dry_wet*,SGFLT,SGFLT);
/* void v_dw_run_dry_wet(
 * t_dw_dry_wet* a_dw,
 * SGFLT a_dry, //dry signal
 * SGFLT a_wet) //wet signal
 */
void v_dw_run_dry_wet(t_dw_dry_wet*,SGFLT,SGFLT);
t_dw_dry_wet* g_dw_get_dry_wet();
void dry_wet_init(t_dw_dry_wet*);

#endif /* DRY_WET_H */

