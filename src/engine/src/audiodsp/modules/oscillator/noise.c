#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/oscillator/noise.h"


fp_noise_func_ptr f_noise_func_ptr_arr[] = {
    f_run_noise_off,
    f_run_white_noise,
    f_run_pink_noise,
    f_run_noise_off
};

fp_noise_func_ptr fp_get_noise_func_ptr(int a_index){
    return f_noise_func_ptr_arr[a_index];
}

fp_noise_stereo FP_NOISE_STEREO[] = {
    noise_off_stereo_run,
    white_noise_mono_run,
    pink_noise_mono_run,
    white_noise_stereo_run,
    pink_noise_stereo_run,
};

fp_noise_stereo fp_noise_stereo_get(int a_index){
    return FP_NOISE_STEREO[a_index];
}

unsigned int seed_helper = 18;

void g_white_noise_init(t_white_noise * f_result, SGFLT a_sample_rate)
{
    int f_i;
    double f_rand_recip = 1.0 / (double)RAND_MAX;
    time_t f_clock = time(NULL);

    f_clock %= UINT32_MAX;
    srand((unsigned int)f_clock + (seed_helper));

    seed_helper *= 2;
    f_result->array_count = (int)(a_sample_rate);

    f_result->read_head = 0;

    hpalloc(
        (void**)&f_result->sample_array,
        sizeof(SGFLT) * f_result->array_count
    );

    f_result->b0 = f_result->b1 = f_result->b2 = f_result->b3 =
        f_result->b4 = f_result->b5 = f_result->b6 = 0.0f;

    for(f_i = 0; f_i < f_result->array_count; ++f_i){
        /*Mixing 3 random numbers together gives a more natural
         * sounding white noise, instead of a "brick" of noise,
         * as seen on an oscilloscope*/
        SGFLT f_sample1 = ((double)rand() * f_rand_recip) - 0.5f;
        SGFLT f_sample2 = ((double)rand() * f_rand_recip) - 0.5f;
        SGFLT f_sample3 = ((double)rand() * f_rand_recip) - 0.5f;

        f_result->sample_array[f_i] = (f_sample1 + f_sample2 + f_sample3) * .5f;
    }
}

/* SGFLT f_run_white_noise(t_white_noise * a_w_noise)
 *
 * returns a single sample of white noise
 */
SGFLT f_run_white_noise(t_white_noise * a_w_noise){
    ++a_w_noise->read_head;

    if((a_w_noise->read_head) >= (a_w_noise->array_count)){
        a_w_noise->read_head = 0;
    }

    return a_w_noise->sample_array[(a_w_noise->read_head)];
}

/* SGFLT f_run_pink_noise(t_white_noise * a_w_noise)
 *
 * returns a single sample of pink noise
 */
SGFLT f_run_pink_noise(t_white_noise * a_w_noise)
{
    ++a_w_noise->read_head;

    if((a_w_noise->read_head) >= (a_w_noise->array_count)){
        a_w_noise->read_head = 0;
    }

    SGFLT f_white = a_w_noise->sample_array[(a_w_noise->read_head)];

    (a_w_noise->b0) = 0.99886f * (a_w_noise->b0) + f_white * 0.0555179f;
    (a_w_noise->b1) = 0.99332f * (a_w_noise->b1) + f_white * 0.0750759f;
    (a_w_noise->b2) = 0.96900f * (a_w_noise->b2) + f_white * 0.1538520f;
    (a_w_noise->b3) = 0.86650f * (a_w_noise->b3) + f_white * 0.3104856f;
    (a_w_noise->b4) = 0.55000f * (a_w_noise->b4) + f_white * 0.5329522f;
    (a_w_noise->b5) = -0.7616f * (a_w_noise->b5) - f_white * 0.0168980f;
    (a_w_noise->b6) = f_white * 0.115926f;
    return (a_w_noise->b0) + (a_w_noise->b1) + (a_w_noise->b2)
        + (a_w_noise->b3) + (a_w_noise->b4) + (a_w_noise->b5)
        + (a_w_noise->b6) + f_white * 0.5362f;
}

SGFLT f_run_noise_off(t_white_noise * a_w_noise){
    return 0.0f;
}

struct SamplePair white_noise_mono_run(t_white_noise* self){
    SGFLT sample = f_run_white_noise(&self[0]);
    return (struct SamplePair){sample, sample};
}

struct SamplePair pink_noise_mono_run(t_white_noise* self){
    SGFLT sample = f_run_pink_noise(&self[0]);
    return (struct SamplePair){sample, sample};
}

struct SamplePair white_noise_stereo_run(t_white_noise* self){
    SGFLT left = f_run_white_noise(&self[0]);
    SGFLT right = f_run_white_noise(&self[1]);

    return (struct SamplePair){left, right};
}

struct SamplePair pink_noise_stereo_run(t_white_noise* self){
    SGFLT left = f_run_pink_noise(&self[0]);
    SGFLT right = f_run_pink_noise(&self[1]);

    return (struct SamplePair){left, right};
}

struct SamplePair noise_off_stereo_run(t_white_noise* self){
    return  (struct SamplePair){0.0, 0.0};
}
