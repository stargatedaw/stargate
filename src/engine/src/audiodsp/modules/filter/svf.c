#include "audiodsp/constants.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/modules/filter/svf.h"


void v_svf_reset(t_state_variable_filter * a_svf){
    int f_i;
    for(f_i = 0; f_i < SVF_MAX_CASCADE; ++f_i){
        a_svf->filter_kernels[f_i].bp = 0.0f;
        a_svf->filter_kernels[f_i].bp_m1 = 0.0f;
        a_svf->filter_kernels[f_i].filter_input = 0.0f;
        a_svf->filter_kernels[f_i].filter_last_input = 0.0f;
        a_svf->filter_kernels[f_i].hp = 0.0f;
        a_svf->filter_kernels[f_i].lp = 0.0f;
        a_svf->filter_kernels[f_i].lp_m1 = 0.0f;
    }
}

void v_svf_set_output(t_state_variable_filter * a_svf, SGFLT value){
    int f_i;
    SGFLT output;
    for(f_i = 0; f_i < SVF_MAX_CASCADE; ++f_i){
        a_svf->filter_kernels[f_i].bp = value;
        a_svf->filter_kernels[f_i].bp_m1 = value;
        a_svf->filter_kernels[f_i].filter_input = value;
        a_svf->filter_kernels[f_i].filter_last_input = value;
        a_svf->filter_kernels[f_i].hp = value;
        a_svf->filter_kernels[f_i].lp = value;
        a_svf->filter_kernels[f_i].lp_m1 = value;
    }
    for(f_i = 0; f_i < 10; ++f_i){
        output = v_svf_run_2_pole_lp(a_svf, value);
        if(output == value){
            break;
        }
    }
}

/* SGFLT v_svf_run_no_filter(
 * t_state_variable_filter* a_svf,
 * SGFLT a_in) //audio input
 *
 * This is for allowing a filter to be turned off by running a
 * function pointer.  a_in is returned unmodified.
 */
SGFLT v_svf_run_no_filter(
    t_state_variable_filter* a_svf,
    SGFLT a_in
){
    return a_in;
}

void v_svf_set_eq(t_state_variable_filter* a_svf, SGFLT a_gain){
    if(a_gain != (a_svf->gain_db)){
        a_svf->gain_db = a_gain;
        a_svf->gain_linear = f_db_to_linear_fast(a_gain);
    }
}

void v_svf_set_eq4(
    t_state_variable_filter* a_svf,
    SGFLT a_gain
){
    if(a_gain != a_svf->gain_db){
        a_svf->gain_db = a_gain;
        a_svf->gain_linear = f_db_to_linear_fast((a_gain * .05));
    }
}

void g_svf_filter_kernel_init(t_svf_kernel * f_result){
    f_result->bp = 0.0f;
    f_result->hp = 0.0f;
    f_result->lp = 0.0f;
    f_result->lp_m1 = 0.0f;
    f_result->filter_input = 0.0f;
    f_result->filter_last_input = 0.0f;
    f_result->bp_m1 = 0.0f;
}

/* fp_svf_run_filter svf_get_run_filter_ptr(
 * int a_cascades,
 * int a_filter_type)
 *
 * The int refers to the number of cascaded filter kernels,
 * ie:  a value of 2 == 4 pole filter
 *
 * Filter types:
 *
 * SVF_FILTER_TYPE_LP 0
 * SVF_FILTER_TYPE_HP 1
 * SVF_FILTER_TYPE_BP 2
 */
fp_svf_run_filter svf_get_run_filter_ptr(int a_cascades, int a_filter_type){
    if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_LP)){
        return v_svf_run_2_pole_lp;
    } else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_LP)){
        return v_svf_run_4_pole_lp;
    } else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_HP)){
        return v_svf_run_2_pole_hp;
    } else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_HP)){
        return v_svf_run_4_pole_hp;
    } else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_BP)){
        return v_svf_run_2_pole_bp;
    } else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_BP)){
        return v_svf_run_4_pole_bp;
    } else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_NOTCH)){
        return v_svf_run_2_pole_notch;
    } else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_NOTCH)){
        return v_svf_run_4_pole_notch;
    } else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_EQ)){
        return v_svf_run_2_pole_eq;
    } else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_EQ)){
        return v_svf_run_4_pole_eq;
    } else {
        // This means that you entered invalid settings
        return v_svf_run_2_pole_lp;
    }
}

/* void v_svf_set_input_value(
 * t_state_variable_filter * a_svf,
 * t_svf_kernel * a_kernel,
 * SGFLT a_input_value) //the audio input to filter
 *
 * The main action to run the filter kernel*/
void v_svf_set_input_value(
    t_state_variable_filter* a_svf,
    t_svf_kernel*  a_kernel,
    SGFLT a_input_value
){
    SGFLT oversample_iterator;

    a_kernel->filter_input = a_input_value;

    for(
        oversample_iterator = 0.0f;
        oversample_iterator < 1.0f;
        ++oversample_iterator
    ){
        a_kernel->hp = f_linear_interpolate(
            a_kernel->filter_last_input,
            a_input_value,
            oversample_iterator
        ) - ((a_kernel->bp_m1 * a_svf->filter_res) + a_kernel->lp_m1);
        a_kernel->bp = (a_kernel->hp * a_svf->cutoff_filter) + a_kernel->bp_m1;
        a_kernel->lp = (a_kernel->bp * a_svf->cutoff_filter) + a_kernel->lp_m1;

        oversample_iterator += SVF_OVERSAMPLE_STEP_SIZE;
    }

    a_kernel->bp_m1 = f_remove_denormal((a_kernel->bp));
    a_kernel->lp_m1 = f_remove_denormal((a_kernel->lp));

    a_kernel->filter_last_input = a_input_value;
}




SGFLT v_svf_run_2_pole_lp(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    return (a_svf->filter_kernels[0].lp);
}


SGFLT v_svf_run_4_pole_lp(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_svf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].lp
    );

    return (a_svf->filter_kernels[1].lp);
}

SGFLT v_svf_run_2_pole_hp(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    return (a_svf->filter_kernels[0].hp);
}


SGFLT v_svf_run_4_pole_hp(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_svf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].hp
    );

    return (a_svf->filter_kernels[1].hp);
}


SGFLT v_svf_run_2_pole_bp(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    return (a_svf->filter_kernels[0].bp);
}

SGFLT v_svf_run_4_pole_bp(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_svf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].bp
    );

    return (a_svf->filter_kernels[1].bp);
}

SGFLT v_svf_run_2_pole_notch(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    return (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp);
}

SGFLT v_svf_run_4_pole_notch(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    v_svf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].hp + a_svf->filter_kernels[0].lp
    );

    return (a_svf->filter_kernels[1].hp) + (a_svf->filter_kernels[1].lp);
}

SGFLT v_svf_run_2_pole_allpass(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp) +
            (a_svf->filter_kernels[0].bp);
}

SGFLT v_svf_run_2_pole_eq(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (((a_svf->filter_kernels[0].lp) + (a_svf->filter_kernels[0].hp)) +
            ((a_svf->filter_kernels[0].bp) * (a_svf->gain_linear)));
}


SGFLT v_svf_run_4_pole_eq(
    t_state_variable_filter* a_svf,
    SGFLT a_input
){
    v_svf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_svf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        (
            (a_svf->filter_kernels[0].lp + a_svf->filter_kernels[0].hp) +
            (a_svf->filter_kernels[0].bp * a_svf->gain_linear)
        )
    );

    return (
        (a_svf->filter_kernels[1].lp + a_svf->filter_kernels[1].hp) +
        (a_svf->filter_kernels[1].bp * a_svf->gain_linear)
    );
}

/* void v_svf_velocity_mod(t_state_variable_filter* a_svf, SGFLT a_velocity)
 */
void v_svf_velocity_mod(
    t_state_variable_filter* a_svf,
    SGFLT a_velocity
){
    a_svf->velocity_cutoff = ((a_velocity) * .2f) - 24.0f;
    a_svf->velocity_mod_amt = a_velocity * 0.007874016f;
}

/* void v_svf_set_cutoff_base(
 * t_state_variable_filter* a_svf, SGFLT a_midi_note_number)
 * Set the base pitch of the filter*/
void v_svf_set_cutoff_base(
    t_state_variable_filter* a_svf,
    SGFLT a_midi_note_number
){
    a_svf->cutoff_base = a_midi_note_number;
}

/* void v_svf_add_cutoff_mod(
 * t_state_variable_filter* a_svf, SGFLT a_midi_note_number)
 * Modulate the filters cutoff with an envelope, LFO, etc...*/
void v_svf_add_cutoff_mod(t_state_variable_filter* a_svf, SGFLT a_midi_note_number)
{
    a_svf->cutoff_mod = (a_svf->cutoff_mod) + a_midi_note_number;
}

/* void v_svf_set_cutoff(t_state_variable_filter * a_svf)
 * This should be called every sample, otherwise the smoothing and
 * modulation doesn't work properly*/
void v_svf_set_cutoff(t_state_variable_filter * a_svf)
{
    a_svf->cutoff_note = (a_svf->cutoff_base) + ((a_svf->cutoff_mod) *
            (a_svf->velocity_mod_amt)) + (a_svf->velocity_cutoff);
    a_svf->cutoff_mod = 0.0f;

    if(a_svf->cutoff_note > 123.9209f)  //21000hz
    {
        a_svf->cutoff_note = 123.9209f;
    }

    /*It hasn't changed since last time, return*/
    if((a_svf->cutoff_note) == (a_svf->cutoff_last))
        return;

    a_svf->cutoff_last = (a_svf->cutoff_note);

    a_svf->cutoff_hz = f_pit_midi_note_to_hz_fast(a_svf->cutoff_note);
    //_svf->cutoff_smoother->last_value);

    a_svf->cutoff_filter = (a_svf->pi2_div_sr) * (a_svf->cutoff_hz) * 4.0f;

    /*prevent the filter from exploding numerically,
     * this does artificially cap the cutoff frequency to below what you
     * set it to if you lower the oversampling rate of the filter.*/
    if((a_svf->cutoff_filter) > 0.8f)
        a_svf->cutoff_filter = 0.8f;
}

/* void v_svf_set_res(
 * t_state_variable_filter * a_svf,
 * SGFLT a_db)   //-100 to 0 is the expected range
 *
 */
void v_svf_set_res(t_state_variable_filter * a_svf, SGFLT a_db)
{
    /*Don't calculate it again if it hasn't changed*/
    if((a_svf->filter_res_db) == a_db)
    {
        return;
    }

    a_svf->filter_res_db = a_db;

    if(a_db < -100.0f)
    {
        a_db = -100.0f;
    }
    else if (a_db > -0.2f)
    {
        a_db = -0.2f;
    }

    a_svf->filter_res = (1.0f - (f_db_to_linear_fast(a_db))) * 2.0f;
}

void g_svf_init(t_state_variable_filter * f_svf, SGFLT a_sample_rate){
    int i;

    f_svf->sr = a_sample_rate * ((SGFLT)(SVF_OVERSAMPLE_MULTIPLIER));
    f_svf->pi2_div_sr = (PI2 / (f_svf->sr));

    for(i = 0; i < SVF_MAX_CASCADE; ++i){
        g_svf_filter_kernel_init(&f_svf->filter_kernels[i]);
    }

    f_svf->cutoff_note = 60.0f;
    f_svf->cutoff_hz = 1000.0f;
    f_svf->cutoff_filter = 0.7f;
    f_svf->filter_res = 0.25f;

    f_svf->cutoff_base = 78.0f;
    f_svf->cutoff_mod = 0.0f;
    f_svf->cutoff_last = 81.0f;
    f_svf->filter_res_db = -21023.0f;
    f_svf->filter_res = 0.5f;
    f_svf->velocity_cutoff = 0.0f;
    f_svf->velocity_mod_amt = 1.0f;

    f_svf->gain_db = 0.0f;
    f_svf->gain_linear = 1.0f;

    v_svf_set_cutoff_base(f_svf, 75.0f);
    v_svf_add_cutoff_mod(f_svf, 0.0f);
    v_svf_set_res(f_svf, -12.0f);
    v_svf_set_cutoff(f_svf);
}

/* t_state_variable_filter * g_svf_get(SGFLT a_sample_rate)
 */
t_state_variable_filter * g_svf_get(SGFLT a_sample_rate)
{
    t_state_variable_filter * f_svf;
    lmalloc((void**)&f_svf, sizeof(t_state_variable_filter));
    g_svf_init(f_svf, a_sample_rate);
    return f_svf;
}

