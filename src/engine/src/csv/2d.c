#include <stdlib.h>

#include "files.h"
#include "csv/2d.h"

void g_free_2d_char_array(t_2d_char_array * a_array){
    if(a_array->array)
    {
        free(a_array->array);
    }

    if(a_array)
    {
        free(a_array->current_str);
        free(a_array);
    }
}


t_2d_char_array * g_get_2d_array(int a_size){
    t_2d_char_array * f_result =
            (t_2d_char_array*)malloc(sizeof(t_2d_char_array));
    f_result->array = (char*)malloc(sizeof(char) * a_size);
    f_result->current_str = (char*)malloc(sizeof(char) * SMALL_STRING);

    f_result->current_index = 0;
    f_result->current_row = 0;
    f_result->current_column = 0;
    f_result->eof = 0;
    f_result->eol = 0;
    return f_result;
}

t_2d_char_array * g_get_2d_array_from_file(
    const SGPATHSTR* a_file,
    int a_size
){
    t_2d_char_array * f_result = g_get_2d_array(a_size);
    get_string_from_file(a_file, a_size, f_result->array);
    return f_result;
}

void v_iterate_2d_char_array(t_2d_char_array* a_array){
    char * f_result = a_array->current_str;
    int f_i = 0;

    while(1)
    {
        if((a_array->array[(a_array->current_index)] == TERMINATING_CHAR
            && a_array->eol)
            ||
            (a_array->array[(a_array->current_index)] == '\0'))
        {
            f_result[f_i] = '\0';
            a_array->eof = 1;
            a_array->eol = 1;
            break;
        }
        else if(a_array->array[(a_array->current_index)] == '\n')
        {
            f_result[f_i] = '\0';
            ++a_array->current_index;
            ++a_array->current_row;
            a_array->current_column = 0;
            a_array->eol = 1;
            break;
        }
        else if(a_array->array[(a_array->current_index)] == '|')
        {
            f_result[f_i] = '\0';
            ++a_array->current_index;
            ++a_array->current_column;
            a_array->eol = 0;
            //TODO:  A check for acceptable column counts
            //assert((a_array->current_column) < (a_array->));
            break;
        }
        else
        {
            a_array->eol = 0;
            f_result[f_i] = a_array->array[(a_array->current_index)];
        }

        ++a_array->current_index;
        ++f_i;
    }
}

void v_iterate_2d_char_array_to_next_line(t_2d_char_array* a_array){
    char * f_result = a_array->current_str;
    int f_i = 0;

    while(1)
    {
        //char a_test = a_array->array[(a_array->current_index)];
        if(a_array->array[(a_array->current_index)] == TERMINATING_CHAR
            && a_array->eol)
        {
            f_result[f_i] = '\0';
            a_array->eof = 1;
            break;
        }
        else if(a_array->array[(a_array->current_index)] == '\n')
        {
            f_result[f_i] = '\0';
            ++a_array->current_index;
            ++a_array->current_row;
            a_array->eol = 1;
            a_array->current_column = 0;
            break;
        }
        else
        {
            a_array->eol = 0;
            f_result[f_i] = a_array->array[(a_array->current_index)];
        }

        ++a_array->current_index;
        ++f_i;
    }
}

