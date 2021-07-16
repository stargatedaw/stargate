#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "audiodsp/modules/oscillator/osc_simple.h"


/* void v_lfs_sync(
 * t_lfs_lfo * a_lfs,
 * SGFLT a_phase,  //the phase to resync to.  Range:  0 to .9999
 * int a_type)  //The type of LFO.  See types below
 *
 * Types:
 * 0 : Off
 * 1 : Sine
 * 2 : Triangle
 */
void v_lfs_sync(t_lfs_lfo * a_lfs, SGFLT a_phase, int a_type)
{
    a_lfs->osc_core.output = a_phase;

    switch(a_type)
    {
        case 0:
            a_lfs->osc_ptr = f_get_osc_off;
            break;
        case 1:
            a_lfs->osc_ptr = f_get_sine;
            break;
        case 2:
            a_lfs->osc_ptr = f_get_triangle;
            //So that it will be at 0 to begin with
            a_lfs->osc_core.output = 0.5f;
            break;
    }
}


/* void v_osc_set_hz(
 * t_lfs_lfo * a_lfs_ptr,
 * SGFLT a_hz)  //the pitch of the oscillator in hz, typically 0.1 to 10000
 *
 * For setting LFO frequency.
 */
void v_lfs_set(t_lfs_lfo * a_lfs_ptr, SGFLT a_hz)
{
    a_lfs_ptr->inc =  a_hz * a_lfs_ptr->sr_recip;
}

/* void v_lfs_run(t_lfs_lfo *)
 */
void v_lfs_run(t_lfs_lfo * a_lfs)
{
    v_run_osc(&a_lfs->osc_core, (a_lfs->inc));
    a_lfs->output = a_lfs->osc_ptr(&a_lfs->osc_core);
}

void g_lfs_init(t_lfs_lfo * f_result, SGFLT a_sr)
{
    f_result->inc = 0.0f;
    g_init_osc_core(&f_result->osc_core);
    f_result->osc_ptr = f_get_osc_off;
    f_result->output = 0.0f;
    f_result->sr = a_sr;
    f_result->sr_recip = 1.0f / a_sr;
}

t_lfs_lfo * g_lfs_get(SGFLT a_sr)
{
    t_lfs_lfo * f_result;
    lmalloc((void**)&f_result, sizeof(t_lfs_lfo));
    g_lfs_init(f_result, a_sr);
    return f_result;
}

void v_lfs_free(t_lfs_lfo * a_lfs)
{
    free(a_lfs);
}

