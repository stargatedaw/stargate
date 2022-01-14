#ifndef FREQ_SPLITTER_H
#define FREQ_SPLITTER_H

// Allows splitting audio into frequency bands

#include "compiler.h"
#include "./svf_stereo.h"

#define FREQ_SPLITTER_MAX_SPLITS 3

struct _FreqSplitter;
struct FreqSplitter;

typedef void (*freq_splitter_run_func)(
    struct _FreqSplitter* self,
    SGFLT input[2],
    SGFLT* bottom,
    SGFLT* top
);

typedef void (*freq_splitter_set_func)(
    struct _FreqSplitter* self,
    SGFLT res,
    SGFLT freq
);

struct _FreqSplitter {
    t_svf2_filter svf;
};

struct FreqSplitterControls {
    PluginData* splits;
    PluginData* type;
    PluginData* res;
    PluginData* output[4];
    PluginData* freq[3];
};

struct FreqSplitter {
    int splits;
    struct _FreqSplitter splitters[FREQ_SPLITTER_MAX_SPLITS];
    freq_splitter_set_func set;
    freq_splitter_run_func run;
    SGFLT output[4][2];
};

void _freq_splitter_init(struct _FreqSplitter*, SGFLT);
void freq_splitter_init(struct FreqSplitter*, SGFLT);
void freq_splitter_run(struct FreqSplitter*, SGFLT[2]);
void freq_splitter_set(
    struct FreqSplitter* self,
    int splits,
    int type,
    SGFLT res,
    SGFLT freqs[3]
);

#endif
