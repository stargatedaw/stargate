#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/distortion/soft_clipper.h"


void v_scl_set(t_soft_clipper* a_scl, SGFLT a_threshold_db, SGFLT a_amount)
{
    if(a_threshold_db != (a_scl->threshold_db))
    {
        a_scl->threshold_db = a_threshold_db;
        a_scl->threshold_linear = f_db_to_linear_fast(a_threshold_db);
        a_scl->threshold_linear_neg = (a_scl->threshold_linear) * -1.0f;
    }

    a_scl->amount = a_amount;
}

void v_scl_run(t_soft_clipper* a_scl,SGFLT a_in0, SGFLT a_in1)
{
    if(a_in0 > (a_scl->threshold_linear))
    {
        a_scl->temp = a_in0 - (a_scl->threshold_linear);
        a_scl->output0 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear);
    }
    else if(a_in0 < (a_scl->threshold_linear_neg))
    {
        a_scl->temp = a_in0 - (a_scl->threshold_linear_neg);
        a_scl->output0 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear_neg);
    }


    if(a_in1 > (a_scl->threshold_linear))
    {
        a_scl->temp = a_in1 - (a_scl->threshold_linear);
        a_scl->output1 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear);
    }
    else if(a_in1 < (a_scl->threshold_linear_neg))
    {
        a_scl->temp = a_in1 - (a_scl->threshold_linear_neg);
        a_scl->output1 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear_neg);
    }
}

t_soft_clipper * g_scl_get()
{
    t_soft_clipper * f_result = (t_soft_clipper*)malloc(sizeof(t_soft_clipper));

    f_result->amount = 1.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->temp = 0.0f;
    f_result->threshold_db = 0.0f;
    f_result->threshold_linear = 1.0f;
    f_result->threshold_linear_neg = -1.0f;

    return f_result;
}
