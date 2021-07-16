#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/modules/modulation/ramp_env.h"


void f_rmp_run_ramp(t_ramp_env* a_rmp_ptr)
{
    if((a_rmp_ptr->output_multiplier) == 0.0f )
    {
        a_rmp_ptr->output_multiplied = 0.0f;
        return;
    }

    if((a_rmp_ptr->output) == 1.0f)
    {
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }

    a_rmp_ptr->output = (a_rmp_ptr->output) + (a_rmp_ptr->ramp_inc);

    if((a_rmp_ptr->output) >= 1.0f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }

    a_rmp_ptr->output_multiplied =
        (a_rmp_ptr->output) * (a_rmp_ptr->output_multiplier);
}


void f_rmp_run_ramp_curve(t_ramp_env* a_rmp_ptr)
{
    f_rmp_run_ramp(a_rmp_ptr);

    a_rmp_ptr->output_multiplied =
    f_cubic_interpolate_ptr(a_rmp_ptr->curve_table, 2.0f + a_rmp_ptr->output)
        * (a_rmp_ptr->output_multiplier);
}


/* void v_rmp_set_time(
 * t_ramp_env* a_rmp_ptr,
 * SGFLT a_time)  //time in seconds
 *
 * Set envelope time without retriggering the envelope
 */
void v_rmp_set_time(t_ramp_env* a_rmp_ptr,SGFLT a_time)
{
    a_rmp_ptr->ramp_time = a_time;

    if((a_rmp_ptr->ramp_time) <= .01f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }
}

/* void v_rmp_set_time(
 * t_ramp_env* a_rmp_ptr,
 * SGFLT a_time,  //time in seconds
 * SGFLT a_curve) // 0.0 to 1.0
 *
 * Retrigger when using with
 */
void v_rmp_retrigger_curve(t_ramp_env* a_rmp_ptr, SGFLT a_time, SGFLT a_multiplier, SGFLT a_curve)
{
    v_rmp_retrigger(a_rmp_ptr, a_time, a_multiplier);

    if(a_rmp_ptr->curve != a_curve)
    {
        a_rmp_ptr->curve_table[1] = f_linear_interpolate(0.0f, a_curve, 0.66666f);
        a_rmp_ptr->curve_table[2] = f_linear_interpolate(a_curve, 1.0f, 0.33333f);
        a_rmp_ptr->curve = a_curve;
    }
}


/*void v_rmp_retrigger(
 * t_ramp_env* a_rmp_ptr,
 * SGFLT a_time,
 * SGFLT a_multiplier)
 */
void v_rmp_retrigger(t_ramp_env* a_rmp_ptr, SGFLT a_time, SGFLT a_multiplier)
{
    a_rmp_ptr->output = 0.0f;
    a_rmp_ptr->ramp_time = a_time;
    a_rmp_ptr->output_multiplier = a_multiplier;

    if((a_rmp_ptr->ramp_time) <= .05f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }

}

/*Glide with constant time in seconds*/
void v_rmp_retrigger_glide_t(t_ramp_env* a_rmp_ptr, SGFLT a_time, SGFLT a_current_note, SGFLT a_next_note)
{
    a_rmp_ptr->ramp_time = a_time;

    a_rmp_ptr->output_multiplier = a_next_note - a_current_note;

    /*Turn off if true*/
    if((a_rmp_ptr->ramp_time) <= .05f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }

}

/*Glide with constant rate in seconds-per-octave*/
void v_rmp_retrigger_glide_r(t_ramp_env* a_rmp_ptr, SGFLT a_time, SGFLT a_current_note, SGFLT a_next_note)
{
    a_rmp_ptr->output = 0.0f;
    a_rmp_ptr->output_multiplier = a_next_note - a_current_note;
    a_rmp_ptr->ramp_time = a_time * (a_rmp_ptr->output_multiplier) * .083333f;

    /*Turn off if true*/
    if((a_rmp_ptr->ramp_time) <= .05f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }
}

void g_rmp_init(t_ramp_env * f_result, SGFLT a_sr)
{
    f_result->sr = a_sr;
    f_result->sr_recip = 1.0f/a_sr;
    f_result->output_multiplied = 0.0f;
    f_result->output_multiplier = 1.0f;
    f_result->ramp_inc = .01f;
    f_result->ramp_time = .05f;
    f_result->output = 0.0f;
    f_result->curve = 1342.0f;
    f_result->last_curve = 422.4f;
    f_result->curve_table[0] = 0.0f;
    f_result->curve_table[1] = 0.3333f;
    f_result->curve_table[2] = 0.6666f;
    f_result->curve_table[3] = 1.0f;
    f_result->curve_table[4] = 1.0f;
}

/*t_ramp_env * g_rmp_get_ramp_env(
 * SGFLT a_sr  //sample rate
 * )
 */
t_ramp_env * g_rmp_get_ramp_env(SGFLT a_sr)
{
    t_ramp_env * f_result;
    lmalloc((void**)&f_result, sizeof(t_ramp_env));
    g_rmp_init(f_result, a_sr);
    return f_result;
}
