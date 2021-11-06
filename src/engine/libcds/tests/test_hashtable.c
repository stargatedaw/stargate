#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cds/hashtable.h"
#include "test_hashtable.h"


void TestCDSHashTable(){
    TestCDSHashTableNewGetSetDelete();
    TestCDSHashTableResize();
}

void TestCDSHashTableNewGetSetDelete(){
    int* value = (int*)malloc(sizeof(int));
    *value = 1;
    char key[] = "hello";
    int keySize = strlen(key);
    CDSHash hash = CDSHashNew(key, keySize);
    struct CDSHashTableEntry* ret;
    struct CDSHashTable* hashtable = CDSHashTableNew(6, free);
    assert(hashtable->len == 0);
    ret = CDSHashTableGet(
        hashtable,
        hash,
        key,
        keySize
    );
    assert(ret == NULL);
    CDSHashTableSet(
        hashtable,
        hash,
        key,
        keySize,
        value
    );
    assert(hashtable->len == 1);
    CDSHashTableSet(
        hashtable,
        hash,
        key,
        keySize,
        value
    );
    assert(hashtable->len == 1);
    ret = CDSHashTableGet(
        hashtable,
        hash,
        key,
        keySize
    );
    assert(ret != NULL);
    assert(*ret->value == *value);
    CDSHashTableDelete(
        hashtable,
        hash,
        key,
        keySize
    );
    assert(hashtable->len == 0);
    CDSHashTableDelete(
        hashtable,
        hash,
        key,
        keySize
    );
    assert(hashtable->len == 0);

    value = (int*)malloc(sizeof(int));
    *value = 1;
    ret = CDSHashTableGet(
        hashtable,
        hash,
        key,
        keySize
    );
    assert(ret == NULL);
    CDSHashTableSet(
        hashtable,
        hash,
        key,
        keySize,
        value
    );

    CDSHashTableFree(hashtable, 1);
}

void TestCDSHashTableResize(){
    int i;
    int count = 100;
    int* values = (int*)malloc(sizeof(int) * count);
    char key[64];
    int keySize;
    CDSHash hash;
    struct CDSHashTable* hashtable = CDSHashTableNew(3, NULL);

    for(i = 0; i < count; ++i){
        values[i] = i;
        sprintf(key, "%i", i);
        keySize = strlen(key);
        hash = CDSHashNew(key, keySize);
        CDSHashTableSet(
            hashtable,
            hash,
            key,
            keySize,
            &values[i]
        );
    }
    assert(hashtable->len == count);

    for(i = 0; i < count / 2; ++i){
        sprintf(key, "%i", i);
        keySize = strlen(key);
        hash = CDSHashNew(key, keySize);
        CDSHashTableDelete(
            hashtable,
            hash,
            key,
            keySize
        );
    }
    CDSHashTableFree(hashtable, 1);
    free(values);
}
