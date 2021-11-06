#include <stddef.h>
#include <stdlib.h>

#include "cds/hashtable.h"


static inline size_t CDSHashTableIndex(
    struct CDSHashTable* self,
    CDSHash hash
){
    size_t index = hash % self->max;
    return index;
}

struct CDSHashTable* CDSHashTableNew(
    size_t initialSize,
    void(*valueFree)(void*)
){
    struct CDSHashTable* self = (struct CDSHashTable*)malloc(
        sizeof(struct CDSHashTable)
    );
    CDSHashTableInit(
        self,
        initialSize,
        valueFree
    );
    return self;
}

void CDSHashTableInit(
    struct CDSHashTable* self,
    size_t initialSize,
    void(*valueFree)(void*)
){
    *self = (struct CDSHashTable){
        .len = 0,
        .max = initialSize,
        .buckets = (struct CDSHashBucket*)calloc(
            initialSize,
            sizeof(struct CDSHashBucket)
        ),
        .valueFree = valueFree,
    };
}

void CDSHashTableFree(
    struct CDSHashTable* self,
    int freePtr
){
    size_t i, j;
    struct CDSHashBucket* bucket;

    for(i = 0; i < self->max; ++i){
        bucket = &self->buckets[i];
        for(j = 0; j < bucket->len; ++j){
            CDSHashTableEntryFree(
                &bucket->entries[j],
                self->valueFree
            );
        }
    }

    free(self->buckets);
    if(freePtr){
        free(self);
    }
}

void CDSHashTableResize(
    struct CDSHashTable* self,
    size_t initialSize
){
    size_t i, j;
    struct CDSHashTableEntry* entry;
    struct CDSHashBucket* bucket;
    struct CDSHashTable old = *self;

    self->buckets = (struct CDSHashBucket*)calloc(
        initialSize,
        sizeof(struct CDSHashBucket)
    );
    self->max = initialSize;
    self->len = 0;

    for(i = 0; i < old.max; ++i){
        bucket = &old.buckets[i];
        for(j = 0; j < bucket->len; ++j){
            entry = &bucket->entries[j];
            CDSHashTableSet(
                self,
                entry->hash,
                entry->key,
                entry->keySize,
                entry->value
            );
            free(entry->key);
        }
    }

    free(old.buckets);
}

struct CDSHashTableEntry* CDSHashTableGet(
    struct CDSHashTable* self,
    CDSHash hash,
    char*  key,
    size_t keySize
){
    size_t index = CDSHashTableIndex(self, hash);
    struct CDSHashBucket* bucket = &self->buckets[index];

    return CDSHashBucketGet(
        bucket,
        hash,
        key,
        keySize
    );
}

void CDSHashTableSet(
    struct CDSHashTable* self,
    CDSHash hash,
    char*  key,
    size_t keySize,
    void*  value
){
    size_t index = CDSHashTableIndex(self, hash);
    struct CDSHashBucket* bucket = &self->buckets[index];
    int bucket_index = CDSHashBucketIndex(
        bucket,
        hash,
        key,
        keySize
    );

    if(
        bucket_index < 0
        &&
        CDSHashBucketIsFull(bucket)
    ){
        CDSHashTableResize(
            self,
            self->max * 2
        );
        CDSHashTableSet(
            self,
            hash,
            key,
            keySize,
            value
        );
    } else {
        CDSHashBucketSet(
            bucket,
            hash,
            key,
            keySize,
            value
        );
        if(bucket_index < 0){
            ++self->len;
        }
    }
}

void CDSHashTableDelete(
    struct CDSHashTable* self,
    CDSHash hash,
    char*  key,
    size_t keySize
){
    size_t index = CDSHashTableIndex(self, hash);
    struct CDSHashBucket* bucket = &self->buckets[index];

    int found = CDSHashBucketDelete(
        bucket,
        hash,
        key,
        keySize,
        self->valueFree
    );
    if(found){
        --self->len;
    }
}
