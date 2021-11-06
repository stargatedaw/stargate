#ifndef TEST_LIST_H
#define TEST_LIST_H

struct dummyStruct {
    char   field1[10];
    int    field2;
    double field3;
};

void TestCDSList();
void TestCDSListNewAppendFree();
void TestCDSListAppendResize();
void TestCDSListIndex();
void TestCDSListPop();
void TestCDSListRemove();
void TestCDSListInsert();
void TestCDSListSlice();
void TestCDSListIndexNegative();
void TestCDSListExtend();
void TestCDSListInsertionSort();
void TestCDSListMergeSort();
void TestCDSListSearch();
void TestCDSListBinarySearch();

#endif
