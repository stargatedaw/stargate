#include <sndfile.h>

#include "audiodsp/lib/amp.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/multifx/multifx3knob.h"
#include "plugin.h"
#include "audio/item.h"
#include "audio/audio_pool.h"
#include "csv/2d.h"
#include "files.h"
#include "unicode.h"


void g_audio_pool_item_init(
    t_audio_pool_item *f_result,
    int a_uid,
    SGFLT volume,
    const SGPATHSTR *a_path,
    SGFLT a_sr
){
    f_result->uid = a_uid;
    f_result->volume = volume;
    f_result->is_loaded = 0;
    f_result->host_sr = a_sr;
    sg_path_snprintf(
        f_result->path, 
	2047,
#if SG_OS == _OS_WINDOWS
	L"%ls",
#else
	"%s",
#endif
        a_path
    );
    file_fx_controls_init(&f_result->fx_controls);
}

t_audio_pool_item * g_audio_pool_item_get(
    int a_uid,
    const SGPATHSTR *a_path,
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

    sg_assert(
        i_file_exists(a_audio_pool_item->path),
#if SG_OS == _OS_WINDOWS
        "Audio file does not exist: '%ls'",
#else
        "Audio file does not exist: '%s'",
#endif
        a_audio_pool_item->path
    );

    file = SG_SF_OPEN(
        a_audio_pool_item->path,
        SFM_READ,
        &info
    );

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
            if(f_i >= f_fade_out_start){
                if(f_fade_out_envelope <= 0.0f){
                    f_fade_out_dec = 0.0f;
                }

                f_fade_out_envelope -= f_fade_out_dec;
            }

            for (j = 0; j < f_adjusted_channel_count; ++j){
                f_temp_sample =
                        (tmpFrames[(f_i - AUDIO_ITEM_PADDING_DIV2) *
                        info.channels + j]);

                if(f_i >= f_fade_out_start){
                    tmpSamples[j][f_i] = f_temp_sample * f_fade_out_envelope;
                } else {
                    tmpSamples[j][f_i] = f_temp_sample;
                }
            }
        } else {
            tmpSamples[0][f_i] = 0.0f;
            if(f_adjusted_channel_count > 1){
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
        log_info("Using hugepages, not freeing audio_pool uid %i", a_uid);
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
                log_info("free'd %f MB",
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
    SGPATHSTR* a_file_path,
    SGPATHSTR* audio_folder
){
    SGPATHSTR f_path[8192];
    f_path[0] = '\0';

    int f_pos = 2;

#if SG_OS == _OS_WINDOWS
    if(a_file_path[0] == L'!'){
#else
    if(a_file_path[0] == '!'){
#endif
        SGPATHSTR* rest = a_file_path;
        ++rest;
        sg_path_snprintf(
            f_path,
            8191,
#if SG_OS == _OS_WINDOWS
            L"%ls%ls",
#else
            "%s%s",
#endif
            audio_folder,
            rest
        );
    } else if(a_file_path[0] != L'/' && a_file_path[1] == L':'){  // Windows
        SGPATHSTR f_file_path[2048];

        f_file_path[0] = a_file_path[0];
        while(1){
            f_file_path[f_pos - 1] = a_file_path[f_pos];
            if(a_file_path[f_pos] == L'\0'){
                break;
            }
            ++f_pos;
        }

        log_info(
#if SG_OS == _OS_WINDOWS
            "v_audio_pool_add_item:  '%ls' '%ls'",
#else
            "v_audio_pool_add_item:  '%s' '%s'",
#endif
            a_audio_pool->samples_folder,
            f_file_path
        );

        sg_path_snprintf(
            f_path,
            8191,
#if SG_OS == _OS_WINDOWS
            L"%ls/%ls",
#else
            "%s/%s",
#endif
            a_audio_pool->samples_folder,
            f_file_path
        );
    } else {  // UNIX
        if(a_file_path[0] == '/'){
            sg_path_snprintf(
                f_path,
                8191,
#if SG_OS == _OS_WINDOWS
                L"%ls%ls",
#else
                "%s%s",
#endif
                a_audio_pool->samples_folder,
                a_file_path
            );
	    // TODO Stargate v2: Delete this quirk for the 
	    // audio_pool corruption bug
#if SG_OS == _OS_WINDOWS
	    if(a_file_path[1] == L':' && !i_file_exists(f_path)){
                sg_path_snprintf(
                    f_path,
                    8191,
                    L"%ls/%ls",
                    a_audio_pool->samples_folder,
                    &a_file_path[2]
                );
	    }
#else
	    if(a_file_path[1] == ':' && !i_file_exists(f_path)){
                sg_path_snprintf(
                    f_path,
                    8191,
                    "%s/%s",
                    a_audio_pool->samples_folder,
                    &a_file_path[2]
                );
	    }
#endif
        } else {
            sg_path_snprintf(
                f_path,
                8191,
#if SG_OS == _OS_WINDOWS
                L"%ls/%ls",
#else
                "%s/%s",
#endif
                a_audio_pool->samples_folder,
                a_file_path
            );
        }
    }

    if(!i_file_exists(f_path)){
        sg_assert(
            a_file_path[0] != '!',
#if SG_OS == _OS_WINDOWS
            "File in project audio folder does not exist '%ls'",
#else
            "File in project audio folder does not exist '%s'",
#endif
            a_file_path
        );
        sg_path_snprintf(
            f_path, 
            8191,
#if SG_OS == _OS_WINDOWS
            L"%ls",
#else
            "%s",
#endif
            a_file_path
        );
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
    SGPATHSTR * a_file_path,
    SGPATHSTR* audio_folder
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
                        "v_audio_pool_add_items: control out of range: %f",
                        control
                    );
                    item->fx_controls.controls[i].knobs[j] = control;
                }
                v_iterate_2d_char_array(f_arr);
                fx_type = atoi(f_arr->current_str);
                sg_assert(
                    fx_type >= 0 && fx_type < MULTIFX3KNOB_MAX_INDEX,
                    "v_audio_pool_add_items: Invalid fx_type %i not in "
                    "range 0 to %i",
                    fx_type,
                    MULTIFX3KNOB_MAX_INDEX
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
            log_info("Audio Pool: Loading file '%s'", f_arr->current_str);
#if SG_OS == _OS_WINDOWS
            SGPATHSTR path[2048];
            utf8_to_utf16(
	        (const utf8_t*)f_arr->current_str, 
                strlen(f_arr->current_str), 
                path, 
                2048
            );
            v_audio_pool_add_item(
                a_audio_pool,
                f_uid,
                volume,
                path,
                audio_folder
            );
#else
            v_audio_pool_add_item(
                a_audio_pool,
                f_uid,
                volume,
                f_arr->current_str,
                audio_folder
            );
#endif
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
                log_error(
                    "g_audio_pool_get_item_by_uid: Failed to load file "
                    "for %i",
                    a_uid
                );
                return NULL;
            }
        }
        return &a_audio_pool->items[a_uid];
    } else {
        log_error(
            "g_audio_pool_get_item_by_uid: Couldn't find uid %i",
            a_uid
        );
    }

    return NULL;
}

