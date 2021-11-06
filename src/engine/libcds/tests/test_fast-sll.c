#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "./test_fast-sll.h"
#include "cds/fast-sll.h"


void TestCDSFastSLL(){
    TestCDSFastSLLAllocFree();
    TestCDSFastSLLZeroCommonSize();
}

static void fakeValueFree(struct CDSFastSLLCurrent* ptr){}

void TestCDSFastSLLAllocFree(){
    size_t i;
    int valueLen = 2;
    char values[][20] = {
        "value1",
        "value...2"
    };
    char* entry;

    struct CDSFastSLL* self = CDSFastSLLNew(
        27,
        sizeof(size_t),
        fakeValueFree
    );

    // The code path where length == 0
    CDSFastSLLNext(self);
    CDSFastSLLReset(self);

    for(i = 0; i < valueLen; ++i){
        entry = CDSFastSLLAppend(
            self,
            (char*)&i,
            strlen(values[i]) + 1
        );
        strcpy(entry, values[i]);
    }
    for(i = 0; i < valueLen; ++i){
        assert(
            !strcmp(self->current.value, values[i])
        );
        assert(
            *(size_t*)self->current.common == i
        );
        CDSFastSLLNext(self);
    }

    // Test appending after iterating to the end
    assert(self->current.value == NULL);
    entry = CDSFastSLLAppend(
        self,
        (char*)&i,
        strlen(values[0]) + 1
    );
    strcpy(entry, values[0]);
    assert(
        !strcmp(self->current.value, values[0])
    );

    CDSFastSLLFree(self, 1);
}

void TestCDSFastSLLZeroCommonSize(){
    size_t i;
    int valueLen = 2;
    char values[][20] = {
        "value1",
        "value...2"
    };
    char* entry;

    struct CDSFastSLL self;
    CDSFastSLLInit(&self, 27, 0, NULL);

    for(i = 0; i < valueLen; ++i){
        entry = CDSFastSLLAppend(
            &self,
            NULL,
            strlen(values[i]) + 1
        );
        strcpy(entry, values[i]);
    }
    for(i = 0; i < valueLen; ++i){
        assert(
            !strcmp(self.current.value, values[i])
        );
        assert(self.current.common == NULL);
        CDSFastSLLNext(&self);
    }

    CDSFastSLLFree(&self, 0);
}
