#ifndef UTIL_CSV_SPLIT_H
#define UTIL_CSV_SPLIT_H

typedef struct{
    int count;
    char** str_arr;
    char* str_block;
}t_line_split;

t_line_split* g_split_line(
    char a_delimiter,
    const char * a_str
);
void v_free_split_line(t_line_split * a_split_line);

// The new, faster way
char* str_split(char*, char*, char);

#endif
