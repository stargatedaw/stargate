#include "audiodsp/modules/distortion/foldback.h"


void g_fbk_init(t_fbk_foldback * self){
    self->output[0] = 0.0f;
    self->output[1] = 0.0f;
    self->thresh = 1.0f;
    self->thresh_db = 0.0f;
    self->gain = 1.0f;
    self->gain_db = 0.0f;
}

void v_fbk_set(
    t_fbk_foldback * self,
    SGFLT a_thresh_db,
    SGFLT a_gain_db
){
    if(self->gain_db != a_gain_db){
        self->gain_db = a_gain_db;
        self->gain = f_db_to_linear_fast(a_gain_db);
    }

    if(self->thresh_db != a_thresh_db){
        self->thresh_db = a_thresh_db;
        self->thresh = f_db_to_linear_fast(a_thresh_db);
    }
}

void v_fbk_run(t_fbk_foldback * self, SGFLT a_input0, SGFLT a_input1)
{
    a_input0 *= self->gain;
    a_input1 *= self->gain;

    SGFLT f_arr[2] = {a_input0, a_input1};
    int f_i;

    for(f_i = 0; f_i < 2; ++f_i)
    {
        SGFLT f_input = f_arr[f_i];
        if(f_input > 0.0f)
        {
            if(f_input > self->thresh)
            {
                f_input = self->thresh - (f_input - self->thresh);
                if(f_input < 0.0f)
                {
                    f_input = 0.0f;
                }
            }
            self->output[f_i] = f_input;
        }
        else
        {
            f_input *= -1.0f;
            if(f_input > self->thresh)
            {
                f_input = self->thresh - (f_input - self->thresh);
                if(f_input < 0.0f)
                {
                    f_input = 0.0f;
                }
            }
            self->output[f_i] = f_input * -1.0f;
        }
    }
}

SGFLT f_fbk_mono(SGFLT a_val)
{
    if(a_val > 1.0f)
    {
        return 1.0 - fmodf(a_val, 1.0f);
    }
    else if(a_val < -1.0f)
    {
        return fmodf(a_val, 1.0f);
    }
    else
    {
        return a_val;
    }
}

