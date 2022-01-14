#include <math.h>

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/lib/peak_meter.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/modules/dynamics/limiter.h"
#include "audiodsp/modules/filter/svf.h"


void v_lim_free(t_lim_limiter * a_lim)
{
    if(a_lim)
    {
        free(a_lim->buffer0);
        free(a_lim->buffer1);
        //free(a_lim);
    }
}

void v_lim_set(t_lim_limiter*a_lim, SGFLT a_thresh, SGFLT a_ceiling,
        SGFLT a_release)
{
    if(a_thresh != a_lim->last_thresh)
    {
        a_lim->thresh = f_db_to_linear_fast(a_thresh);
        a_lim->autogain = 1.0f / a_lim->thresh;
        a_lim->last_thresh = a_thresh;
    }

    if(a_ceiling != a_lim->last_ceiling)
    {
        a_lim->volume = f_db_to_linear_fast(a_ceiling);
        a_lim->last_ceiling = a_ceiling;
    }

    if(a_release != a_lim->last_release)
    {
        if(a_release <= 0)
        {
            a_lim->release = 0.005f;
        }
        else
        {
            a_lim->release = a_release * 0.001f;
        }


        a_lim->r = (a_lim->sr_recip / a_lim->release) * SG_HOLD_TIME_DIVISOR;
        a_lim->last_release = a_release;
    }
}

void v_lim_run(t_lim_limiter *a_lim, SGFLT a_in0, SGFLT a_in1)
{
    a_lim->maxSpls = f_sg_max(f_sg_abs(a_in0), f_sg_abs(a_in1));

    /*clip at 24dB.  If a memory error causes a huge value,
     * the limiter would never return.*/
    if(a_lim->maxSpls > 16.0f)
    {
        a_lim->maxSpls = 16.0f;
    }

    ++a_lim->r1Timer;

    if(a_lim->r1Timer >= a_lim->holdtime)
    {
        a_lim->r1Timer = 0;
        a_lim->max1Block = (a_lim->max1Block) - (a_lim->r);

        if((a_lim->max1Block) < 0.0f)
        {
            a_lim->max1Block = 0.0f;
        }
    }

    a_lim->max1Block = f_sg_max(a_lim->max1Block, a_lim->maxSpls);
    ++a_lim->r2Timer;

    if(a_lim->r2Timer >= a_lim->holdtime)
    {
        a_lim->r2Timer = 0;
        a_lim->max2Block = a_lim->max2Block - a_lim->r;

        if((a_lim->max2Block) < 0.0f)
        {
            a_lim->max2Block = 0.0f;
        }
    }

    a_lim->max2Block = f_sg_max(a_lim->max2Block, a_lim->maxSpls);

    a_lim->env = f_sg_max(a_lim->max1Block, a_lim->max2Block);

    if(a_lim->env > a_lim->thresh)
    {
        a_lim->gain = (a_lim->thresh / a_lim->env) * a_lim->volume;
    }
    else
    {
        a_lim->gain = a_lim->volume;
    }

    a_lim->buffer0[a_lim->buffer_index] = a_in0;
    a_lim->buffer1[a_lim->buffer_index] = a_in1;

    ++a_lim->buffer_index;

    if(a_lim->buffer_index >= a_lim->buffer_size)
    {
        a_lim->buffer_index = 0;
    }

    SGFLT f_gain =
        v_svf_run_4_pole_lp(&a_lim->filter, a_lim->gain * a_lim->autogain);

    a_lim->output0 = a_lim->buffer0[a_lim->buffer_index] * f_gain;
    a_lim->output1 = a_lim->buffer1[a_lim->buffer_index] * f_gain;

    v_pkm_redux_run(&a_lim->peak_tracker, a_lim->gain);
}

void g_lim_init(t_lim_limiter * f_result, SGFLT a_sr, int a_huge_pages)
{
    f_result->holdtime = ((int)(a_sr / SG_HOLD_TIME_DIVISOR));

    f_result->buffer_size = f_result->holdtime; // (int)(a_sr*0.003f);
    f_result->buffer_index = 0;

    if(a_huge_pages)
    {
        hpalloc((void**)&f_result->buffer0,
            sizeof(SGFLT) * f_result->buffer_size);
        hpalloc((void**)&f_result->buffer1,
            sizeof(SGFLT) * f_result->buffer_size);
    }
    else
    {
        lmalloc((void**)&f_result->buffer0,
            sizeof(SGFLT) * f_result->buffer_size);
        lmalloc((void**)&f_result->buffer1,
            sizeof(SGFLT) * f_result->buffer_size);
    }

    int f_i;

    for(f_i = 0; f_i < f_result->buffer_size; ++f_i)
    {
        f_result->buffer0[f_i] = 0.0f;
        f_result->buffer1[f_i] = 0.0f;
    }

    f_result->r1Timer = 0;
    f_result->r2Timer = f_result->holdtime / 2;

    f_result->ceiling = 0.0f;
    f_result->env = 0.0f;
    f_result->envT = 0.0f;
    f_result->gain = 0.0f;
    f_result->max1Block = 0.0f;
    f_result->max2Block = 0.0f;
    f_result->maxSpls = 0.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->r = 0.0f;
    f_result->release = 0.0f;
    f_result->thresh = 0.0f;
    f_result->volume = 0.0f;
    f_result->sr = a_sr;
    f_result->sr_recip = 1.0f / a_sr;

    g_svf_init(&f_result->filter, a_sr);
    v_svf_set_res(&f_result->filter, -9.0f);
    v_svf_set_cutoff_base(&f_result->filter, f_pit_hz_to_midi_note(4000.0f));
    v_svf_set_cutoff(&f_result->filter);

    for(f_i = 0; f_i < 50; ++f_i)
    {
        v_svf_run_4_pole_lp(&f_result->filter, 1.0f);
    }

    //nonsensical values that it won't evaluate to on the first run
    f_result->last_ceiling = 1234.4522f;
    f_result->last_release = 1234.4522f;
    f_result->last_thresh = 1234.4532f;

    g_pkm_redux_init(&f_result->peak_tracker, a_sr);
}

