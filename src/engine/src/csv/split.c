#include <stdlib.h>

#include "files.h"
#include "csv/split.h"

const char* str_split(const char* self, char* buf, char delim){
    while(1){
        if(self[0] == '\0'){
            buf[0] = '\0';
            return NULL;
        } else if(self[0] == delim){
            buf[0] = '\0';
            ++self;
            return self;
        }
        buf[0] = self[0];
        ++buf;
        ++self;
    }
}

t_line_split* g_split_line(
    char a_delimiter,
    const char * a_str
){
    t_line_split * f_result = (t_line_split*)malloc(sizeof(t_line_split));
    f_result->count = 1;

    int f_i = 0;
    while(1)
    {
        if(a_str[f_i] == '\0')
        {
            break;
        }
        else if(a_str[f_i] == a_delimiter)
        {
            ++f_result->count;
        }
        ++f_i;
    }

    f_result->str_arr = (char**)malloc(sizeof(char*) * f_result->count);
    f_result->str_block = (char*)malloc(
        sizeof(char) * TINY_STRING * f_result->count);

    f_i = 0;
    while(f_i < f_result->count)
    {
        f_result->str_arr[f_i] =
            &f_result->str_block[f_i * TINY_STRING];
        f_result->str_arr[f_i][0] = '\0';
        ++f_i;
    }

    f_i = 0;
    int f_i3 = 0;
    while(f_i < f_result->count)
    {
        int f_i2 = 0;
        while(1)
        {
            if(a_str[f_i3] == '\0' || a_str[f_i3] == a_delimiter)
            {
                f_result->str_arr[f_i][f_i2] = '\0';
                ++f_i3;
                break;
            }
            else
            {
                f_result->str_arr[f_i][f_i2] = a_str[f_i3];
            }
            ++f_i2;
            ++f_i3;
        }
        ++f_i;
    }

    return f_result;
}

void v_free_split_line(t_line_split * a_split_line){
    free(a_split_line->str_block);
    free(a_split_line->str_arr);
    free(a_split_line);
}

