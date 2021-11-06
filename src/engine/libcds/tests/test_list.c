#include <assert.h>
#include <stdlib.h>

#include "cds/list.h"

#include "test_list.h"


void TestCDSList(){
    TestCDSListNewAppendFree();
    TestCDSListAppendResize();
    TestCDSListIndex();
    TestCDSListPop();
    TestCDSListRemove();
    TestCDSListInsert();
    TestCDSListSlice();
    TestCDSListIndexNegative();
    TestCDSListExtend();
    TestCDSListInsertionSort();
    TestCDSListMergeSort();
    TestCDSListSearch();
    TestCDSListBinarySearch();
}

void fakeFree(void* ptr){}

void TestCDSListNewAppendFree(){
    struct CDSList* list = CDSListNew(
        sizeof(struct dummyStruct),
        3,
        fakeFree
    );
    assert(list);
    assert(list->len == 0);
    struct dummyStruct d = (struct dummyStruct){};
    CDSListAppend(
        list,
        &d
    );
    assert(list->len == 1);
    CDSListFree(list, 1);
}

void TestCDSListAppendResize(){
    int i;
    struct CDSList* list = CDSListNew(
        sizeof(struct dummyStruct),
        2,
        fakeFree
    );
    struct dummyStruct d = (struct dummyStruct){};
    for(i = 0; i < 10; ++i){
        CDSListAppend(
            list,
            &d
        );
    }
    assert(list->len == 10);
    CDSListFree(list, 1);
}

void TestCDSListIndex(){
    struct CDSList* list = CDSListNew(
        sizeof(struct dummyStruct),
        3,
        NULL
    );
    assert(list);
    struct dummyStruct d1 = (struct dummyStruct){
        .field2 = 1,
    };
    struct dummyStruct d2 = (struct dummyStruct){
        .field2 = 2,
    };
    CDSListAppend(
        list,
        &d1
    );
    // Get
    struct dummyStruct* d3 = (struct dummyStruct*)CDSListIndex(list, 0);
    assert(d3->field2 == d1.field2);
    // Set
    *d3 = d2;
    assert(d3->field2 == d2.field2);

    CDSListFree(list, 1);
}

void TestCDSListIndexNegative(){
    int i;
    int* _return;
    int values[4] = {3, 6, 9, 12};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        4,
        NULL
    );
    for(i = 0; i < 4; ++i){
        CDSListAppend(list, &values[i]);
    }

    _return = (int*)CDSListIndex(list, -1);
    assert(*_return == 12);
    _return = (int*)CDSListIndex(list, -3);
    assert(*_return == 6);

    CDSListFree(list, 1);
}

void TestCDSListPop(){
    int pop, i;
    char* _return;
    int values[3] = {3, 6, 9};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        3,
        NULL
    );
    for(i = 0; i < 3; ++i){
        CDSListAppend(list, &values[i]);
    }
    assert(list->len == 3);

    for(i = 2; i >= 0; --i){
        assert(list->len == i + 1);
        _return = CDSListPop(list);
        pop = (int)(*_return);
        assert(pop == values[i]);
        assert(list->len == i);
    }

    assert(list->len == 0);
    _return = (void*)CDSListPop(list);
    assert(_return == NULL);
    assert(list->len == 0);

    CDSListFree(list, 1);
}

void TestCDSListRemove(){
    int i;
    int* _return;
    int values[4] = {3, 6, 9, 12};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        4,
        fakeFree
    );
    for(i = 0; i < 4; ++i){
        CDSListAppend(list, &values[i]);
    }

    assert(list->len == 4);
    CDSListRemove(list, 1);
    assert(list->len == 3);
    _return = (int*)CDSListIndex(list, 1);
    assert(*_return == 9);
    _return = (int*)CDSListIndex(list, 2);
    assert(*_return == 12);

    CDSListRemove(list, 0);
    assert(list->len == 2);
    _return = (int*)CDSListIndex(list, 0);
    assert(*_return == 9);

    CDSListFree(list, 1);
}

void TestCDSListInsert(){
    int i, val;
    int* _return;
    int values[4] = {3, 6, 9, 12};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        4,
        NULL
    );
    for(i = 0; i < 4; ++i){
        CDSListAppend(list, &values[i]);
    }
    assert(list->len == 4);

    val = 5;
    CDSListInsert(list, 1, &val);
    assert(list->len == 5);
    _return = (int*)CDSListIndex(list, 0);
    assert(*_return == 3);
    _return = (int*)CDSListIndex(list, 1);
    assert(*_return == 5);
    _return = (int*)CDSListIndex(list, 2);
    assert(*_return == 6);
    _return = (int*)CDSListIndex(list, 4);
    assert(*_return == 12);

    CDSListFree(list, 1);
}

void TestCDSListSlice(){
    int i;
    int* _return;
    int values[4] = {3, 6, 9, 12};
    struct CDSList* slice;
    struct CDSList* list = CDSListNew(
        sizeof(int),
        4,
        NULL
    );
    for(i = 0; i < 4; ++i){
        CDSListAppend(list, &values[i]);
    }

    // Forward
    slice = CDSListSlice(list, -3, -1, 1);
    assert(slice->len == 3);
    _return = (int*)CDSListIndex(slice, 0);
    assert(*_return == 6);
    _return = (int*)CDSListIndex(slice, 2);
    assert(*_return == 12);
    CDSListFree(slice, 1);

    // Reverse
    slice = CDSListSlice(list, 3, 0, -2);
    assert(slice->len == 2);
    _return = (int*)CDSListIndex(slice, 0);
    assert(*_return == 12);
    _return = (int*)CDSListIndex(slice, 1);
    assert(*_return == 6);
    CDSListFree(slice, 1);

    CDSListFree(list, 1);
}

void TestCDSListExtend(){
    int i;
    int* _return;
    int values[6] = {3, 6, 9, 12, 15, 18};
    struct CDSList* list1 = CDSListNew(
        sizeof(int),
        3,
        NULL
    );
    struct CDSList* list2 = CDSListNew(
        sizeof(int),
        3,
        NULL
    );

    for(i = 0; i < 3; ++i){
        CDSListAppend(list1, &values[i]);
    }
    for(i = 3; i < 6; ++i){
        CDSListAppend(list2, &values[i]);
    }

    assert(list1->len == 3);
    assert(list2->len == 3);

    _return = (int*)CDSListIndex(list1, 0);
    assert(*_return == 3);
    _return = (int*)CDSListIndex(list2, 0);
    assert(*_return == 12);

    CDSListExtend(list1, list2);
    assert(list1->len == 6);

    _return = (int*)CDSListIndex(list1, 5);
    assert(*_return == 18);

    CDSListFree(list1, 1);
    CDSListFree(list2, 1);
}

int IntSortCmpFunc(void* a, void* b){
    int A = *((int*)a);
    int B = *((int*)b);
    if(A > B){
        return 1;
    } else if(A == B){
        return 0;
    } else {
        return -1;
    }
}

void TestCDSListInsertionSort(){
    int i;
    int* _return1;
    int* _return2;
    int values[6] = {9, 3, 6, 9, 12, 3};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        6,
        NULL
    );
    for(i = 0; i < 6; ++i){
        CDSListAppend(list, &values[i]);
    }

    CDSListInsertionSort(list, IntSortCmpFunc);

    for(i = 0; i < 5; ++i){
        _return1 = (int*)CDSListIndex(list, i);
        _return2 = (int*)CDSListIndex(list, i + 1);
        assert((*_return1) <= (*_return2));
    }
    CDSListFree(list, 1);
}

void TestCDSListMergeSort(){
    int i;
    int* _return1;
    int* _return2;
    int values[6] = {9, 3, 6, 9, 12, 3};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        6,
        NULL
    );
    for(i = 0; i < 6; ++i){
        CDSListAppend(list, &values[i]);
    }

    CDSListMergeSort(list, IntSortCmpFunc);

    for(i = 0; i < 5; ++i){
        _return1 = (int*)CDSListIndex(list, i);
        _return2 = (int*)CDSListIndex(list, i + 1);
        assert((*_return1) <= (*_return2));
    }
    CDSListFree(list, 1);
}

int _ListIntMatchIntCmpFunc(
    void* object,
    void* match
){
    if(*(int*)object == *(int*)match){
        return 1;
    } else {
        return 0;
    }
}

void TestCDSListSearch(){
    int i;
    long result;
    int match;
    int values[6] = {9, 3, 6, 9, 12, 3};
    struct CDSList* list = CDSListNew(
        sizeof(int),
        6,
        NULL
    );
    for(i = 0; i < 6; ++i){
        CDSListAppend(list, &values[i]);
    }

    // basic
    match = 9;
    result = CDSListSearch(
        list,
        _ListIntMatchIntCmpFunc,
        &match,
        0
    );
    assert(result == 0);

    // non-zero start
    result = CDSListSearch(
        list,
        _ListIntMatchIntCmpFunc,
        (void*)&match,
        1
    );

    // no match
    match = 99;
    assert(result == 3);
    result = CDSListSearch(
        list,
        _ListIntMatchIntCmpFunc,
        (void*)&match,
        0
    );
    assert(result == -1);

    CDSListFree(list, 1);
}

void TestCDSListBinarySearch(){
    int i;
    long result;
    int expected, search;
    int searches[3][2] = {
        {-99, -1},
        {1000000, -1},
        {10043, -1}
    };
    struct CDSList* list = CDSListNew(
        sizeof(int),
        1043,
        NULL
    );
    for(i = 0; i < 10043; ++i){
        CDSListAppend(list, &i);
    }

    for(i = -1; i < 10043; ++i){
        search = i;
        expected = i;
        result = CDSListBinarySearch(
            list,
            IntSortCmpFunc,
            &search
        );
        assert(result == expected);
    }

    for(i = 0; i < 3; ++i){
        search = searches[i][0];
        expected = searches[i][1];
        result = CDSListBinarySearch(
            list,
            IntSortCmpFunc,
            &search
        );
        assert(result == expected);
    }

    CDSListFree(list, 1);
}
