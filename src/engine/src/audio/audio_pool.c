#include <sndfile.h>

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "plugin.h"
#include "audio/item.h"
#include "audio/audio_pool.h"
#include "csv/2d.h"
#include "files.h"


void g_audio_pool_item_init(
    t_audio_pool_item *f_result,
    int a_uid,
    SGFLT volume,
    const char *a_path,
    SGFLT a_sr
){
    f_result->uid = a_uid;
    f_result->volume = volume;
    f_result->is_loaded = 0;
    f_result->host_sr = a_sr;
    strncpy(f_result->path, a_path, 2047);
    file_fx_controls_init(&f_result->fx_controls);
}

t_audio_pool_item * g_audio_pool_item_get(
    int a_uid,
    const char *a_path,
    SGFLT a_sr
){
    t_audio_pool_item *f_result;

    lmalloc((void**)&f_result, sizeof(t_audio_pool_item));

    g_audio_pool_item_init(f_result, a_uid, 1.0, a_path, a_sr);

    return f_result;
}

int i_audio_pool_item_load(
    t_audio_pool_item *a_audio_pool_item,
    int a_huge_pages
){
    SF_INFO info;
    SNDFILE *file = NULL;
    size_t samples = 0;
    SGFLT *tmpFrames, *tmpSamples[2];
    int f_i = 0;

    info.format = 0;

    file = sf_open(a_audio_pool_item->path, SFM_READ, &info);

    if (!file){
        fprintf(
            stderr,
            "Unable to load sample file '%s'\n",
            a_audio_pool_item->path
        );
        return 0;
    }

    samples = info.frames;

    tmpFrames = (SGFLT*)malloc(info.frames * info.channels * sizeof(SGFLT));
    sg_read_audio(file, tmpFrames, info.frames);
    sf_close(file);

    if ((int)(info.samplerate) != (int)(a_audio_pool_item->host_sr)){
        double ratio = (double)(info.samplerate) /
            (double)(a_audio_pool_item->host_sr);
        a_audio_pool_item->ratio_orig = (SGFLT)ratio;
    } else {
        a_audio_pool_item->ratio_orig = 1.0f;
    }

    int f_adjusted_channel_count = 1;
    if(info.channels >= 2){
        f_adjusted_channel_count = 2;
    }

    int f_actual_array_size = (samples + AUDIO_ITEM_PADDING);

    for(f_i = 0; f_i < f_adjusted_channel_count; ++f_i){
        if(a_huge_pages){
            hpalloc(
                (void**)&(tmpSamples[f_i]),
                f_actual_array_size * sizeof(SGFLT)
            );
        } else {
            lmalloc(
                (void**)&(tmpSamples[f_i]),
                f_actual_array_size * sizeof(SGFLT)
            );
        }
    }

    int j;

    //For performing a 5ms fadeout of the sample, for preventing clicks
    SGFLT f_fade_out_dec = (1.0f / (SGFLT)(info.samplerate)) / (0.005);
    int f_fade_out_start = (samples + AUDIO_ITEM_PADDING_DIV2) -
        ((int)(0.005f * ((SGFLT)(info.samplerate))));
    SGFLT f_fade_out_envelope = 1.0f;
    SGFLT f_temp_sample = 0.0f;

    for(f_i = 0; f_i < f_actual_array_size; f_i++){
        if(
            f_i > AUDIO_ITEM_PADDING_DIV2
            &&
            f_i < (samples + AUDIO_ITEM_PADDING_DIV2)
        ){
            if(f_i >= f_fade_out_start)
            {
                if(f_fade_out_envelope <= 0.0f)
                {
                    f_fade_out_dec = 0.0f;
                }

                f_fade_out_envelope -= f_fade_out_dec;
            }

            for (j = 0; j < f_adjusted_channel_count; ++j){
                f_temp_sample =
                        (tmpFrames[(f_i - AUDIO_ITEM_PADDING_DIV2) *
                        info.channels + j]);

                if(f_i >= f_fade_out_start)
                {
                    tmpSamples[j][f_i] = f_temp_sample * f_fade_out_envelope;
                }
                else
                {
                    tmpSamples[j][f_i] = f_temp_sample;
                }
            }
        }
        else
        {
            tmpSamples[0][f_i] = 0.0f;
            if(f_adjusted_channel_count > 1)
            {
                tmpSamples[1][f_i] = 0.0f;
            }
        }
    }

    free(tmpFrames);

    a_audio_pool_item->samples[0] = tmpSamples[0];

    if(f_adjusted_channel_count > 1){
        a_audio_pool_item->samples[1] = tmpSamples[1];
    } else {
        a_audio_pool_item->samples[1] = NULL;
    }

    //-20 to ensure we don't read past the end of the array
    a_audio_pool_item->length = (samples + AUDIO_ITEM_PADDING_DIV2 - 20);

    a_audio_pool_item->sample_rate = info.samplerate;

    a_audio_pool_item->channels = f_adjusted_channel_count;

    a_audio_pool_item->is_loaded = 1;

    return 1;
}

void v_audio_pool_item_free(t_audio_pool_item *a_audio_pool_item){
    a_audio_pool_item->path[0] = '\0';

    SGFLT *tmpOld[2];

    tmpOld[0] = a_audio_pool_item->samples[0];
    tmpOld[1] = a_audio_pool_item->samples[1];
    a_audio_pool_item->samples[0] = 0;
    a_audio_pool_item->samples[1] = 0;
    a_audio_pool_item->length = 0;

    if (tmpOld[0]) free(tmpOld[0]);
    if (tmpOld[1]) free(tmpOld[1]);
    free(a_audio_pool_item);
}

t_audio_pool * g_audio_pool_get(SGFLT a_sr){
    t_audio_pool * f_result;
    hpalloc((void**)&f_result, sizeof(t_audio_pool));

    f_result->sample_rate = a_sr;
    f_result->count = 0;

    int f_i;
    for(f_i = 0; f_i < MAX_AUDIO_POOL_ITEM_COUNT; ++f_i){
        f_result->items[f_i].uid = -1;
    }
    return f_result;
}

void v_audio_pool_remove_item(
    t_audio_pool* a_audio_pool,
    int a_uid
){
    if(USE_HUGEPAGES){
        printf("Using hugepages, not freeing audio_pool uid %i\n", a_uid);
        return;
    }

    int f_i = 0;
    t_audio_pool_item * f_item = &a_audio_pool->items[a_uid];
    if(f_item->is_loaded){
        f_item->is_loaded = 0;
        for(f_i = 0; f_i < f_item->channels; ++f_i){
            SGFLT * f_data = f_item->samples[f_i];
            if(f_data){
                free(f_data);
                printf("free'd %f MB\n",
                    ((SGFLT)f_item->length / (1024. * 1024.)) * 4.0);
                f_item->samples[f_i] = NULL;
            }
        }
    }
}

t_audio_pool_item * v_audio_pool_add_item(
    t_audio_pool* a_audio_pool,
    int a_uid,
    SGFLT volume,
    char * a_file_path
){
    char f_path[2048];

    int f_pos = 2;

    if(a_file_path[0] != '/' && a_file_path[1] == ':'){
        char f_file_path[2048];

        f_file_path[0] = a_file_path[0];
        while(1){
            f_file_path[f_pos - 1] = a_file_path[f_pos];
            if(a_file_path[f_pos] == '\0'){
                break;
            }
            ++f_pos;
        }

        printf(
            "v_audio_pool_add_item:  '%s' '%s'\n",
            a_audio_pool->samples_folder,
            f_file_path
        );

        snprintf(
            f_path,
            2047,
            "%s%s%s",
            a_audio_pool->samples_folder,
            PATH_SEP,
            f_file_path
        );
    }
    else{
        if(a_file_path[0] == '/'){
            snprintf(
                f_path,
                2047,
                "%s%s",
                a_audio_pool->samples_folder,
                a_file_path
            );
        } else {
            snprintf(
                f_path,
                2047,
                "%s%s%s",
                a_audio_pool->samples_folder,
                PATH_SEP,
                a_file_path
            );
        }
    }

    g_audio_pool_item_init(
        &a_audio_pool->items[a_uid],
        a_uid,
        volume,
        f_path,
        a_audio_pool->sample_rate
    );
    ++a_audio_pool->count;
    return &a_audio_pool->items[a_uid];
}

/* Load entire pool at startup/open */
void v_audio_pool_add_items(
    t_audio_pool* a_audio_pool,
    char * a_file_path
){
    int i, j;
    a_audio_pool->count = 0;
    t_2d_char_array * f_arr = g_get_2d_array_from_file(
        a_file_path,
        LARGE_STRING
    );

    while(1){
        v_iterate_2d_char_array(f_arr);
        if(f_arr->eof){
            break;
        }
        if(!strcmp(f_arr->current_str, "f")){  // per-file fx
            int uid;
            SGFLT control;
            int fx_type;

            v_iterate_2d_char_array(f_arr);
            uid = atoi(f_arr->current_str);
            // The data model should always place the per-file-fx after all
            // pool entries
            t_audio_pool_item* item = g_audio_pool_get_item_by_uid(
                a_audio_pool,
                uid
            );
            for(i = 0; i < 8; ++i){
                for(j = 0; j < 3; ++j){
                    v_iterate_2d_char_array(f_arr);
                    control = atof(f_arr->current_str);
                    sg_assert(
                        control >= 0. && control <= 127.,
                        "v_audio_pool_add_items: control out of range"
                    );
                    item->fx_controls.controls[i].knobs[j] = control;
                }
                v_iterate_2d_char_array(f_arr);
                fx_type = atoi(f_arr->current_str);
                sg_assert(
                    fx_type >= 0 && fx_type <= 42,  // TODO: get the real count
                    "v_audio_pool_add_items: Invalid fx_type"
                );
                item->fx_controls.controls[i].fx_type = fx_type;
                item->fx_controls.controls[i].func_ptr =
                    g_mf3_get_function_pointer(fx_type);
            }
            item->fx_controls.loaded = 1;
        } else {  // audio pool item
            int f_uid = atoi(f_arr->current_str);
            v_iterate_2d_char_array(f_arr);
            SGFLT volume = atof(f_arr->current_str);
            volume = f_db_to_linear(volume);
            v_iterate_2d_char_array_to_next_line(f_arr);
            printf("Audio Pool: Loading file '%s'\n", f_arr->current_str);
            v_audio_pool_add_item(
                a_audio_pool,
                f_uid,
                volume,
                f_arr->current_str
            );
        }
    }
}

t_audio_pool_item * g_audio_pool_get_item_by_uid(
    t_audio_pool* a_audio_pool,
    int a_uid
){
    if(a_audio_pool->items[a_uid].uid == a_uid){
        if(!a_audio_pool->items[a_uid].is_loaded){
            if(!i_audio_pool_item_load(&a_audio_pool->items[a_uid], 1)){
                fprintf(
                    stderr,
                    "g_audio_pool_get_item_by_uid: Failed to load file "
                    "for %i\n",
                    a_uid
                );
                return NULL;
            }
        }
        return &a_audio_pool->items[a_uid];
    } else {
        fprintf(
            stderr,
            "g_audio_pool_get_item_by_uid: Couldn't find uid %i\n",
            a_uid
        );
    }

    return NULL;
}

