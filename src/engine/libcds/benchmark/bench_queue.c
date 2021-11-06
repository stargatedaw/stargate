#include <assert.h>
#include <stddef.h>

#include "cds/queue.h"

#include "./bench_queue.h"
#include "./util.h"


void BenchQueue(){
    BenchQueueAppendPop();
}

size_t BenchQueueAppendPop(){
    size_t i, j;
    clock_t start, end;
    size_t count = BenchObjCount(sizeof(size_t));
    struct CDSQueue* queue = CDSQueueNew(
        sizeof(size_t),
        10,
        1000,
        NULL
    );

    start = clock();
    for(i = 0; i < count; ++i){
        CDSQueueAppend(queue, &i);
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchQueueAppendPop::Append",
        count
    );

    start = clock();
    for(i = 0; i < count; ++i){
        j = *(size_t*)CDSQueuePop(queue);
        assert(i == j);
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchQueueAppendPop::Pop",
        count
    );

    CDSQueueFree(queue, 1);
    return count;
}
