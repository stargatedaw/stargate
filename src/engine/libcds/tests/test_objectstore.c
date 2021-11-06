#include <assert.h>

#include "cds/objectstore.h"
#include "./test_objectstore.h"

void TestCDSObjectStore(){
    TestCDSObjectStoreNewGetDelete();
    TestCDSObjectStoreResize();
    TestCDSObjectStoreValues();
}

static void fakeValueFree(void* ptr){}

void TestCDSObjectStoreNewGetDelete(){
    int* value;
    size_t i;
    struct CDSObjectStore* self = CDSObjectStoreNew(
        sizeof(int),
        4,
        fakeValueFree
    );
    value = (int*)CDSObjectStoreGet(self);
    *value = 6;
    assert(*(int*)&self->data[0][0] == 6);
    CDSObjectStoreDelete(self, (char*)value);
    value = (int*)CDSObjectStoreGet(self);
    assert((char*)value == &self->data[0][0]);

    for(i = 0; i < 11; ++i){
        CDSObjectStoreGet(self);
    }

    CDSObjectStoreFree(self, 1);
}

void TestCDSObjectStoreResize(){
    int* value[500];
    size_t i;
    struct CDSObjectStore* self = CDSObjectStoreNew(
        sizeof(int),
        4,
        fakeValueFree
    );

    for(i = 0; i < 500; ++i){
        value[i] = (int*)CDSObjectStoreGet(self);
    }

    for(i = 0; i < 500; ++i){
        CDSObjectStoreDelete(self, (char*)value[i]);
    }

    for(i = 0; i < 500; ++i){
        CDSObjectStoreGet(self);
    }

    CDSObjectStoreFree(self, 1);
}

void TestCDSObjectStoreValues(){
    int* value;
    int i, j;
    struct CDSObjectStore* self = CDSObjectStoreNew(
        sizeof(int),
        10,
        NULL
    );

    for(i = 0; i < 100; ++i){
        value = (int*)CDSObjectStoreGet(self);
        *value = i;
    }

    for(i = 0; i < 10; ++i){
        for(j = 0; j < 10; ++j){
            value = (int*)CDSObjectStoreIndex(self, i, j);
            assert(*value == (i * 10) + j);
        }
    }

    CDSObjectStoreFree(self, 1);
}
