
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/modules/filter/nosvf.h"

void v_nosvf_reset(t_nosvf_filter * a_svf)
{
    int f_i = 0;
    while(f_i < NOSVF_MAX_CASCADE)
    {
        a_svf->filter_kernels[f_i].bp = 0.0f;
        a_svf->filter_kernels[f_i].bp_m1 = 0.0f;
        a_svf->filter_kernels[f_i].hp = 0.0f;
        a_svf->filter_kernels[f_i].lp = 0.0f;
        a_svf->filter_kernels[f_i].lp_m1 = 0.0f;
        ++f_i;
    }
}

SG_THREAD_LOCAL fp_nosvf_run_filter NOSVF_TYPES[9] = {
    v_nosvf_run_2_pole_lp,
    v_nosvf_run_4_pole_lp,
    v_nosvf_run_2_pole_hp,
    v_nosvf_run_4_pole_hp,
    v_nosvf_run_2_pole_bp,
    v_nosvf_run_4_pole_bp,
    v_nosvf_run_2_pole_notch,
    v_nosvf_run_4_pole_notch,
    v_nosvf_run_no_filter
};

/* SGFLT v_nosvf_run_no_filter(
 * t_nosvf_filter* a_svf,
 * SGFLT a_in) //audio input
 *
 * This is for allowing a filter to be turned off by running a
 * function pointer.  a_in is returned unmodified.
 */
SGFLT v_nosvf_run_no_filter(
    t_nosvf_filter* a_svf,
    SGFLT a_in
){
    return a_in;
}

void v_nosvf_set_eq(t_nosvf_filter* a_svf, SGFLT a_gain){
    if(a_gain != (a_svf->gain_db)){
        a_svf->gain_db = a_gain;
        a_svf->gain_linear = f_db_to_linear_fast(a_gain);
    }
}

void v_nosvf_set_eq4(
    t_nosvf_filter* a_svf,
    SGFLT a_gain
){
    if(a_gain != a_svf->gain_db){
        a_svf->gain_db = a_gain;
        a_svf->gain_linear = f_db_to_linear_fast(a_gain * .05);
    }
}

void g_nosvf_filter_kernel_init(t_nosvf_kernel * f_result){
    f_result->bp = 0.0f;
    f_result->hp = 0.0f;
    f_result->lp = 0.0f;
    f_result->lp_m1 = 0.0f;
    f_result->bp_m1 = 0.0f;
}

/* fp_nosvf_run_filter nosvf_get_run_filter_ptr(
 * int a_cascades,
 * int a_filter_type)
 *
 * The int refers to the number of cascaded filter kernels,
 * ie:  a value of 2 == 4 pole filter
 *
 * Filter types:
 *
 * NOSVF_FILTER_TYPE_LP 0
 * NOSVF_FILTER_TYPE_HP 1
 * NOSVF_FILTER_TYPE_BP 2
 */
fp_nosvf_run_filter nosvf_get_run_filter_ptr(
    int a_cascades,
    int a_filter_type
){
    /*Lowpass*/
    if(
        a_cascades == 1
        &&
        a_filter_type == NOSVF_FILTER_TYPE_LP
    ){
        return v_nosvf_run_2_pole_lp;
    } else if(
        a_cascades == 2
        &&
        a_filter_type == NOSVF_FILTER_TYPE_LP
    ){
        return v_nosvf_run_4_pole_lp;
    } else if(
        a_cascades == 1
        &&
        a_filter_type == NOSVF_FILTER_TYPE_HP
    ){
        return v_nosvf_run_2_pole_hp;
    } else if(
        a_cascades == 2
        &&
        a_filter_type == NOSVF_FILTER_TYPE_HP
    ){
        return v_nosvf_run_4_pole_hp;
    } else if(
        a_cascades == 1
        &&
        a_filter_type == NOSVF_FILTER_TYPE_BP
    ){
        return v_nosvf_run_2_pole_bp;
    } else if(
        a_cascades == 2
        &&
        a_filter_type == NOSVF_FILTER_TYPE_BP
    ){
        return v_nosvf_run_4_pole_bp;
    } else if(
        a_cascades == 1
        &&
        a_filter_type == NOSVF_FILTER_TYPE_NOTCH
    ){
        return v_nosvf_run_2_pole_notch;
    } else if(
        a_cascades == 2
        &&
        a_filter_type == NOSVF_FILTER_TYPE_NOTCH
    ){
        return v_nosvf_run_4_pole_notch;
    } else if(
        a_cascades == 1
        &&
        a_filter_type == NOSVF_FILTER_TYPE_EQ
    ){
        return v_nosvf_run_2_pole_eq;
    } else if(
        a_cascades == 2
        &&
        a_filter_type == NOSVF_FILTER_TYPE_EQ
    ){
        return v_nosvf_run_4_pole_eq;
    } else {
        // This means that you entered invalid settings
        return v_nosvf_run_2_pole_lp;
    }
}

/* void v_nosvf_set_input_value(
 * t_nosvf_filter * a_svf,
 * t_nosvf_kernel * a_kernel,
 * SGFLT a_input_value) //the audio input to filter
 *
 * The main action to run the filter kernel*/
void v_nosvf_set_input_value(
    t_nosvf_filter* a_svf,
    t_nosvf_kernel* a_kernel,
    SGFLT a_input_value
){
    a_kernel->hp = a_input_value -
        (((a_kernel->bp_m1) * (a_svf->filter_res)) + (a_kernel->lp_m1));
    a_kernel->bp = ((a_kernel->hp) * (a_svf->cutoff_filter)) +
            (a_kernel->bp_m1);
    a_kernel->lp = ((a_kernel->bp) * (a_svf->cutoff_filter)) +
            (a_kernel->lp_m1);

    a_kernel->bp_m1 = f_remove_denormal((a_kernel->bp));
    a_kernel->lp_m1 = f_remove_denormal((a_kernel->lp));
}

SGFLT v_nosvf_run_2_pole_lp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].lp);
}


SGFLT v_nosvf_run_4_pole_lp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].lp
    );

    return (a_svf->filter_kernels[1].lp);
}

SGFLT v_nosvf_run_6_pole_lp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].lp
    );
    v_nosvf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[2],
        a_svf->filter_kernels[1].lp
    );

    return a_svf->filter_kernels[2].lp;
}

SGFLT v_nosvf_run_2_pole_hp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    return (a_svf->filter_kernels[0].hp);
}


SGFLT v_nosvf_run_4_pole_hp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].hp
    );

    return (a_svf->filter_kernels[1].hp);
}


SGFLT v_nosvf_run_2_pole_bp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].bp);
}

SGFLT v_nosvf_run_4_pole_bp(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].bp
    );

    return (a_svf->filter_kernels[1].bp);
}

SGFLT v_nosvf_run_2_pole_notch(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp);
}

SGFLT v_nosvf_run_4_pole_notch(
    t_nosvf_filter* a_svf,
    SGFLT a_input
){
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    v_nosvf_set_input_value(
        a_svf,
        &a_svf->filter_kernels[1],
        a_svf->filter_kernels[0].hp + a_svf->filter_kernels[0].lp
    );

    return (a_svf->filter_kernels[1].hp) + (a_svf->filter_kernels[1].lp);
}

SGFLT v_nosvf_run_2_pole_allpass(t_nosvf_filter* a_svf,
        SGFLT a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp) +
            (a_svf->filter_kernels[0].bp);
}

SGFLT v_nosvf_run_2_pole_eq(t_nosvf_filter* a_svf,
        SGFLT a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (((a_svf->filter_kernels[0].lp) + (a_svf->filter_kernels[0].hp)) +
            ((a_svf->filter_kernels[0].bp) * (a_svf->gain_linear)));
}


SGFLT v_nosvf_run_4_pole_eq(t_nosvf_filter* a_svf,
        SGFLT a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
            (((a_svf->filter_kernels[0].lp) + (a_svf->filter_kernels[0].hp)) +
            ((a_svf->filter_kernels[0].bp) * (a_svf->gain_linear))));

    return (((a_svf->filter_kernels[1].lp) + (a_svf->filter_kernels[1].hp)) +
            ((a_svf->filter_kernels[1].bp) * (a_svf->gain_linear)));
}

/* void v_nosvf_velocity_mod(t_nosvf_filter* a_svf, SGFLT a_velocity)
 */
void v_nosvf_velocity_mod(
    t_nosvf_filter* a_svf,
    SGFLT a_velocity,
    SGFLT a_amt
){
    a_velocity *= 0.007874016f;
    a_svf->velocity_cutoff = ((a_velocity * 24.0f) - 24.0f) * a_amt;
}

/* void v_nosvf_set_cutoff_base(
 * t_nosvf_filter* a_svf, SGFLT a_midi_note_number)
 * Set the base pitch of the filter*/
void v_nosvf_set_cutoff_base(
    t_nosvf_filter* a_svf,
    SGFLT a_midi_note_number
){
    a_svf->cutoff_base = a_midi_note_number;
}

/* void v_nosvf_add_cutoff_mod(
 * t_nosvf_filter* a_svf, SGFLT a_midi_note_number)
 * Modulate the filters cutoff with an envelope, LFO, etc...*/
void v_nosvf_add_cutoff_mod(t_nosvf_filter* a_svf,
        SGFLT a_midi_note_number)
{
    a_svf->cutoff_mod = (a_svf->cutoff_mod) + a_midi_note_number;
}

/* void v_nosvf_set_cutoff(t_nosvf_filter * a_svf)
 * This should be called every sample, otherwise the smoothing and
 * modulation doesn't work properly*/
void v_nosvf_set_cutoff(t_nosvf_filter * a_svf)
{
    a_svf->cutoff_note = a_svf->cutoff_base + a_svf->cutoff_mod  +
        a_svf->velocity_cutoff;
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

    a_svf->cutoff_filter = (a_svf->pi2_div_sr) * (a_svf->cutoff_hz);

    /*prevent the filter from exploding numerically,
     * this does artificially cap the cutoff frequency to below what you
     * set it to if you lower the oversampling rate of the filter.*/
    if((a_svf->cutoff_filter) > 0.8f)
        a_svf->cutoff_filter = 0.8f;
}

/* void v_nosvf_set_res(
 * t_nosvf_filter * a_svf,
 * SGFLT a_db)   //-100 to 0 is the expected range
 *
 */
void v_nosvf_set_res(t_nosvf_filter * a_svf, SGFLT a_db)
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

void g_nosvf_init(t_nosvf_filter * f_svf, SGFLT a_sample_rate){
    f_svf->sr = a_sample_rate;
    f_svf->pi2_div_sr = (PI2 / (f_svf->sr));

    int f_i;

    for(f_i = 0; f_i < NOSVF_MAX_CASCADE; ++f_i){
        g_nosvf_filter_kernel_init(&f_svf->filter_kernels[f_i]);
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

    f_svf->gain_db = 0.0f;
    f_svf->gain_linear = 1.0f;

    v_nosvf_set_cutoff_base(f_svf, 75.0f);
    v_nosvf_add_cutoff_mod(f_svf, 0.0f);
    v_nosvf_set_res(f_svf, -12.0f);
    v_nosvf_set_cutoff(f_svf);
}

/* t_nosvf_filter * g_nosvf_get(SGFLT a_sample_rate)
 */
t_nosvf_filter * g_nosvf_get(SGFLT a_sample_rate)
{
    t_nosvf_filter * f_svf;
    lmalloc((void**)&f_svf, sizeof(t_nosvf_filter));
    g_nosvf_init(f_svf, a_sample_rate);
    return f_svf;
}

