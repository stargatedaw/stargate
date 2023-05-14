#ifndef UTIL_FILES_H
#define UTIL_FILES_H

#include "compiler.h"

/*Standard string sizes*/
#define XLARGE_STRING 1048576
#define LARGE_STRING  65536 //1048576
#define MEDIUM_STRING  32768 //262144 //8192
#define SMALL_STRING  16384 //65536 //512
#define TINY_STRING 4096 //16384 //32

#define TERMINATING_CHAR '\\'

typedef struct st_dir_list
{
    char** dir_list;
    int dir_count;
}t_dir_list;

void chown_file(const char *file_name);
int i_file_exists(SGPATHSTR*);
void get_string_from_file(const SGPATHSTR* a_file, int a_size, char* a_buf);

void v_write_to_file(SGPATHSTR * a_file, char * a_string);
void v_append_to_file(SGPATHSTR * a_file, char * a_string);
t_dir_list* g_get_dir_list(char * a_dir);
void delete_file(SGPATHSTR* path);

// Retrieve a config setting from ~/stargate/config/
void get_file_setting(
    char * a_dest,
    SGPATHSTR * a_name,
    char * a_default
);

#endif
