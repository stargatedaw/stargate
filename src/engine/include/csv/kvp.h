#ifndef UTIL_CSV_KVP_H
#define UTIL_CSV_KVP_H

/*No pointers internally, call free() directly on an instance*/
typedef struct
{
    int key_len, val_len;
    char key[256];
    char value[5000];
}t_key_value_pair;

/* Specialized function, split a char* on the first index of a '|' char */
t_key_value_pair* g_kvp_get(const char * a_input);

#endif
