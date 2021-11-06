#include <assert.h>
#include <stddef.h>
#include <stdlib.h>

#include "cds/queue.h"
#include "./test_queue.h"


void TestCDSQueue(){
    TestCDSQueueNewAppendPopPurgeFree();
    TestCDSQueueFreeFunc();
    TestCDSQueuePopAlloc();
}

void TestCDSQueueNewAppendPopPurgeFree(){
    size_t i;
    size_t* result;
    struct CDSQueue* queue = CDSQueueNew(
        sizeof(size_t),
        3,
        100,
        NULL
    );
    for(i = 0; i < 1000; ++i){
        CDSQueueAppend(queue, &i);
    }
    assert(queue->len == 1000);
    for(i = 0; i < 500; ++i){
        result = (size_t*)CDSQueuePop(queue);
        assert(*result == i);
    }
    assert(queue->len == 500);

    CDSQueuePurge(queue);
    CDSQueuePurge(queue);

    for(i = 500; i < 1000; ++i){
        result = (size_t*)CDSQueuePop(queue);
        assert(*result == i);
    }
    result = (size_t*)CDSQueuePop(queue);
    assert(result == NULL);

    CDSQueueFree(queue, 1);
}

struct TestQueueStruct {
    int* field1;
};

static void FreeTestQueueStruct(void* ptr){
    struct TestQueueStruct* obj = (struct TestQueueStruct*)ptr;
    free(obj->field1);
}

void TestCDSQueueFreeFunc(){
    size_t i;
    struct TestQueueStruct var1;

    struct CDSQueue* queue = CDSQueueNew(
        sizeof(struct TestQueueStruct),
        3,
        10,
        FreeTestQueueStruct
    );
    for(i = 0; i < 96; ++i){
        var1 = (struct TestQueueStruct){
            .field1 = (int*)malloc(sizeof(int)),
        };
        CDSQueueAppend(queue, &var1);
        CDSQueuePop(queue);
    };
    CDSQueuePurge(queue);

    for(i = 0; i < 96; ++i){
        var1 = (struct TestQueueStruct){
            .field1 = (int*)malloc(sizeof(int)),
        };
        CDSQueueAppend(queue, &var1);
    };
    CDSQueueFree(queue, 1);
}


void TestCDSQueuePopAlloc(){
    size_t i;
    size_t* result;
    struct CDSQueue* queue = CDSQueueNew(
        sizeof(size_t),
        3,
        100,
        NULL
    );
    for(i = 0; i < 1000; ++i){
        CDSQueueAppend(queue, &i);
    }
    assert(queue->len == 1000);
    for(i = 0; i < 1000; ++i){
        result = (size_t*)CDSQueuePopAlloc(queue);
        assert(*result == i);
        free(result);
    }
    assert(queue->len == 0);
    result = (size_t*)CDSQueuePopAlloc(queue);
    assert(result == NULL);

    CDSQueueFree(queue, 1);
}
