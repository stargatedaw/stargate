#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/smoother-iir.h"


/* void v_smr_iir_run(
 * t_smoother_iir *
 * a_smoother, SGFLT a_in)  //The input to be smoothed
 *
 * Use t_smoother_iir->output as your new control value after running this
 */
void v_smr_iir_run(t_smoother_iir * a_smoother, SGFLT a_in)
{
    a_smoother->output =
            f_remove_denormal((a_in * 0.01f) + ((a_smoother->output) * 0.99f));
}

/* void v_smr_iir_run_fast(
 * t_smoother_iir *
 * a_smoother, SGFLT a_in)  //The input to be smoothed
 *
 * Use t_smoother_iir->output as your new control value after running this
 */
void v_smr_iir_run_fast(t_smoother_iir * a_smoother, SGFLT a_in)
{
    a_smoother->output =
            f_remove_denormal((a_in * .2f) + ((a_smoother->output) * .8f));
}

t_smoother_iir * g_smr_iir_get_smoother();

t_smoother_iir * g_smr_iir_get_smoother()
{
    t_smoother_iir * f_result;

    lmalloc((void**)&f_result, sizeof(t_smoother_iir));

    f_result->output = 0.0f;
    return f_result;
}

