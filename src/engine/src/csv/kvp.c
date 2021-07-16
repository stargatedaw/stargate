#include <stdlib.h>

#include "csv/kvp.h"

/* Specialized function, split a char* on the first index of a '|' char */
t_key_value_pair* g_kvp_get(const char * a_input){
    t_key_value_pair * f_result =
            (t_key_value_pair*)malloc(sizeof(t_key_value_pair));
    int f_i = 0;
    f_result->key_len = 0;
    f_result->val_len = 0;
    int f_stage = 0;

    while(a_input[f_i] != '\0')
    {
        if(f_stage)
        {
            f_result->value[f_result->val_len] = a_input[f_i];
            ++f_result->val_len;
        }
        else
        {
            if(a_input[f_i] == '|')
            {
                f_stage = 1;
                f_result->key[f_result->key_len] = '\0';
            }
            else
            {
                f_result->key[f_result->key_len] = a_input[f_i];
                ++f_result->key_len;
            }
        }

        ++f_i;
    }

    f_result->value[f_result->val_len] = '\0';

    return f_result;
}

