#include <stdio.h>
#include <stdlib.h>

#include "compiler.h"
#include "files.h"
#include "csv/1d.h"

void g_free_1d_char_array(t_1d_char_array * a_array){
    free(a_array->array);
    free(a_array->buffer);
    free(a_array);
}

t_1d_char_array * g_1d_char_array_get(
    int a_column_count,
    int a_string_size
){
    int f_i = 0;
    t_1d_char_array * f_result =
            (t_1d_char_array*)malloc(sizeof(t_1d_char_array));
    f_result->array = (char**)malloc(sizeof(char*) * a_column_count);
    f_result->buffer =
        (char*)malloc(sizeof(char) * a_column_count * a_string_size);
    f_result->x_count = a_column_count;

    while(f_i < a_column_count)
    {
        f_result->array[f_i] = &f_result->buffer[f_i * a_string_size];
        ++f_i;
    }

    return f_result;
}

/* A specialized split function.  Column count and string size will
 * always be known in advance */
t_1d_char_array * c_split_str(
    const char * a_input,
    char a_delim,
    int a_column_count,
    int a_string_size
){
    int f_i = 0;
    int f_current_string_index = 0;
    int f_current_column = 0;

    t_1d_char_array * f_result = g_1d_char_array_get(
        a_column_count,
        a_string_size
    );

    while(1)
    {
        if(a_input[f_i] == a_delim)
        {
            f_result->array[f_current_column][f_current_string_index] = '\0';
            ++f_current_column;
            f_current_string_index = 0;
            sg_assert(
                f_current_column < a_column_count,
                "c_split_str: f_current_column %i >= a_column_count %i: %s",
                f_current_column,
                a_column_count,
                f_result->array[f_current_column]
            );
        }
        else if((a_input[f_i] == '\n') || (a_input[f_i] == '\0'))
        {
            f_result->array[f_current_column][f_current_string_index] = '\0';
            break;
        }
        else
        {
            f_result->array[f_current_column][f_current_string_index] =
                    a_input[f_i];
            ++f_current_string_index;
        }

        ++f_i;
    }

    sg_assert(
        f_current_column == a_column_count - 1,
        "c_split_str: f_current_column %i != a_column_count %i - 1",
        f_current_column,
        a_column_count
    );

    return f_result;
}

t_1d_char_array * c_split_str_remainder(
    const char * a_input,
    char a_delim,
    int a_column_count,
    int a_string_size
){
    int f_i = 0;
    int f_current_string_index = 0;
    int f_current_column = 0;

    t_1d_char_array * f_result = g_1d_char_array_get(
        a_column_count,
        a_string_size
    );

    while(f_i < a_column_count)
    {
        f_result->array[f_i] = (char*)malloc(sizeof(char) * a_string_size);
        ++f_i;
    }

    f_i = 0;

    while(1)
    {
        if(
            f_current_column < a_column_count - 1
            &&
            a_input[f_i] == a_delim
        ){
            f_result->array[f_current_column][f_current_string_index] = '\0';
            ++f_current_column;
            f_current_string_index = 0;
        }
        else if((a_input[f_i] == '\n') || (a_input[f_i] == '\0'))
        {
            f_result->array[f_current_column][f_current_string_index] = '\0';
            break;
        }
        else
        {
            f_result->array[f_current_column][f_current_string_index] =
                    a_input[f_i];
            ++f_current_string_index;
        }

        ++f_i;
    }

    return f_result;
}

