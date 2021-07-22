#include <stdint.h>
#include "ds/list.h"

void * shds_alloc(size_t size)
{
    return malloc(size);
}

void shds_free(void *ptr)
{
    free(ptr);
}

void * shds_realloc(void *data, size_t size)
{
    return realloc(data, size);
}

struct ShdsList * shds_list_new(size_t default_size, shds_dtor dtor){
    struct ShdsList * result =
        (struct ShdsList*)shds_alloc(sizeof(struct ShdsList));
    result->dtor = dtor;
    result->max_size = default_size;
    result->len = 0;
    result->data = (void**)shds_alloc(sizeof(void*) * default_size);
    return result;
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

    for(i = 1; i < self->len; ++i)
    {
        for(i2 = i; i2 > 0 && cmpfunc(data[i2], data[i2 - 1]); --i2){
            swap = data[i2 - 1];
            data[i2 - 1] = data[i2];
            data[i2] = swap;
        }
    }
}

void shds_list_grow(struct ShdsList * self){
    self->max_size *= 2;
    self->data = (void**)shds_realloc(
        self->data,
        sizeof(void*) * self->max_size
    );
}
