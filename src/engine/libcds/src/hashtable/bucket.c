#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include "cds/hashtable/bucket.h"


int CDSHashBucketIndex(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*   key,
    size_t  keySize
){
    int i;
    struct CDSHashTableEntry* current;

    for(i = 0; i < self->len; ++i){
        current = &self->entries[i];
        if(
            current->hash == hash
            &&
            current->keySize == keySize
            &&
            !memcmp(
                key,
                current->key,
                keySize
            )
        ){
            return i;
        }
    }

    return -1;
}

int CDSHashBucketIsFull(
    struct CDSHashBucket* self
){
    if(self->len >= HASH_BUCKET_MAX - 1){
        return 1;
    } else {
        return 0;
    }
}

struct CDSHashTableEntry* CDSHashBucketGet(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*   key,
    size_t  keySize
){
    int index =  CDSHashBucketIndex(
        self,
        hash,
        key,
        keySize
    );
    if(index == -1){
        return NULL;
    } else {
        return &self->entries[index];
    }
}

void CDSHashBucketSet(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*   key,
    size_t  keySize,
    void*   value
){
    struct CDSHashTableEntry* entry;

    int index =  CDSHashBucketIndex(
        self,
        hash,
        key,
        keySize
    );

    // The caller is supposed to check if the bucket is full and resize
    // the hashtable if so.  So do not check for that condition here
    if(index == -1){
        entry = &self->entries[self->len];
        *entry = (struct CDSHashTableEntry){
            .hash =    hash,
            .key =     (char*)malloc(keySize),
            .keySize = keySize,
            .value =   value,
        };
        memcpy(
            entry->key,
            key,
            keySize
        );
        ++self->len;
    } else {
        entry = &self->entries[index];
        entry->value = value;
    }
}

int CDSHashBucketDelete(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*  key,
    size_t keySize,
    void(*valueFree)(void*)
){
    struct CDSHashTableEntry* entry;

    int index =  CDSHashBucketIndex(
        self,
        hash,
        key,
        keySize
    );

    if(index == -1){
        return 0;
    }

    entry = &self->entries[index];

    if(valueFree != NULL){
        valueFree(entry->value);
    }

    free(entry->key);

    // shift everything down by one
    if(index < self->len - 1){
        memmove(
            &self->entries[index],
            &self->entries[index + 1],
            sizeof(struct CDSHashTableEntry) * (self->len - 1)
        );
    }
    --self->len;
    return 1;
}
