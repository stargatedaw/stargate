#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "cds/fast-sll.h"


struct CDSFastSLL* CDSFastSLLNew(
    size_t allocSize,
    size_t commonSize,
    void (*valueFree)(struct CDSFastSLLCurrent*)
){
    struct CDSFastSLL* result = (struct CDSFastSLL*)malloc(
        sizeof(struct CDSFastSLL)
    );
    CDSFastSLLInit(
        result,
        allocSize,
        commonSize,
        valueFree
    );
    return result;
}

void CDSFastSLLInit(
    struct CDSFastSLL* self,
    size_t             allocSize,
    size_t             commonSize,
    void (*valueFree)(struct CDSFastSLLCurrent*)
){
    assert(allocSize);
    *self = (struct CDSFastSLL){
        .allocSize  = allocSize,
        .data       = (char*)malloc(allocSize),
        .commonSize = commonSize,
        .length     = 0,
        .valueFree  = valueFree,
    };
}

void CDSFastSLLFree(
    struct CDSFastSLL* self,
    int freePtr
){
    if(self->valueFree){
        CDSFastSLLReset(self);
        while(self->current.value){
            self->valueFree(&self->current);
            CDSFastSLLNext(self);
        }
    }
    free(self->data);
    if(freePtr){
        free(self);
    }
}

void CDSFastSLLNext(
    struct CDSFastSLL* self
){
    if(self->length == 0){
        return;
    }

    ++self->current.index;
    if(self->current.index >= self->length){
        self->current = (struct CDSFastSLLCurrent){
            .node   = NULL,
            .common = NULL,
            .value  = NULL,
            .index  = self->length,
        };
    } else {
        self->current.node = (struct CDSFastSLLNode*)(
            (char*)self->current.node + self->current.node->size
        );
        if(self->commonSize){
            self->current.common = (char*)(
                (char*)self->current.node + sizeof(struct CDSFastSLLNode)
            );
        }
        self->current.value = (char*)(
            (char*)self->current.node
            +
            sizeof(struct CDSFastSLLNode)
            +
            self->commonSize
        );
        self->current.size = (
            self->current.node->size
            -
            sizeof(struct CDSFastSLLNode)
            -
            self->commonSize
        );
    }
}

void CDSFastSLLReset(
    struct CDSFastSLL* self
){
    if(self->length == 0){
        self->current = (struct CDSFastSLLCurrent){};
    } else {
        self->current.index = 0;
        self->current.node = (struct CDSFastSLLNode*)self->data;
        if(self->commonSize){
            self->current.common = (char*)(
                self->data + sizeof(struct CDSFastSLLNode)
            );
        }
        self->current.value = (char*)(
            (char*)self->current.node
            +
            self->commonSize
            +
            sizeof(struct CDSFastSLLNode)
        );
        self->current.size = (
            self->current.node->size
            -
            self->commonSize
            -
            sizeof(struct CDSFastSLLNode)
        );
    }
}

char* CDSFastSLLAppend(
    struct CDSFastSLL* self,
    char*  common,
    size_t size
){
    struct CDSFastSLLNode* nextNode;
    size_t nextNodeSize = (
        sizeof(struct CDSFastSLLNode)
        +
        self->commonSize
        +
        size
    );
    size_t allocSize = self->nextPos + nextNodeSize;

    if(allocSize >= self->allocSize){
        size_t newSize = (self->allocSize * 2) + nextNodeSize;
        char* oldData = self->data;
        self->data = (char*)realloc(self->data, newSize);
        self->allocSize = newSize;
        if(self->current.node){
            self->current.node = (struct CDSFastSLLNode*)(
                ((char*)self->current.node - oldData) + self->data
            );
            if(self->commonSize){
                self->current.common = (char*)(
                    (self->current.common - oldData) + self->data
                );
            }
            self->current.value = (char*)(
                (self->current.value - oldData) + self->data
            );
        }
    }
    nextNode = (struct CDSFastSLLNode*)(
        self->data + self->nextPos
    );
    *nextNode = (struct CDSFastSLLNode){
        .size = nextNodeSize,
    };
    if(self->commonSize){
        memcpy(
            ((char*)nextNode + sizeof(struct CDSFastSLLNode)),
            common,
            self->commonSize
        );
    }

    // Must increment before calling reset
    ++self->length;
    if(self->current.index == 0){
        CDSFastSLLReset(self);
    // -1 because we already incremented length
    } else if(self->current.index == self->length - 1){
        self->current.node = (struct CDSFastSLLNode*)(
            self->data + self->nextPos
        );
        if(self->commonSize){
            self->current.common = (
                (char*)self->current.node + sizeof(struct CDSFastSLLNode)
            );
        }
        self->current.value = (
            (char*)self->current.node
            +
            sizeof(struct CDSFastSLLNode)
            +
            self->commonSize
        );
    }

    self->nextPos += nextNodeSize;

    return (char*)(
        (char*)nextNode
        +
        sizeof(struct CDSFastSLLNode)
        +
        self->commonSize
    );
}

