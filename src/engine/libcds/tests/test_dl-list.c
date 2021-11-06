#include <assert.h>

#include "cds/dl-list.h"
#include "./test_dl-list.h"


void TestCDSDLList(){
    TestCDSDLListInsertAfter();
    TestCDSDLListInsertBefore();
    TestCDSDLListRemove();
    TestCDSDLListSwap();
    TestCDSDLListObjSizeZero();
}

static void fakeValueFree(void* ptr){}

void TestCDSDLListInsertAfter(){
    int value;
    struct CDSDLList* dllist = CDSDLListNew(
        sizeof(int),
        10,
        fakeValueFree
    );

    value = 1;
    CDSDLListInsertAfter(dllist, NULL, &value);
    assert(*(int*)dllist->head->value == 1);
    assert(*(int*)dllist->tail->value == 1);

    value = 3;
    CDSDLListInsertAfter(dllist, dllist->head, &value);

    assert(*(int*)dllist->head->value == 1);
    assert(*(int*)dllist->tail->value == 3);

    value = 2;
    CDSDLListInsertAfter(dllist, dllist->head, &value);
    assert(*(int*)dllist->head->value == 1);
    assert(*(int*)dllist->head->next->value == 2);
    assert(*(int*)dllist->tail->prev->value == 2);
    assert(*(int*)dllist->tail->value == 3);

    CDSDLListFree(dllist, 1);
}

void TestCDSDLListInsertBefore(){
    int value;
    struct CDSDLList* dllist = CDSDLListNew(
        sizeof(int),
        10,
        fakeValueFree
    );

    value = 1;
    CDSDLListInsertBefore(dllist, NULL, &value);

    value = 3;
    CDSDLListInsertBefore(dllist, dllist->head, &value);

    assert(*(int*)dllist->head->value == 3);
    assert(*(int*)dllist->tail->value == 1);

    value = 2;
    CDSDLListInsertBefore(dllist, dllist->head->next, &value);
    assert(*(int*)dllist->head->value == 3);
    assert(*(int*)dllist->head->next->value == 2);
    assert(*(int*)dllist->tail->value == 1);

    CDSDLListFree(dllist, 1);
}

void TestCDSDLListRemove(){
    int value;
    struct CDSDLList* dllist = CDSDLListNew(
        sizeof(int),
        10,
        fakeValueFree
    );

    value = 1;
    CDSDLListInsertBefore(dllist, NULL, &value);
    value = 3;
    CDSDLListInsertBefore(dllist, dllist->head, &value);
    value = 2;
    CDSDLListInsertBefore(dllist, dllist->head, &value);

    CDSDLListRemove(dllist, dllist->head->next);
    assert(dllist->len == 2);
    assert(*(int*)dllist->head->value == 2);
    assert(*(int*)dllist->tail->prev->value == 2);
    assert(*(int*)dllist->tail->value == 1);
    assert(*(int*)dllist->head->next->value == 1);
    CDSDLListRemove(dllist, dllist->tail);
    CDSDLListRemove(dllist, dllist->head);

    assert(dllist->len == 0);
    assert(dllist->head == NULL);
    assert(dllist->tail == NULL);

    CDSDLListFree(dllist, 1);
}

void TestCDSDLListSwap(){
    int value;
    struct CDSDLListNode* node;
    struct CDSDLList* dllist = CDSDLListNew(
        sizeof(int),
        10,
        fakeValueFree
    );

    value = 1;
    CDSDLListInsertAfter(dllist, NULL, &value);

    value = 3;
    CDSDLListInsertAfter(dllist, dllist->head, &value);

    value = 2;
    CDSDLListInsertAfter(dllist, dllist->head, &value);

    value = 99;
    node = CDSDLListNodeNew(dllist, &value);
    CDSDLListSwap(dllist, dllist->head->next, node, 1);
    assert(*(int*)dllist->head->next->value == 99);
    assert(*(int*)dllist->head->next->next->value == 3);
    assert(*(int*)dllist->head->value == 1);
    assert(*(int*)dllist->tail->value == 3);

    CDSDLListRemove(dllist, dllist->head);
    CDSDLListRemove(dllist, dllist->head);
    assert(dllist->len == 1);
    assert(*(int*)dllist->head->value == 3);
    assert(*(int*)dllist->tail->value == 3);

    value = -99;
    node = CDSDLListNodeNew(dllist, &value);
    CDSDLListSwap(dllist, dllist->head, node, 1);
    assert(*(int*)dllist->head->value == -99);
    assert(*(int*)dllist->tail->value == -99);

    CDSDLListFree(dllist, 1);
}

void TestCDSDLListObjSizeZero(){
    int values[2];
    struct CDSDLList* dllist = CDSDLListNew(0, 10, NULL);

    values[0] = 0;
    CDSDLListInsertAfter(dllist, NULL, &values[0]);

    values[1] = 1;
    CDSDLListInsertAfter(dllist, dllist->head, &values[1]);

    assert((int*)dllist->head->value == &values[0]);
    assert(*(int*)dllist->head->value == 0);
    assert((int*)dllist->tail->value == &values[1]);
    assert(*(int*)dllist->tail->value == 1);

    CDSDLListFree(dllist, 1);

}
