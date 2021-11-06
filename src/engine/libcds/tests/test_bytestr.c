#include <assert.h>
#include <stddef.h>
#include <string.h>

#include "cds/bytestr.h"
#include "cds/list.h"
#include "./test_bytestr.h"


void TestCDSByteStr(){
    TestCDSByteStrNew();
    TestCDSByteStrSlice();
    TestCDSByteStrJoin();
    TestCDSByteStrJoinEmpty();
    TestCDSByteStrSearch();
    TestCDSByteStrStartsWith();
    TestCDSByteStrEndsWith();
    TestCDSByteStrStrip();
}

void TestCDSByteStrNew(){
    char str[] = "test";
    struct CDSByteStr* assign = CDSByteStrNew(
        str,
        1,
        0
    );
    struct CDSByteStr* copy = CDSByteStrNew(
        str,
        0,
        1
    );

    assert(strcmp(assign->data, copy->data) == 0);
    assert(assign->len == copy->len);

    CDSByteStrFree(assign, 1);
    CDSByteStrFree(copy, 1);
}

void TestCDSByteStrSlice(){
    struct TestCase {
        long start;
        long end;
        long step;
        char expected[20];
    };
    struct TestCase test;
    int i;
    int count = 5;
    struct TestCase testcases[] = {
        {0, 0, 1, "a"},
        {1, 4, 1, "bcde"},
        {-3,-1, 1, "xyz"},
        {0, 4, 2, "ace"},
        {4, 0, -2, "eca"}
    };
    struct CDSByteStr* slice;
    struct CDSByteStr* str = CDSByteStrNew(
        "abcdefghijklmnopqrstuvwxyz",
        0,
        1
    );
    for(i = 0; i < count; ++i){
        test = testcases[i];
        slice = CDSByteStrSlice(
            str,
            test.start,
            test.end,
            test.step
        );
        assert(strcmp(slice->data, test.expected) == 0);
        assert(slice->len == strlen(slice->data));
        CDSByteStrFree(slice, 1);
    }
    CDSByteStrFree(str, 1);
}

void TestCDSByteStrJoin(){
    int i;
    struct CDSByteStr* tmp;
    struct CDSByteStr* joined;
    char strings[][20] = {"a", "b", "c"};
    struct CDSByteStr* self = CDSByteStrNew(", ", 0, 1);
    struct CDSList* stringsList = CDSListNew(
        sizeof(struct CDSByteStr),
        3,
        NULL
    );

    for(i = 0; i < 3; ++i){
        tmp = (struct CDSByteStr*)CDSListAppendEmpty(stringsList);
        CDSByteStrInit(
            tmp,
            strings[i],
            1,
            0
        );
    }

    joined = CDSByteStrJoin(self, stringsList);

    assert(strcmp(joined->data, "a, b, c") == 0);
    assert(joined->len == 7);

    for(i = 0; i < 3; ++i){
        tmp = (struct CDSByteStr*)CDSListIndex(stringsList, i);
        CDSByteStrFree(tmp, 0);
    }
    CDSListFree(stringsList, 1);
    CDSByteStrFree(joined, 1);
    CDSByteStrFree(self, 1);
}

void TestCDSByteStrJoinEmpty(){
    struct CDSByteStr* joined;
    struct CDSByteStr* self = CDSByteStrNew(", ", 0, 1);
    struct CDSList* stringsList = CDSListNew(
        sizeof(struct CDSByteStr),
        3,
        NULL
    );

    joined = CDSByteStrJoin(self, stringsList);

    assert(strcmp(joined->data, "") == 0);
    assert(joined->len == 0);

    CDSByteStrFree(joined, 1);
    CDSByteStrFree(self, 1);
    CDSListFree(stringsList, 1);
}

void TestCDSByteStrSearch(){
    long result;
    struct CDSByteStr* self = CDSByteStrNew(
        "abcdefghijklmnopqrstuvwxyz",
        0,
        1
    );
    struct CDSByteStr* substr1 = CDSByteStrNew("jklmn", 0, 1);
    struct CDSByteStr* substr2 = CDSByteStrNew("jlkn", 0, 1);

    result = CDSByteStrSearch(self, substr1, -21);
    assert(result == 9);

    result = CDSByteStrSearch(self, substr2, 0);
    assert(result == -1);

    CDSByteStrFree(self, 1);
    CDSByteStrFree(substr1, 1);
    CDSByteStrFree(substr2, 1);
}

void TestCDSByteStrStartsWith(){
    struct TestCase{
        char self[20];
        char substr[20];
        int  expected;
    };
    struct TestCase testcases[] = {
        {"", "", 1},
        {"lol", "lo", 1},
        {"lo", "lol", 0}
    };
    struct TestCase test;
    int i, result;
    int count = 3;

    struct CDSByteStr* self;
    struct CDSByteStr* substr;

    for(i = 0; i < count; ++i){
        test = testcases[i];
        self = CDSByteStrNew(test.self, 0, 1);
        substr = CDSByteStrNew(test.substr, 0, 1);
        result = CDSByteStrStartsWith(self, substr);
        assert(result == test.expected);
        CDSByteStrFree(self, 1);
        CDSByteStrFree(substr, 1);
    }
}

void TestCDSByteStrEndsWith(){
    struct TestCase{
        char self[20];
        char substr[20];
        int  expected;
    };
    struct TestCase testcases[] = {
        {"", "", 1},
        {"lol", "ol", 1},
        {"lol", "lol", 1},
        {"lol", "jkj", 0},
        {"lo", "lol", 0}
    };
    struct TestCase test;
    int i, result;
    int count = 5;

    struct CDSByteStr* self;
    struct CDSByteStr* substr;

    for(i = 0; i < count; ++i){
        test = testcases[i];
        self = CDSByteStrNew(test.self, 0, 1);
        substr = CDSByteStrNew(test.substr, 0, 1);
        result = CDSByteStrEndsWith(self, substr);
        assert(result == test.expected);
        CDSByteStrFree(self, 1);
        CDSByteStrFree(substr, 1);
    }
}

void TestCDSByteStrStrip(){
    struct TestCase{
        char self[20];
        char expected[20];
    };
    struct TestCase testcases[] = {
        {"", ""},
        {"lol", "lol"},
        {"  \t\r\nlol", "lol"},
        {"lol\t\r \n", "lol"},
        {"   lol    ", "lol"}
    };
    struct TestCase test;
    int i;
    int count = 5;

    struct CDSByteStr* self;
    struct CDSByteStr* result;

    for(i = 0; i < count; ++i){
        test = testcases[i];
        self = CDSByteStrNew(test.self, 0, 1);
        result = CDSByteStrStrip(self);
        assert(strcmp(result->data, test.expected) == 0);
        assert(result->len == strlen(result->data));
        CDSByteStrFree(self, 1);
        CDSByteStrFree(result, 1);
    }
}
