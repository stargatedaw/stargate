#include <stddef.h>
#include <stdint.h>

#include "cds/hashtable/hash.h"


CDSHash CDSHashNew(
    char * data,
    size_t size
){
    size_t i;

    CDSHash result = 19;

    for(i = 0; i < size; ++i){
        result = 31 * result + data[i];
    }

    return result;
}
