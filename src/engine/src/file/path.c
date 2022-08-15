#include <stdarg.h>
#include <string.h>

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

void vpath_join(
	char* result,
    int count,
	...
){
	va_list args;
	va_start(args, count);

    int i, j, pos = 0;
    char * str;
    char chr;

    for(i = 0; i < count; ++i){
        str = va_arg(args, char*);
		sg_assert(
			str != NULL && str[0] != '\0',
			"vpath_join: '%s' has empty section at %i",
			result,
			i
		);

        if(i){
            result[pos] = PATH_SEP[0];
            ++pos;
        }

        for(j = 0; ; ++j){
            chr = str[j];
            if(chr == '\0'){
                break;
            }
            result[pos] = chr;
            ++pos;
        }
    }

    result[pos] = '\0';
	va_end(args);
}

