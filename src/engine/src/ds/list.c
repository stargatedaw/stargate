#include <stdint.h>
#include "ds/list.h"

void * shds_alloc(size_t size){
    return malloc(size);
}

void shds_free(void *ptr){
    free(ptr);
}

void* shds_realloc(void *data, size_t size){
    return realloc(data, size);
}

struct ShdsList* shds_list_new(size_t default_size, shds_dtor dtor){
    struct ShdsList * self = (struct ShdsList*)shds_alloc(
        sizeof(struct ShdsList)
    );
    shds_list_init(self, default_size, dtor);
    return self;
}

void shds_list_init(
    struct ShdsList* self,
    size_t default_size,
    shds_dtor dtor
){
    self->dtor = dtor;
    self->max_size = default_size;
    self->len = 0;
    if(default_size){
        self->data = (void**)shds_alloc(sizeof(void*) * default_size);
    } else {
        self->data = NULL;
    }
}

void shds_list_append(struct ShdsList *self, void *value){
    if(self->len >= self->max_size){
        shds_list_grow(self);
    }

    self->data[self->len] = value;
    ++self->len;
}

/* Insertion Sort a list */
void shds_list_isort(struct ShdsList * self, shds_cmpfunc cmpfunc){
    size_t i;
    int64_t i2;
    void *swap;
    void **data = self->data;

    for(i = 1; i < self->len; ++i){
        for(i2 = i; i2 > 0 && cmpfunc(data[i2], data[i2 - 1]); --i2){
            swap = data[i2 - 1];
            data[i2 - 1] = data[i2];
            data[i2] = swap;
        }
    }
}

void shds_list_grow(struct ShdsList * self){
    if(self->data){
        self->max_size *= 2;
        self->data = (void**)shds_realloc(
            self->data,
            sizeof(void*) * self->max_size
        );
    } else {
        self->max_size = 10;
        self->data = (void**)shds_alloc(sizeof(void*) * self->max_size);
    }
}

void shds_list_free(struct ShdsList* self, int free_ptr){
    int i;
    if(self->dtor){
        for(i = 0; i < self->len; ++i){
           self->dtor(self->data[i]);
        }
    }

    shds_free(self->data);

    if(free_ptr){
        shds_free(self);
    }
}

