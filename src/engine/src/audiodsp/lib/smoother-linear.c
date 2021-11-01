#include <math.h>

#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/lib/smoother-linear.h"


void g_sml_init(
    t_smoother_linear* f_result,
    SGFLT a_sample_rate,
    SGFLT a_high,
    SGFLT a_low,
    SGFLT a_time_in_seconds
){
    sg_assert(a_high > a_low, "g_sml_init: high %f <= low %f", a_high, a_low);
    f_result->last_value = (((a_high - a_low) * .5f) + a_low);

    /*Rate is the time it would take to complete if the knob was all
     * the way counter-clockwise, and then instantly moved all the
     * way clockwise*/
    f_result->rate = (((a_high - a_low ) / a_time_in_seconds) / a_sample_rate);

    f_result->sample_rate = a_sample_rate;
    f_result->sr_recip = 1.0f / a_sample_rate;
}

/* void v_sml_run(
 * t_smoother_linear * a_smoother,
 * SGFLT a_current_value) //the current control value you wish to smooth
 *
 * smoother->last_value will be the smoothed value
 */
void v_sml_run(t_smoother_linear * a_smoother, SGFLT a_current_value)
{
    /*Evaluated first because most controls won't be moving most of the time,
     * should consume the fewest cycles*/
    if((a_smoother->last_value) == a_current_value)
    {
        //Do nothing
    }
    /*This does waste CPU while knobs are being moved, but it will effectively
     *  kill the knobs processing once it does reach it's destination value*/
    /*Moving up*/
    else if(((a_current_value > (a_smoother->last_value)) &&
            (a_current_value - (a_smoother->last_value) <= (a_smoother->rate)))
            /*Moving down*/
            || ((a_current_value < (a_smoother->last_value)) &&
            ((a_smoother->last_value) - a_current_value <= (a_smoother->rate))))
    {
        a_smoother->last_value = a_current_value;
    }

    /*Moving down*/
    else if(a_current_value > (a_smoother->last_value))
    {
        a_smoother->last_value = (a_smoother->last_value) + (a_smoother->rate);
    }

    /*Moving up*/
    else
    {
        a_smoother->last_value = (a_smoother->last_value) - (a_smoother->rate);
    }
}

