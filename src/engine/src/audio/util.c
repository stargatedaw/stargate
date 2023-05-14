#include <sndfile.h>

#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/pitch_core.h"
#include "audio/util.h"
#include "compiler.h"


/*For time(affecting pitch) time stretching...  Since this is done
 offline anyways, it's not super optimized... */
void v_rate_envelope(
    SGPATHSTR* a_file_in,
    SGPATHSTR* a_file_out,
    SGFLT a_start_rate,
    SGFLT a_end_rate
){
    SF_INFO info;
    SNDFILE *file;
    SGFLT *tmpFrames;

    info.format = 0;

    file = SG_SF_OPEN(a_file_in, SFM_READ, &info);

    if (info.frames > 100000000)
    {
        //TODO:  Something, anything....
    }

    tmpFrames = (SGFLT *)malloc(info.frames * info.channels * sizeof(SGFLT));
    sf_readf_float(file, tmpFrames, info.frames);

    SF_INFO f_sf_info;
    f_sf_info.channels = info.channels;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = info.samplerate;
    sf_close(file);

    SGFLT f_sample_pos = 0.0;

    long f_size = 0;
    long f_block_size = 5000;

    SGFLT * f_output = (SGFLT*)malloc(sizeof(SGFLT) * (f_block_size * 2));

    SGFLT * f_buffer0 = 0;
    SGFLT * f_buffer1 = 0;
    int f_i = 0;

    if(info.channels == 1){
        f_buffer0 = tmpFrames;
    } else if(info.channels == 2){
        f_buffer0 = (SGFLT*)malloc(sizeof(SGFLT) * info.frames);
        f_buffer1 = (SGFLT*)malloc(sizeof(SGFLT) * info.frames);

        int f_i2 = 0;
        //De-interleave...
        while(f_i < (info.frames * 2)){
            f_buffer0[f_i2] = tmpFrames[f_i];
            f_i++;
            f_buffer1[f_i2] = tmpFrames[f_i];
            f_i++;
            f_i2++;
        }
    } else {
        sg_assert(
            0,
            "v_rate_envelope: %i channels is not supported",
            info.channels
        );
    }

    SNDFILE* f_sndfile = SG_SF_OPEN(a_file_out, SFM_WRITE, &f_sf_info);

    while(((int)f_sample_pos) < info.frames){
        f_size = 0;

        while(f_size < f_block_size){
            if(info.channels == 1){
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
            } else if(info.channels == 2){
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer1, info.frames,
                        f_sample_pos);
                f_size++;
            }

            double f_rate = (((double)(a_end_rate - a_start_rate)) *
                (f_sample_pos / ((double)(info.frames)))) + a_start_rate;

            f_sample_pos += f_rate;

            if((int)f_sample_pos >= info.frames)
            {
                break;
            }
        }

        if(info.channels == 1){
            sg_write_audio(f_sndfile, f_output, f_size);
        } else if(info.channels == 2){
            sg_write_audio(f_sndfile, f_output, f_size / 2);
        }
    }

    sf_close(f_sndfile);

    SGPATHSTR f_tmp_finished[2048];
    sg_path_snprintf(
        f_tmp_finished, 
        2048, 
#if SG_OS == _OS_WINDOWS
        L"%ls.finished", 
#else
        "%s.finished", 
#endif
        a_file_out
    );
#if SG_OS == _OS_WINDOWS
    FILE * f_finished = _wfopen(f_tmp_finished, L"w");
#else
    FILE * f_finished = fopen(f_tmp_finished, "w");
#endif
    fclose(f_finished);
    free(f_output);
    free(f_buffer0);
    if(f_buffer1)
    {
        free(f_buffer1);
    }
    if(info.channels > 1)
    {
        free(tmpFrames);
    }
}


void v_pitch_envelope(
    SGPATHSTR * a_file_in,
    SGPATHSTR * a_file_out,
    SGFLT a_start_pitch,
    SGFLT a_end_pitch
){
    SF_INFO info;
    SNDFILE *file;
    SGFLT *tmpFrames;

    info.format = 0;

    file = SG_SF_OPEN(a_file_in, SFM_READ, &info);

    if (info.frames > 100000000){
        //TODO:  Something, anything....
    }

    //!!! complain also if more than 2 channels

    tmpFrames = (SGFLT *)malloc(info.frames * info.channels * sizeof(SGFLT));
    sg_read_audio(file, tmpFrames, info.frames);

    SF_INFO f_sf_info;
    f_sf_info.channels = info.channels;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = info.samplerate;
    sf_close(file);

    SGFLT f_sample_pos = 0.0;

    long f_size = 0;
    long f_block_size = 10000;

    SGFLT * f_output = (SGFLT*)malloc(sizeof(SGFLT) * (f_block_size * 2));

    SGFLT * f_buffer0 = 0;
    SGFLT * f_buffer1 = 0;
    int f_i = 0;

    t_pit_ratio * f_pit_ratio = g_pit_ratio();

    if(info.channels == 1){
        f_buffer0 = tmpFrames;
    } else if(info.channels == 2){
        f_buffer0 = (SGFLT*)malloc(sizeof(SGFLT) * info.frames);
        f_buffer1 = (SGFLT*)malloc(sizeof(SGFLT) * info.frames);

        int f_i2 = 0;
        //De-interleave...
        while(f_i < (info.frames * 2))
        {
            f_buffer0[f_i2] = tmpFrames[f_i];
            f_i++;
            f_buffer1[f_i2] = tmpFrames[f_i];
            f_i++;
            f_i2++;
        }
    } else {
        sg_abort("%i channels is not supported", info.channels);
    }

    SNDFILE* f_sndfile = SG_SF_OPEN(a_file_out, SFM_WRITE, &f_sf_info);

    while(((int)f_sample_pos) < info.frames)
    {
        f_size = 0;

        //Interleave the samples...
        while(f_size < f_block_size)
        {
            if(info.channels == 1)
            {
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
            }
            else if(info.channels == 2)
            {
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer1, info.frames,
                        f_sample_pos);
                f_size++;
            }

            double f_rate = (((double)(a_end_pitch - a_start_pitch)) *
                (f_sample_pos / ((double)(info.frames)))) + a_start_pitch;

            SGFLT f_inc = f_pit_midi_note_to_ratio_fast(
                60.0f, f_rate + 60.0f, f_pit_ratio);

            f_sample_pos += f_inc;

            if((int)f_sample_pos >= info.frames)
            {
                break;
            }
        }

        if(info.channels == 1)
        {
            sg_write_audio(f_sndfile, f_output, f_size);
        }
        else if(info.channels == 2)
        {
            sg_write_audio(f_sndfile, f_output, f_size / 2);
        }
    }

    sf_close(f_sndfile);

    SGPATHSTR f_tmp_finished[2048];
    sg_path_snprintf(
        f_tmp_finished, 
        2048, 
#if SG_OS == _OS_WINDOWS
        L"%ls.finished", 
#else
        "%s.finished", 
#endif
        a_file_out
    );
#if SG_OS == _OS_WINDOWS
    FILE * f_finished = _wfopen(f_tmp_finished, L"w");
#else
    FILE * f_finished = fopen(f_tmp_finished, "w");
#endif
    fclose(f_finished);
    free(f_output);
    free(f_buffer0);
    if(f_buffer1)
    {
        free(f_buffer1);
    }
    if(info.channels > 1)
    {
        free(tmpFrames);
    }

    free(f_pit_ratio);
}

