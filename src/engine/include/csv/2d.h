#ifndef UTIL_CSV_2D_H
#define UTIL_CSV_2D_H

typedef struct
{
    char * array;
    char * current_str;
    int current_index;
    int current_row;
    int current_column;
    int eof;
    int eol;
}t_2d_char_array;

void g_free_2d_char_array(t_2d_char_array * a_array);
/* You must assign something to x->array before trying to read. */
t_2d_char_array * g_get_2d_array(int a_size);
/* Return a 2d array of strings from a file delimited by
 * "|" and "\n" individual fields are
 * limited to being the size of SG_TINY_STRING */
t_2d_char_array * g_get_2d_array_from_file(
    const SGPATHSTR* a_file,
    int a_size
);
/* Return the next string from the array*/
void v_iterate_2d_char_array(t_2d_char_array* a_array);

/* Return the next string from the array until a newline, ignoring any
 * delimiting '|' characters */
void v_iterate_2d_char_array_to_next_line(t_2d_char_array* a_array);

#endif
