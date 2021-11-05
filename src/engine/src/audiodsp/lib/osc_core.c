#include <stdlib.h>

#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"


void g_init_osc_core(t_osc_core * f_result)
{
    f_result->output = 0.0f;
}

void v_osc_core_free(t_osc_core * a_osc)
{
    free(a_osc);
}

/* void v_run_osc(
 * t_osc_core *a_core,
 * SGFLT a_inc) //The increment to run the oscillator by.
 * The oscillator will increment until it reaches 1,
 * then resets to (value - 1), for each oscillation
 */
void v_run_osc(t_osc_core *a_core, SGFLT a_inc)
{
    a_core->output = (a_core->output) + a_inc;

    if(unlikely(a_core->output >= 1.0f))
    {
        a_core->output -= 1.0f;
    }
}

int v_run_osc_sync(t_osc_core *a_core, SGFLT a_inc)
{
    a_core->output += a_inc;

    if(unlikely(a_core->output >= 1.0f))
    {
        a_core->output = (a_core->output - 1.0f);
        return 1;
    }
    else
    {
        return 0;
    }
}

