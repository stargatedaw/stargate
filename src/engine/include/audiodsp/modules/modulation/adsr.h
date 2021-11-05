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

#ifndef ADSR_H
#define ADSR_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "compiler.h"

#define ADSR_DB 18.0f
#define ADSR_DB_THRESHOLD -18.0f
#define ADSR_DB_THRESHOLD_LINEAR 0.125f

#define ADSR_DB_RELEASE 48.0f
#define ADSR_DB_THRESHOLD_RELEASE -48.0f
#define ADSR_DB_THRESHOLD_LINEAR_RELEASE  0.00390625f

#define ADSR_STAGE_DELAY 0
#define ADSR_STAGE_ATTACK 1
#define ADSR_STAGE_HOLD 2
#define ADSR_STAGE_DECAY 3
#define ADSR_STAGE_SUSTAIN 4
#define ADSR_STAGE_RELEASE 5
#define ADSR_STAGE_WAIT 6
#define ADSR_STAGE_OFF 7

typedef struct st_adsr {
    SGFLT output;
    SGFLT output_db;
    int stage;  //0=a,1=d,2=s,3=r,4=inactive,6=delay,9=hold
    SGFLT a_inc;
    SGFLT d_inc;
    SGFLT s_value;
    SGFLT r_inc;

    SGFLT a_inc_db;
    SGFLT d_inc_db;
    SGFLT r_inc_db;

    SGFLT a_time;
    SGFLT d_time;
    SGFLT r_time;

    int time_counter;
    int delay_count;
    int hold_count;
    int wait_count;

    SGFLT sr;
    SGFLT sr_recip;
} t_adsr;

void v_adsr_set_a_time(t_adsr*, SGFLT);
void v_adsr_set_d_time(t_adsr*, SGFLT);
void v_adsr_set_s_value(t_adsr*, SGFLT);
void v_adsr_set_s_value_db(t_adsr*, SGFLT);
void v_adsr_set_r_time(t_adsr*, SGFLT);
void v_adsr_set_fast_release(t_adsr*);

void v_adsr_set_delay_time(t_adsr*, SGFLT);
void v_adsr_set_hold_time(t_adsr*, SGFLT);

void v_adsr_set_adsr_db(t_adsr*, SGFLT, SGFLT, SGFLT, SGFLT);
void v_adsr_set_adsr(t_adsr*, SGFLT, SGFLT, SGFLT, SGFLT);
void v_adsr_set_adsr_lin_from_db(t_adsr*, SGFLT, SGFLT, SGFLT, SGFLT);

void v_adsr_retrigger(t_adsr *);
void v_adsr_release(t_adsr *);
void v_adsr_run(t_adsr *);
void v_adsr_run_db(t_adsr *);
void v_adsr_kill(t_adsr *);
void g_adsr_init(t_adsr * f_result, SGFLT a_sr);

typedef void (*fp_adsr_run)(t_adsr*);
typedef void (*fp_adsr_set)(t_adsr*, SGFLT, SGFLT, SGFLT, SGFLT);

extern fp_adsr_set FP_ADSR_SET[2];
extern fp_adsr_run FP_ADSR_RUN[2];

typedef void (*fn_adsr_run)(t_adsr*);
//fn_adsr_run ADSR_RUN[];
//fn_adsr_run ADSR_RUN_DB[];

#endif /* ADSR_H */

