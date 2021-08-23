#include <complex.h>
#include <fftw3.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "audiodsp/lib/fftw_lock.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/spectrum_analyzer.h"

t_spa_spectrum_analyzer * g_spa_spectrum_analyzer_get(
    int a_sample_count,
    int a_plugin_uid
){
    t_spa_spectrum_analyzer * f_result = (t_spa_spectrum_analyzer*)malloc(
        sizeof(t_spa_spectrum_analyzer))
    ;
    int f_i = 0;

    lmalloc((void**)&f_result->buffer, sizeof(SGFLT) * a_sample_count);

    f_result->plugin_uid = a_plugin_uid;
    f_result->buf_pos = 0;
    f_result->samples_count = a_sample_count;
    f_result->samples_count_div2 = a_sample_count / 2;

#ifdef SG_USE_DOUBLE
    f_result->samples = fftw_alloc_real(a_sample_count);
    f_result->output = fftw_alloc_complex(a_sample_count);
#else
    f_result->samples = fftwf_alloc_real(a_sample_count);
    f_result->output = fftwf_alloc_complex(a_sample_count);
#endif

    for(f_i = 0; f_i < f_result->samples_count; ++f_i)
    {
        f_result->samples[f_i] = 0.0f;
        f_result->output[f_i] = 0.0f;
    }

    f_result->str_buf = (char*)malloc(sizeof(char) * 15 * a_sample_count);
    f_result->str_buf[0] = '\0';

    f_result->plan = g_fftw_plan_dft_r2c_1d(
        f_result->samples_count,
        f_result->samples,
        f_result->output,
        0
    );

    return f_result;
}

/*
void g_spa_free(t_spa_spectrum_analyzer *a_spa){
#ifdef SG_USE_DOUBLE
    fftw_destroy_plan(a_spa->plan);
    fftw_free(a_spa->output);
    fftw_free(a_spa->samples);
#else
    fftwf_destroy_plan(a_spa->plan);
    fftwf_free(a_spa->output);
    fftwf_free(a_spa->samples);
#endif
}
*/

void v_spa_compute_fft(t_spa_spectrum_analyzer *a_spa)
{
    a_spa->str_buf[0] = '\0';
    int f_i;

#ifdef SG_USE_DOUBLE
    fftw_execute(a_spa->plan);
#else
    fftwf_execute(a_spa->plan);
#endif

    sprintf(
        a_spa->str_buf,
        "%i|spectrum|%f",
        a_spa->plugin_uid,
        cabs(a_spa->output[0])
    );

    for(f_i = 1; f_i < a_spa->samples_count_div2; ++f_i){
        sprintf(a_spa->str_tmp, "|%f", cabs(a_spa->output[f_i]));
        strcat(a_spa->str_buf, a_spa->str_tmp);
    }
}

/* void v_spa_run(struct t_spa_spectrum_analyzer *a_spa,
 * SGFLT * a_buf0, SGFLT * a_buf1, int a_count)
 *
 * Check if a_spa->str_buf[0] == '\0', if not, send a configure message
 * and then set spa->str_buf[0] = '\0'
 */
void v_spa_run(
    t_spa_spectrum_analyzer *a_spa,
    SGFLT * a_buf0,
    SGFLT * a_buf1,
    int a_count
){
    int f_i;

    for(f_i = 0; f_i < a_count; ++f_i)
    {
        a_spa->samples[a_spa->buf_pos] = (a_buf0[f_i] + a_buf1[f_i]) * 0.5f;
        ++a_spa->buf_pos;

        if(a_spa->buf_pos >= a_spa->samples_count)
        {
            a_spa->buf_pos = 0;
            v_spa_compute_fft(a_spa);
        }
    }
}

