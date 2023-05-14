#ifndef UTIL_AUDIO_AUDIO_POOL
#define UTIL_AUDIO_AUDIO_POOL

#include "plugin.h"
#include "compiler.h"

#define MAX_AUDIO_POOL_ITEM_COUNT 1500

typedef struct
{
    SGFLT sample_rate;
    int count;
    t_audio_pool_item items[MAX_AUDIO_POOL_ITEM_COUNT];
    SGPATHSTR samples_folder[2048];  //This must be set when opening a project
}t_audio_pool;

void g_audio_pool_item_init(
    t_audio_pool_item *f_result,
    int a_uid,
    SGFLT volume,
    const SGPATHSTR* a_path,
    SGFLT a_sr
);

t_audio_pool_item * g_audio_pool_item_get(
    int a_uid,
    const SGPATHSTR* a_path,
    SGFLT a_sr
);

int i_audio_pool_item_load(
    t_audio_pool_item *a_audio_pool_item,
    int a_huge_pages
);

void v_audio_pool_item_free(t_audio_pool_item *a_audio_pool_item);

t_audio_pool * g_audio_pool_get(SGFLT a_sr);

void v_audio_pool_remove_item(
    t_audio_pool* a_audio_pool,
    int a_uid
);

t_audio_pool_item * v_audio_pool_add_item(
    t_audio_pool* a_audio_pool,
    int a_uid,
    SGFLT volume,
    SGPATHSTR* a_file_path,
    SGPATHSTR* audio_folder
);

void v_audio_pool_add_items(
    t_audio_pool* a_audio_pool,
    SGPATHSTR* a_file_path,
    SGPATHSTR* audio_folder
);

t_audio_pool_item * g_audio_pool_get_item_by_uid(
    t_audio_pool* a_audio_pool,
    int a_uid
);
#endif
