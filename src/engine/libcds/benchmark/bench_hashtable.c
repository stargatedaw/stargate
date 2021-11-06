#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

#include "cds/hashtable.h"

#include "./bench_hashtable.h"
#include "./util.h"


void BenchHashTable(){
    BenchHashTableSetGetDelete();
}

size_t BenchHashTableSetGetDelete(){
    size_t i, value;
    struct CDSHashTableEntry* result;
    clock_t start, end;
    size_t count = BenchObjCount(
        ((sizeof(size_t) * 2) + sizeof(struct CDSHashTableEntry) * 2)
    );
    size_t* values = (size_t*)malloc(sizeof(size_t) * count);
    struct CDSHashTable* hashtable = CDSHashTableNew(1000, NULL);

    start = clock();
    for(i = 0; i < count; ++i){
        values[i] = i;
        CDSHashTableSet(
            hashtable,
            (CDSHash)i,
            (char*)&values[i],
            sizeof(size_t),
            (char*)&values[i]
        );
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchHashTableSetGetDelete::Set",
        count
    );

    start = clock();
    for(i = 0; i < count; ++i){
        result = CDSHashTableGet(
            hashtable,
            (CDSHash)i,
            (char*)&values[i],
            sizeof(size_t)
        );
        value = *(size_t*)result->value;
        assert(value == i);
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchHashTableSetGetDelete::Get",
        count
    );

    start = clock();
    for(i = 0; i < count; ++i){
        CDSHashTableDelete(
            hashtable,
            (CDSHash)i,
            (char*)&values[i],
            sizeof(size_t)
        );
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchHashTableSetGetDelete::Delete",
        count
    );

    CDSHashTableFree(hashtable, 1);
    free(values);
    return count;
}
