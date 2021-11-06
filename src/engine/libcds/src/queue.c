#include <stdlib.h>
#include <string.h>

#include "cds/queue.h"


struct CDSQueue* CDSQueueNew(
    size_t objSize,
    size_t initialSize,
    size_t shardSize,
    void (*valueFree)(void*)
){
    struct CDSQueue* queue = (struct CDSQueue*)malloc(sizeof(struct CDSQueue));
    CDSQueueInit(
        queue,
        objSize,
        initialSize,
        shardSize,
        valueFree
    );
    return queue;
}

void CDSQueueInit(
    struct CDSQueue* self,
    size_t objSize,
    size_t initialSize,
    size_t shardSize,
    void (*valueFree)(void*)
){
    *self = (struct CDSQueue){
        .objSize   = objSize,
        .len       = 0,
        .max       = initialSize,
        .shardSize = shardSize,
        .data      = (char**)malloc(sizeof(char*) * initialSize),
        .valueFree = valueFree,
    };

    self->data[0] = (char*)malloc(sizeof(char) * objSize * shardSize);
}

void CDSQueueFree(
    struct CDSQueue* self,
    int freePtr
){
    size_t i, j;
    if(self->valueFree){
        // free the shards that are no longer in use
        for(i = 0; i < self->lptr1; ++i){
            for(j = 0; j < self->shardSize; ++j){
                self->valueFree(&self->data[i][j * self->objSize]);
            }
        }
        // Free the active shard
        for(j = 0; j < self->lptr2; ++j){
            self->valueFree(&self->data[self->lptr1][j * self->objSize]);
        }
    }
    for(i = 0; i <= self->lptr1; ++i){
        free(self->data[i]);
    }
    free(self->data);
    if(freePtr){
        free(self);
    }
}

void CDSQueuePurge(
    struct CDSQueue* self
){
    size_t i, j;

    if(self->rptr1 == 0){
        return;
    }

    for(i = 0; i < self->rptr1; ++i){
        if(self->valueFree){
            for(j = 0; j < self->shardSize; ++j){
               self->valueFree(&self->data[i][j * self->objSize]);
            }
        }
        free(self->data[i]);
    }

    memmove(
        &self->data[0],
        &self->data[self->rptr1],
        sizeof(char*) * (self->lptr1 - self->rptr1 + 1)
    );
    self->lptr1 -= self->rptr1;
    self->rptr1 = 0;
}

void CDSQueueAppend(
    struct CDSQueue* self,
    void* object
){
    memcpy(
        &self->data[self->lptr1][self->lptr2 * self->objSize],
        object,
        self->objSize
    );
    ++self->len;
    ++self->lptr2;
    if(self->lptr2 >= self->shardSize){
        self->lptr2 = 0;
        ++self->lptr1;
        if(self->lptr1 >= self->max){
            self->max *= 2;
            self->data = (char**)realloc(
                self->data,
                sizeof(char*) * self->max
            );
        }
        self->data[self->lptr1] = (char*)malloc(
            sizeof(char) * self->objSize * self->shardSize
        );
    }
}

char* CDSQueuePop(
    struct CDSQueue* self
){
    char* result;
    if(self->len == 0){
        return NULL;
    }
    --self->len;
    result = &self->data[self->rptr1][self->rptr2 * self->objSize];
    ++self->rptr2;
    if(self->rptr2 >= self->shardSize){
        self->rptr2 = 0;
        ++self->rptr1;
    }

    return result;
}

char* CDSQueuePopAlloc(
    struct CDSQueue* self
){
    char* result;
    char* copy;
    if(self->len == 0){
        return NULL;
    }
    copy = (char*)malloc(self->objSize);
    result = CDSQueuePop(self);
    memcpy(
        copy,
        result,
        self->objSize
    );
    CDSQueuePurge(self);

    return copy;
}
