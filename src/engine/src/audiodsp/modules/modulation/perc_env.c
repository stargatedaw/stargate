#include "audiodsp/modules/modulation/perc_env.h"


/*
 * void v_pnv_set(t_pnv_perc_env* a_pnv, SGFLT a_t1, SGFLT a_p1,
        SGFLT a_t2, SGFLT a_p2, SGFLT a_note_pitch)
 */
void v_pnv_set(t_pnv_perc_env* a_pnv, SGFLT a_t1, SGFLT a_p1,
        SGFLT a_t2, SGFLT a_p2, SGFLT a_note_pitch)
{
    a_pnv->value = a_p1;
    a_pnv->current_env = 0;
    a_pnv->counter = 0;
    a_pnv->sample_counts[0] = (int)(a_pnv->sample_rate * a_t1);
    a_pnv->sample_counts[1] = (int)(a_pnv->sample_rate * a_t2);
    a_pnv->incs[0] = (a_p2 - a_p1) / a_pnv->sample_counts[0];
    a_pnv->incs[1] = (a_note_pitch - a_p2) / a_pnv->sample_counts[1];
}

SGFLT f_pnv_run(t_pnv_perc_env * a_pnv)
{
    if(a_pnv->current_env < KICK_ENV_SECTIONS)
    {
        a_pnv->value += a_pnv->incs[a_pnv->current_env];

        ++a_pnv->counter;

        if(a_pnv->counter >= a_pnv->sample_counts[a_pnv->current_env])
        {
            a_pnv->counter = 0;
            ++a_pnv->current_env;
        }
    }

    return a_pnv->value;
}

void g_pnv_init(t_pnv_perc_env * f_result, SGFLT a_sr){
    f_result->sample_rate = a_sr;

    v_pnv_set(f_result, 0.01f, 75.0f, 0.15f, 48.0f, 24.0f);
}

t_pnv_perc_env * g_pnv_get(SGFLT a_sr)
{
    t_pnv_perc_env * f_result = (t_pnv_perc_env*)malloc(sizeof(t_pnv_perc_env));

    g_pnv_init(f_result, a_sr);

    return f_result;
}

