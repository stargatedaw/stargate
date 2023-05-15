#include <time.h>

#include "stargate.h"
#include "audio/sample_graph.h"
#include "files.h"
#include "unicode.h"


void v_create_sample_graph(t_audio_pool_item * self){
    SGPATHSTR path_buff[2048];
    char str_buff[2048];
    sg_path_snprintf(
        path_buff,
        2048,
#if SG_OS == _OS_WINDOWS
        L"%ls/%i",
#else
        "%s/%i",
#endif
        STARGATE->samplegraph_folder,
        self->uid
    );

    if(i_file_exists(path_buff)){
#if SG_OS == _OS_WINDOWS
        log_info("%ls exists, not creating sample graph", path_buff);
#else
        log_info("%s exists, not creating sample graph", path_buff);
#endif
        return;
    }

    int len;

#if SG_OS == _OS_WINDOWS
    FILE* f_sg = _wfopen(path_buff, L"w");
    sg_assert_ptr(f_sg, "Failed to open sample graph file %ls", path_buff);
#else
    FILE* f_sg = fopen(path_buff, "w");
    sg_assert_ptr(f_sg, "Failed to open sample graph file %s", path_buff);
#endif

#if SG_OS == _OS_WINDOWS
    char utf8_buff[2048];
    utf16_to_utf8(
        self->path,
        wcslen(self->path),
        (utf8_t*)utf8_buff,
        2048
    );
    len = sg_snprintf(
        str_buff,
        2048,
        "meta|filename|%s\n",
        utf8_buff
    );
#else
    len = sg_snprintf(
        str_buff,
        2048,
        "meta|filename|%s\n",
        self->path
    );
#endif
    fwrite(str_buff, 1, len, f_sg);
    time_t f_ts = time(NULL);

    len = sg_snprintf(
        str_buff,
        2048,
        "meta|timestamp|%lu\n",
        (unsigned long)f_ts
    );
    fwrite(str_buff, 1, len, f_sg);

    len = sg_snprintf(
        str_buff,
        2048,
        "meta|channels|%i\n",
        self->channels
    );
    fwrite(str_buff, 1, len, f_sg);

    len = sg_snprintf(
        str_buff,
        2048,
        "meta|frame_count|%i\n",
        self->length
    );
    fwrite(str_buff, 1, len, f_sg);

    len = sg_snprintf(
        str_buff,
        2048,
        "meta|sample_rate|%i\n",
        (int)self->sample_rate
    );
    fwrite(str_buff, 1, len, f_sg);

    SGFLT f_length = (SGFLT)self->length / (SGFLT)self->sample_rate;

    len = sg_snprintf(str_buff, 2048, "meta|length|%f\n", f_length);
    fwrite(str_buff, 1, len, f_sg);

    int f_peak_size;

    if(f_length < 3.0){
        f_peak_size = 16;
    } else if(f_length < 20.0){
        f_peak_size = (int)((SGFLT)self->sample_rate * 0.005);
    } else {
        f_peak_size = (int)(self->sample_rate * 0.025);
    }

    int f_count = 0;
    int f_i, f_i2, f_i3;
    SGFLT f_sample;

    for(f_i2 = 0; f_i2 < self->length; f_i2 += f_peak_size){
        for(f_i = 0; f_i < self->channels; ++f_i){
            SGFLT f_high = 0.01;
            SGFLT f_low = -0.01;

            int f_stop = f_i2 + f_peak_size;
            if(f_stop > self->length){
                f_stop = self->length;
            }

            for(f_i3 = f_i2; f_i3 < f_stop; ++f_i3){
                f_sample = self->samples[f_i][f_i3];
                if(f_sample > f_high){
                    f_high = f_sample;
                } else if(f_sample < f_low){
                    f_low = f_sample;
                }
            }

            len = sg_snprintf(str_buff, 2048, "p|%i|h|%.3f\n", f_i, f_high);
            fwrite(str_buff, 1, len, f_sg);

            len = sg_snprintf(str_buff, 2048, "p|%i|l|%.3f\n", f_i, f_low);
            fwrite(str_buff, 1, len, f_sg);
        }
        ++f_count;
    }

    len = sg_snprintf(str_buff, 2048, "meta|count|%i\n", f_count);
    fwrite(str_buff, 1, len, f_sg);

    len = sg_snprintf(str_buff, 2048, "\\");
    fwrite(str_buff, 1, len, f_sg);

    fclose(f_sg);

    sg_path_snprintf(
        path_buff,
        2048,
#if SG_OS == _OS_WINDOWS
        L"%ls/%i.finished",
#else
        "%s/%i.finished",
#endif
        STARGATE->samplegraph_folder,
        self->uid
    );
#if SG_OS == _OS_WINDOWS
    FILE * f_finished = _wfopen(path_buff, L"w");
#else
    FILE * f_finished = fopen(path_buff, "w");
#endif
    fclose(f_finished);
}

