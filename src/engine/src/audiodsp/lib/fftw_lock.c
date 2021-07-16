#include <pthread.h>
#include <fftw3.h>

#include "audiodsp/lib/fftw_lock.h"


int FFTW_LOCK_INIT = 0;
pthread_mutex_t FFTW_LOCK;

#ifdef SG_USE_DOUBLE
fftw_plan g_fftw_plan_dft_r2c_1d(
    int a_size,
    SGFLT * a_in,
    fftw_complex * a_out,
    unsigned a_flags
){
    fftw_plan f_result;
#else
fftwf_plan g_fftw_plan_dft_r2c_1d(
    int a_size,
    SGFLT * a_in,
    fftwf_complex * a_out,
    unsigned a_flags
){
    fftwf_plan f_result;
#endif

    if(!FFTW_LOCK_INIT){
        pthread_mutex_init(&FFTW_LOCK, NULL);
        FFTW_LOCK_INIT = 1;
    }

    pthread_mutex_lock(&FFTW_LOCK);
#ifdef SG_USE_DOUBLE
    f_result = fftw_plan_dft_r2c_1d(a_size, a_in, a_out, a_flags);
#else
    f_result = fftwf_plan_dft_r2c_1d(a_size, a_in, a_out, a_flags);
#endif
    pthread_mutex_unlock(&FFTW_LOCK);

    return f_result;
}

