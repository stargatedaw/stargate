#ifndef UTIL_CSV_1D_H
#define UTIL_CSV_1D_H

typedef struct{
    char ** array;
    char * buffer;
    int x_count;
}t_1d_char_array;

void g_free_1d_char_array(t_1d_char_array * a_array);

t_1d_char_array * g_1d_char_array_get(
    int a_column_count,
    int a_string_size
);

t_1d_char_array * c_split_str(
    const char * a_input,
    char a_delim,
    int a_column_count,
    int a_string_size
);

/* Same as above but ignores extra delimiters in the final column */
t_1d_char_array * c_split_str_remainder(
    const char * a_input,
    char a_delim,
    int a_column_count,
    int a_string_size
);

#endif
