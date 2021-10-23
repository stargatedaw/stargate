#include "audiodsp/modules/distortion/clipper.h"


/*v_clp_set_clip_sym(
 * t_clipper*,
 * SGFLT a_db //Threshold to clip at, in decibel,
 * ie:  -6db = clipping at .5 and -.5
 * )
 */
void v_clp_set_clip_sym(t_clipper * a_clp, SGFLT a_db){
    /*Already set, don't set again*/
    if(a_db == (a_clp->clip_db))
        return;

    a_clp->clip_db = a_db;

    SGFLT f_value = f_db_to_linear_fast(a_db);

#ifdef CLP_DEBUG_MODE
        log_info("Clipper value == %f", f_value);
#endif

    a_clp->clip_high = f_value;
    a_clp->clip_low = (f_value * -1.0f);
}

/*void v_clp_set_in_gain(
 * t_clipper*,
 * SGFLT a_db   //gain in dB to apply to the input signal before clipping it,
 * usually a value between 0 and 36
 * )
 */
void v_clp_set_in_gain(t_clipper * a_clp, SGFLT a_db)
{
    if((a_clp->in_db) != a_db)
    {
        a_clp->in_db = a_db;
        a_clp->input_gain_linear = f_db_to_linear(a_db);
    }
}

void g_clp_init(t_clipper * f_result)
{
    f_result->clip_high = 1.0f;
    f_result->clip_low = -1.0f;
    f_result->input_gain_linear = 1.0f;
    f_result->in_db = 0.0f;
    f_result->result = 0.0f;
    f_result->clip_db = 7654567.0f;
}

t_clipper * g_clp_get_clipper()
{
    t_clipper * f_result;

    lmalloc((void**)&f_result, sizeof(t_clipper));
    g_clp_init(f_result);
    return f_result;
};

/* SGFLT f_clp_clip(
 * t_clipper *,
 * SGFLT a_input  //value to be clipped
 * )
 *
 * This function performs the actual clipping, and returns a SGFLT
 */
SGFLT f_clp_clip(t_clipper * a_clp, SGFLT a_input)
{
    a_clp->result = a_input * (a_clp->input_gain_linear);

    if(a_clp->result > (a_clp->clip_high))
        a_clp->result = (a_clp->clip_high);
    else if(a_clp->result < (a_clp->clip_low))
        a_clp->result = (a_clp->clip_low);

    return (a_clp->result);
}


void v_clp_free(t_clipper * a_clp)
{
    free(a_clp);
}
