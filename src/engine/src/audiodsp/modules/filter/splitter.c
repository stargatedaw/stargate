#include "audiodsp/modules/filter/splitter.h"

void splitter_run_svf2(
    struct _FreqSplitter* self,
    SGFLT input[2],
    SGFLT* bottom,
    SGFLT* top
){
    t_svf2_kernel* kernel;
    int ch;
    for(ch = 0; ch < 2; ++ch){
        kernel = &self->svf.filter_kernels[ch][0];
        v_svf2_run(&self->svf, kernel, input[ch]);
        bottom[ch] = kernel->lp + (kernel->bp * 0.5);
        top[ch] = kernel->hp + (kernel->bp * 0.5);
    }
}

SG_THREAD_LOCAL freq_splitter_run_func SPLITTER_RUN_FUNCS[] = {
    splitter_run_svf2,  // 1
};

void freq_splitter_set_svf(
    struct _FreqSplitter* self,
    SGFLT res,
    SGFLT freq
){
    v_svf2_set_res(&self->svf, res);
    v_svf2_set_cutoff_base(&self->svf, freq);
    v_svf2_set_cutoff(&self->svf);
}

SG_THREAD_LOCAL freq_splitter_set_func SPLITTER_SET_FUNCS[] = {
    freq_splitter_set_svf,  // 1
};

void _freq_splitter_init(struct _FreqSplitter* self, SGFLT sr){
    g_svf2_init(&self->svf, sr);
}

void freq_splitter_init(struct FreqSplitter* self, SGFLT sr){
    int i;
    self->splits = 0;
    for(i = 0; i < FREQ_SPLITTER_MAX_SPLITS; ++i){
        _freq_splitter_init(&self->splitters[i], sr);
    }
}

void freq_splitter_set(
    struct FreqSplitter* self,
    int splits,
    int type,
    SGFLT res,
    SGFLT freqs[3]
){
    self->splits = splits;
    self->run = SPLITTER_RUN_FUNCS[type];
    self->set = SPLITTER_SET_FUNCS[type];
    int i;
    for(i = 0; i < splits; ++i){
        self->set(&self->splitters[i], res, freqs[i]);
    }
}

void freq_splitter_run(
    struct FreqSplitter* self,
    SGFLT input[2]
){
    int i;
    for(i = 0; i < self->splits; ++i){
        if(i == self->splits - 1){
            self->run(
                &self->splitters[i],
                input,
                self->output[i],
                self->output[i + 1]
            );
        } else {
            self->run(
                &self->splitters[i],
                input,
                self->output[i],
                input
            );
        }
    }
}

