#include <assert.h>
#include <stddef.h>
#include <stdio.h>

#include "cds/list.h"

#include "./bench_list.h"
#include "./util.h"


void BenchList(){
    BenchListAppendPop();
    BenchListMergeSortBinarySearch();
}

void BenchListAppendPop(){
    size_t i, j;
    clock_t start, end;
    size_t count = BenchObjCount(sizeof(size_t));
    struct CDSList* list = CDSListNew(
        sizeof(size_t),
        1000,
        NULL
    );

    start = clock();
    for(i = 0; i < count; ++i){
        CDSListAppend(list, &i);
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchListAppendPop::Append",
        count
    );

    start = clock();
    for(i = count - 1; i > 0; --i){
        j = *(size_t*)CDSListPop(list);
        assert(i == j);
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchListAppendPop::Pop",
        count
    );

    CDSListFree(list, 1);
}

int LongCmpFunc(void* arg1, void* arg2){
    long a, b;
    a = *(long*)arg1;
    b = *(long*)arg2;
    if(a < b){
        return -1;
    } else if(a == b) {
        return 0;
    } else {
        return 1;
    }
}

void BenchListMergeSortBinarySearch(){
    long i, j, k;
    clock_t start, end;
    size_t count = BenchObjCount(sizeof(long) * 2);
    struct CDSList* list = CDSListNew(
        sizeof(long),
        1000,
        NULL
    );

    for(i = count - 1; i >= 0; --i){
        CDSListAppend(list, &i);
    }

    start = clock();
    CDSListMergeSort(
        list,
        LongCmpFunc
    );
    end = clock();

    fprintf(
        stderr,
        "# BenchListAppendPop::MergeSort\n"
        "# iterations = size of list\n"
        "# average-per-iteration = time to sort each element of the list\n"
    );
    TimeSection(
        start,
        end,
        "BenchListAppendPop::MergeSort",
        count
    );

    start = clock();
    j = *(long*)CDSListIndex(list, 0);
    for(i = 1; i < count; ++i){
        k = *(long*)CDSListIndex(list, i);
        assert(j <= k);
        j = k;
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchListAppendPop::Index",
        count
    );

    start = clock();
    for(i = 0; i < count; ++i){
        j = CDSListBinarySearch(
            list,
            LongCmpFunc,
            &i
        );
        assert(i == j);
    }
    end = clock();

    TimeSection(
        start,
        end,
        "BenchListAppendPop::BinarySearch",
        count
    );
    CDSListFree(list, 1);
}
