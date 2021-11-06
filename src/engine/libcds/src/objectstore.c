#include <stdlib.h>

#include "cds/objectstore.h"


static inline char* _ObjectStoreAllocate(
    struct CDSObjectStore* self
){
    char* result = (char*)malloc(self->allocSize * self->objSize);
    return result;
}

struct CDSObjectStore* CDSObjectStoreNew(
    size_t objSize,
    size_t allocSize,
    void (*valueFree)(void*)
){
    struct CDSObjectStore* self = (struct CDSObjectStore*)malloc(
        sizeof(struct CDSObjectStore)
    );
    CDSObjectStoreInit(
        self,
        objSize,
        allocSize,
        valueFree
    );
    return self;
}

void CDSObjectStoreInit(
    struct CDSObjectStore* self,
    size_t objSize,
    size_t allocSize,
    void (*valueFree)(void*)
){
    *self = (struct CDSObjectStore){
        .objSize   = objSize,
        .allocSize = allocSize,
        .valueFree = valueFree,
        .data      = (char**)malloc(sizeof(char*) * 16),
        .dataMax   = 16,
        .freed     = (char**)malloc(sizeof(char*) * 16),
        .freedLen  = 0,
        .freedMax  = 16,
    };
    self->data[0] = _ObjectStoreAllocate(self);
}

void CDSObjectStoreFree(
    struct CDSObjectStore* self,
    int freePtr
){
    size_t i, j, cLen;
    char* object;
    for(i = 0; i <= self->row; ++i){
        if(self->valueFree){
            if(i == self->row){
                cLen = self->column;
            } else {
                cLen = self->allocSize;
            }
            for(j = 0; j < cLen; ++j){
                object = CDSObjectStoreIndex(self, i, j);
                self->valueFree(object);
            }
        }
        free(self->data[i]);
    }
    free(self->data);
    free(self->freed);
    if(freePtr){
        free(self);
    }
}

char* CDSObjectStoreIndex(
    struct CDSObjectStore* self,
    size_t row,
    size_t column
){
    char* result = &self->data[row][column * self->objSize];
    return result;
}

char* CDSObjectStoreGet(
    struct CDSObjectStore* self
){
    size_t column;
    char* result;

    if(self->freedLen > 0){
        result = self->freed[self->freedLen - 1];
        --self->freedLen;
        if(self->valueFree){
            // The reason it is done here is to simplify freeing the entire
            // objectstore.  Otherwise we would be forced to do one of the
            // following:
            // * sort the freed array and binary search it for every entry,
            // * load freed into an unordered set or use an unordered set to
            //   store the entries in freed
            // So we trade extra memory usage by not cleaning up memory
            // immediately for faster operations and better time complexity
            // and perforamce when freeing the objectstore
            self->valueFree(result);
        }
        return result;
    }

    if(self->column == self->allocSize){
        self->column = 0;
        ++self->row;
        if(self->row == self->dataMax){
            self->dataMax *= 2;
            self->data = (char**)realloc(
                self->data,
                sizeof(char*) * self->dataMax
            );
        }
        self->data[self->row] = _ObjectStoreAllocate(self);
    }

    column = self->column;
    ++self->column;
    result = CDSObjectStoreIndex(self, self->row, column);
    return result;
}

void CDSObjectStoreDelete(
    struct CDSObjectStore* self,
    char* object
){
    if(self->freedLen == self->freedMax){
        self->freedMax *= 2;
        self->freed = (char**)realloc(
            self->freed,
            sizeof(char*) * self->freedMax
        );
    }
    self->freed[self->freedLen] = object;
    ++self->freedLen;
}
