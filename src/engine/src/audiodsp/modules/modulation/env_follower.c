#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/filter/one_pole.h"
#include "audiodsp/modules/modulation/adsr.h"
#include "audiodsp/modules/modulation/env_follower.h"


/* void v_enf_run_env_follower(
 * t_enf_env_follower * a_enf,
 * SGFLT a_input)  //the signal to follow
 */
void v_enf_run_env_follower(t_enf_env_follower * a_enf, SGFLT a_input){
    //Get absolute value.  This is much faster than fabs
    if(a_input < 0)
    {
        a_enf->input = a_input * -1;
    }
    else
    {
        a_enf->input = a_input;
    }

    v_opl_run(a_enf->smoother, (a_enf->input));

    /*TODO:  Test the fast l2db function here*/
    a_enf->output_smoothed = f_linear_to_db_fast((a_enf->smoother->output));

#ifdef ENF_DEBUG_MODE
    a_enf->debug_counter = (a_enf->debug_counter) + 1;

    if((a_enf->debug_counter) >= 100000)
    {
        a_enf->debug_counter = 0;

        log_info("Env Follower info:");
        log_info("a_enf->input == %f", a_enf->input);
        log_info("a_enf->output_smoothed == %f", a_enf->output_smoothed);
    }
#endif
}

void env_follower_init(t_enf_env_follower* self, SGFLT a_sr){
    self->input = 0;
    self->output_smoothed = 0;
    self->smoother = g_opl_get_one_pole(a_sr);

    // Set the smoother to 10hz.  The reciprocal of the hz value is the
    // total smoother time
    v_opl_set_coeff_hz(self->smoother, 10);

#ifdef ENF_DEBUG_MODE
    self->debug_counter = 0;
#endif
}

/* t_enf_env_follower * g_enf_get_env_follower(
 * SGFLT a_sr //sample rate
 * )
 */
t_enf_env_follower * g_enf_get_env_follower(SGFLT a_sr){
    t_enf_env_follower * self = (t_enf_env_follower*)malloc(
        sizeof(t_enf_env_follower)
    );
    env_follower_init(self, a_sr);

    return self;
}

