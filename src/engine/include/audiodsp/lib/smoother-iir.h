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

#ifndef SMOOTHER_IIR_H
#define SMOOTHER_IIR_H

#include "denormal.h"
#include "lmalloc.h"
#include "compiler.h"

typedef struct
{
    SGFLT output;
}t_smoother_iir;

/* void v_smr_iir_run(
 * t_smoother_iir *
 * a_smoother, SGFLT a_in)  //The input to be smoothed
 *
 * Use t_smoother_iir->output as your new control value after running this
 */
void v_smr_iir_run(t_smoother_iir*, SGFLT);
/* void v_smr_iir_run_fast(
 * t_smoother_iir *
 * a_smoother, SGFLT a_in)  //The input to be smoothed
 *
 * Use t_smoother_iir->output as your new control value after running this
 */
void v_smr_iir_run_fast(t_smoother_iir*, SGFLT);

t_smoother_iir * g_smr_iir_get_smoother();

#endif /* SMOOTHER_IIR_H */

