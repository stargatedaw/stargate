#include <stdlib.h>

#include "cds/hashtable/entry.h"

void CDSHashTableEntryFree(
    struct CDSHashTableEntry* self,
    void (*valueFree)(void*)
){
    if(valueFree){
        valueFree(self->value);
    }
    free(self->key);
}
