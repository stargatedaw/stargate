#include "compiler.h"
#include "file/path.h"


/* Intended to be similar to Python's os.path.join */
void path_join(
    char * a_result,
    int num,
    char** a_str_list
){
    int f_i, f_i2, f_pos;
    f_pos = 0;
    char * f_str;
    char f_chr;

    for(f_i = 0; f_i < num; ++f_i){
        if(f_i){
            a_result[f_pos] = PATH_SEP[0];
            ++f_pos;
        }

        f_str = a_str_list[f_i];

        for(f_i2 = 0; ; ++f_i2){
            f_chr = f_str[f_i2];
            if(f_chr == '\0'){
                break;
            }
            a_result[f_pos] = f_chr;
            ++f_pos;
        }
    }

    a_result[f_pos] = '\0';
}

