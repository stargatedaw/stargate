#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/constants.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/denormal.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/filter/svf_stereo.h"


void v_svf2_reset(t_svf2_filter * a_svf2)
{
    int i;
    for(i = 0; i < SVF_MAX_CASCADE; ++i)
    {
        a_svf2->filter_kernels[i][0].bp = 0.0f;
        a_svf2->filter_kernels[i][0].bp_m1 = 0.0f;
        a_svf2->filter_kernels[i][0].filter_input = 0.0f;
        a_svf2->filter_kernels[i][0].filter_last_input = 0.0f;
        a_svf2->filter_kernels[i][0].hp = 0.0f;
        a_svf2->filter_kernels[i][0].lp = 0.0f;
        a_svf2->filter_kernels[i][0].lp_m1 = 0.0f;

        a_svf2->filter_kernels[i][1].bp = 0.0f;
        a_svf2->filter_kernels[i][1].bp_m1 = 0.0f;
        a_svf2->filter_kernels[i][1].filter_input = 0.0f;
        a_svf2->filter_kernels[i][1].filter_last_input = 0.0f;
        a_svf2->filter_kernels[i][1].hp = 0.0f;
        a_svf2->filter_kernels[i][1].lp = 0.0f;
        a_svf2->filter_kernels[i][1].lp_m1 = 0.0f;
    }
}


/* void v_svf2_run_no_filter(
 * t_svf2_filter* a_svf,
 * SGFLT a_in) //audio input
 *
 * This is for allowing a filter to be turned off by running a
 * function pointer.  a_in is returned unmodified.
 */
void v_svf2_run_no_filter(
    t_svf2_filter* a_svf,
    SGFLT a_in0,
    SGFLT a_in1
){
    a_svf->output0 = a_in0;
    a_svf->output1 = a_in1;
}

void g_svf2_filter_kernel_init(t_svf2_kernel * f_result)
{
    f_result->bp = 0.0f;
    f_result->hp = 0.0f;
    f_result->lp = 0.0f;
    f_result->lp_m1 = 0.0f;
    f_result->filter_input = 0.0f;
    f_result->filter_last_input = 0.0f;
    f_result->bp_m1 = 0.0f;
}

/* Return a function pointer to run a filter
 * a_cascades:    The number of filters to cascade, or poles/2, ie 2poles==1
 * a_filter_type: The SVF_FILTER_TYPE_?? you wish to return
 */
fp_svf2_run_filter fp_svf2_get_run_filter_ptr(
    int a_cascades,
    int a_filter_type
){
    /*Lowpass*/
    if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_LP))
    {
        return v_svf2_run_2_pole_lp;
    }
    else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_LP))
    {
        return v_svf2_run_4_pole_lp;
    }
    /*Highpass*/
    else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_HP))
    {
        return v_svf2_run_2_pole_hp;
    }
    else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_HP))
    {
        return v_svf2_run_4_pole_hp;
    }
    /*Bandpass*/
    else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_BP))
    {
        return v_svf2_run_2_pole_bp;
    }
    else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_BP))
    {
        return v_svf2_run_4_pole_bp;
    }
    /*Notch*/
    else if((a_cascades == 1) && (a_filter_type == SVF_FILTER_TYPE_NOTCH))
    {
        return v_svf2_run_2_pole_notch;
    }
    else if((a_cascades == 2) && (a_filter_type == SVF_FILTER_TYPE_NOTCH))
    {
        return v_svf2_run_4_pole_notch;
    }
    /*Sane-ish default...*/
    else
    {
        return v_svf2_run_2_pole_lp;
    }
}

/* void v_svf2_run(
 * t_svf2_filter * a_svf,
 * t_svf2_kernel * a_kernel,
 * SGFLT a_input_value) //the audio input to filter
 *
 * The main action to run the filter kernel*/
void v_svf2_run(
    t_svf2_filter * a_svf,
    t_svf2_kernel * a_kernel,
    SGFLT a_input_value
){
    SGFLT oversample_iterator = 0.0f;
    int f_i;

    a_kernel->filter_input = a_input_value;

    for(f_i = 0; f_i < 4; ++f_i)
    {
        a_kernel->hp = f_linear_interpolate(
            a_kernel->filter_last_input,
            a_kernel->filter_input, oversample_iterator
        ) - ((a_kernel->bp_m1 * a_svf->filter_res) + a_kernel->lp_m1);
        a_kernel->bp = (a_kernel->hp * a_svf->cutoff_filter) + a_kernel->bp_m1;
        a_kernel->lp = (a_kernel->bp * a_svf->cutoff_filter) + a_kernel->lp_m1;

        oversample_iterator += SVF_OVERSAMPLE_STEP_SIZE;
    }

    a_kernel->bp_m1 = f_remove_denormal(a_kernel->bp);
    a_kernel->lp_m1 = f_remove_denormal(a_kernel->lp);
    a_kernel->filter_last_input = a_input_value;
}

void v_svf2_run_2_pole_lp(
    t_svf2_filter* a_svf,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    a_svf->output0 = a_svf->filter_kernels[0][0].lp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );
    a_svf->output1 = a_svf->filter_kernels[0][1].lp;
}

void v_svf2_run_4_pole_lp(
    t_svf2_filter* a_svf,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][0],
        a_svf->filter_kernels[0][0].lp
    );
    a_svf->output0 = a_svf->filter_kernels[1][0].lp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][1],
        a_svf->filter_kernels[0][1].lp
    );
    a_svf->output1 = a_svf->filter_kernels[1][1].lp;
}

void v_svf2_run_2_pole_hp(
    t_svf2_filter* a_svf,
    SGFLT a_in0,
    SGFLT a_in1
){
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    a_svf->output0 = a_svf->filter_kernels[0][0].hp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );
    a_svf->output1 = a_svf->filter_kernels[0][1].hp;
}

void v_svf2_run_4_pole_hp(t_svf2_filter* a_svf,
        SGFLT a_in0, SGFLT a_in1)
{
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][0],
        a_svf->filter_kernels[0][0].hp
    );
    a_svf->output0 = a_svf->filter_kernels[1][0].hp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][1],
        a_svf->filter_kernels[0][1].hp
    );
    a_svf->output1 = a_svf->filter_kernels[1][1].hp;
}

void v_svf2_run_2_pole_bp(t_svf2_filter* a_svf,
        SGFLT a_in0, SGFLT a_in1)
{
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    a_svf->output0 = a_svf->filter_kernels[0][0].bp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );
    a_svf->output1 = a_svf->filter_kernels[0][1].bp;
}

void v_svf2_run_4_pole_bp(t_svf2_filter* a_svf,
        SGFLT a_in0, SGFLT a_in1)
{
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][0],
        a_svf->filter_kernels[0][0].bp
    );
    a_svf->output0 = a_svf->filter_kernels[1][0].bp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][1],
        a_svf->filter_kernels[0][1].bp
    );
    a_svf->output1 = a_svf->filter_kernels[1][1].bp;
}

void v_svf2_run_2_pole_notch(t_svf2_filter* a_svf,
        SGFLT a_in0, SGFLT a_in1)
{
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    a_svf->output0 =
        a_svf->filter_kernels[0][0].hp +
        a_svf->filter_kernels[0][0].lp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );
    a_svf->output1 =
        a_svf->filter_kernels[0][1].hp +
        a_svf->filter_kernels[0][1].lp;
}

void v_svf2_run_4_pole_notch(t_svf2_filter* a_svf,
        SGFLT a_in0, SGFLT a_in1)
{
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][0],
        a_in0
    );
    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[0][1],
        a_in1
    );

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][0],
        a_svf->filter_kernels[0][0].hp + a_svf->filter_kernels[0][0].lp
    );
    a_svf->output0 =
        a_svf->filter_kernels[1][0].hp +
        a_svf->filter_kernels[1][0].lp;

    v_svf2_run(
        a_svf,
        &a_svf->filter_kernels[1][1],
        a_svf->filter_kernels[0][0].hp + a_svf->filter_kernels[0][1].lp
    );
    a_svf->output1 =
        a_svf->filter_kernels[1][1].hp +
        a_svf->filter_kernels[1][1].lp;
}

void v_svf2_run_2_pole_allpass(t_svf2_filter* a_svf,
        SGFLT a_in0, SGFLT a_in1)
{
    v_svf2_run(a_svf, &a_svf->filter_kernels[0][0], a_in0);
    a_svf->output0 = (a_svf->filter_kernels[0][0].hp) +
            (a_svf->filter_kernels[0][0].lp) +
            (a_svf->filter_kernels[0][0].bp);

    v_svf2_run(a_svf, &a_svf->filter_kernels[0][1], a_in1);
    a_svf->output1 = (a_svf->filter_kernels[0][1].hp) +
            (a_svf->filter_kernels[0][1].lp) +
            (a_svf->filter_kernels[0][1].bp);
}

/* void v_svf2_velocity_mod(t_svf2_filter* a_svf, SGFLT a_velocity)
 */
void v_svf2_velocity_mod(
    t_svf2_filter* a_svf,
    SGFLT a_velocity
){
    a_svf->velocity_cutoff = ((a_velocity) * .2f) - 24.0f;
    a_svf->velocity_mod_amt = a_velocity * 0.007874016f;
}

/* void v_svf2_set_cutoff_base(t_svf2_filter* a_svf,
 * SGFLT a_midi_note_number)
 * Set the base pitch of the filter, this will usually correspond to a
 * single GUI knob*/
void v_svf2_set_cutoff_base(
    t_svf2_filter* a_svf,
    SGFLT a_midi_note_number
){
    a_svf->cutoff_base = a_midi_note_number;
}

/* void v_svf2_add_cutoff_mod(t_svf2_filter* a_svf,
 * SGFLT a_midi_note_number)
 * Modulate the filters cutoff with an envelope, LFO, etc...*/
void v_svf2_add_cutoff_mod(t_svf2_filter* a_svf,
        SGFLT a_midi_note_number)
{
    a_svf->cutoff_mod = (a_svf->cutoff_mod) + a_midi_note_number;
}

/* void v_svf2_set_cutoff(t_svf2_filter * a_svf)
 * This should be called every sample, otherwise the smoothing and
 * modulation doesn't work properly*/
void v_svf2_set_cutoff(t_svf2_filter * a_svf){
    a_svf->cutoff_note = (a_svf->cutoff_base) + ((a_svf->cutoff_mod) *
            (a_svf->velocity_mod_amt)) + (a_svf->velocity_cutoff);
    a_svf->cutoff_mod = 0.0f;

    /*It hasn't changed since last time, return*/
    if((a_svf->cutoff_note) == (a_svf->cutoff_last))
        return;

    a_svf->cutoff_last = (a_svf->cutoff_note);

    v_svf2_set_cutoff_hz(
        a_svf,
        f_pit_midi_note_to_hz_fast((a_svf->cutoff_note))
    );

}

void v_svf2_set_cutoff_hz(t_svf2_filter * a_svf, SGFLT hz){
    a_svf->cutoff_hz = hz;
    //_svf->cutoff_smoother->last_value);

    a_svf->cutoff_filter = (a_svf->pi2_div_sr) * (a_svf->cutoff_hz) * 4.0f;

    /*prevent the filter from exploding numerically,
     * this does artificially cap the cutoff frequency to below
     * what you set it to if you lower the oversampling rate of the filter.*/
    if((a_svf->cutoff_filter) > 0.8f){
        a_svf->cutoff_filter = 0.8f;
    }
}

/* void v_svf2_set_res(
 * t_svf2_filter * a_svf,
 * SGFLT a_db)   //-100 to 0 is the expected range
 *
 */
void v_svf2_set_res(t_svf2_filter * a_svf, SGFLT a_db){
    /*Don't calculate it again if it hasn't changed*/
    if((a_svf->filter_res_db) == a_db){
        return;
    }
    a_svf->filter_res_db = a_db;

    if(a_db < -100.0f){
        a_db = -100.0f;
    } else if (a_db > -0.2f){
        a_db = -0.2f;
    }

    a_svf->filter_res = (1.0f - (f_db_to_linear_fast(a_db))) * 2.0f;
}

void g_svf2_init(t_svf2_filter * f_svf, SGFLT a_sample_rate){
    int i;
    f_svf->sr = a_sample_rate * ((SGFLT)(SVF_OVERSAMPLE_MULTIPLIER));
    f_svf->pi2_div_sr = (PI2 / (f_svf->sr));

    for(i = 0; i < SVF_MAX_CASCADE; ++i){
        g_svf2_filter_kernel_init(&f_svf->filter_kernels[i][0]);
        g_svf2_filter_kernel_init(&f_svf->filter_kernels[i][1]);
    }

    f_svf->cutoff_note = 60.0f;
    f_svf->cutoff_hz = 1000.0f;
    f_svf->cutoff_filter = 0.7f;
    f_svf->filter_res = 0.25f;
    f_svf->filter_res_db = -12.0f;

    f_svf->cutoff_base = 78.0f;
    f_svf->cutoff_mod = 0.0f;
    f_svf->cutoff_last = 81.0f;
    f_svf->filter_res_db = -21.0f;
    f_svf->filter_res = 0.5f;
    f_svf->velocity_cutoff = 0.0f;
    f_svf->velocity_mod_amt = 1.0f;

    v_svf2_set_cutoff_base(f_svf, 75.0f);
    v_svf2_add_cutoff_mod(f_svf, 0.0f);
    v_svf2_set_res(f_svf, -12.0f);
    v_svf2_set_cutoff(f_svf);
}

