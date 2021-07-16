#include <math.h>

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/modules/distortion/saturator.h"


void v_sat_free(t_sat_saturator * a_sat)
{
    free(a_sat);
}

void v_sat_set(t_sat_saturator* a_sat, SGFLT a_ingain, SGFLT a_amt,
        SGFLT a_outgain)
{
    if(a_ingain != (a_sat->last_ingain))
    {
        a_sat->last_ingain = a_ingain;
        a_sat->ingain_lin = f_db_to_linear_fast(a_ingain);
    }

    if(a_amt != (a_sat->amount))
    {
        a_sat->a=(a_amt*0.005)*3.141592f;
        a_sat->b = 1.0f / (sin((a_amt*0.005) * 3.141592f));
        a_sat->amount = a_amt;
    }

    if(a_outgain != (a_sat->last_outgain))
    {
        a_sat->last_outgain = a_outgain;
        a_sat->outgain_lin = f_db_to_linear_fast(a_outgain);
    }
}

void v_sat_run(t_sat_saturator* a_sat, SGFLT a_in0, SGFLT a_in1)
{
    a_sat->output0 = f_sg_min(
        f_sg_max(
        sin(
        f_sg_max(
        f_sg_min((a_in0 * (a_sat->ingain_lin)), 1.0f), -1.0f) * (a_sat->a))
        * (a_sat->b) ,-1.0f) ,1.0f) * (a_sat->outgain_lin);

    a_sat->output1 = f_sg_min(
        f_sg_max(
        sin(
        f_sg_max(
        f_sg_min((a_in1 * (a_sat->ingain_lin)), 1.0f), -1.0f) * (a_sat->a))
        * (a_sat->b) ,-1.0f) ,1.0f) * (a_sat->outgain_lin);
}

void g_sat_init(t_sat_saturator * f_result)
{
    f_result->a = 0.0f;
    f_result->b = 0.0f;
    f_result->amount = 1.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->ingain_lin = 1.0f;
    f_result->outgain_lin = 1.0f;
    f_result->last_ingain = 12345.0f;
    f_result->last_outgain = 12345.0f;
}
