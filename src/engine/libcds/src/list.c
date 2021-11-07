#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "cds/list.h"

static inline void _ListIndexIsValid(
    struct CDSList* self,
    long index
){
    assert(
        index >= 0
        &&
        index < self->len
    );
}

static inline long _ListIndexWrap(
    struct CDSList* self,
    long index
){
    if(index < 0){
        index += self->len;
    }
    return index;
}

static inline void _ListCheckResize(
    struct CDSList* self
){
    if(self->len >= self->max){
        self->max = self->len * 2;
        self->data = realloc(
            self->data,
            self->objSize * self->max
        );
    }
}

struct CDSList* CDSListNew(
    size_t objSize,
    size_t initialSize,
    void (*valueFree)(void*)
){
    struct CDSList* list = (struct CDSList*)malloc(sizeof(struct CDSList));
    CDSListInit(
        list,
        objSize,
        initialSize,
        valueFree
    );
    return list;
}

void CDSListInit(
    struct CDSList* self,
    size_t objSize,
    size_t initialSize,
    void (*valueFree)(void*)
){
    *self = (struct CDSList){
        .objSize   = objSize,
        .len       = 0,
        .max       = initialSize,
        .data      = (char*)malloc(sizeof(char) * objSize * initialSize),
        .valueFree = valueFree,
    };
}

struct CDSList* CDSListSlice(
    struct CDSList* self,
    long start,
    long end,
    long step
){
    long i;
    char* obj;
    size_t initialSize = ((end - start) / step) + 6;
    struct CDSList* list = CDSListNew(
        self->objSize,
        initialSize,
        self->valueFree
    );

    start = _ListIndexWrap(self, start);
    end = _ListIndexWrap(self, end);

    assert(
        (step > 0 && end > start)
        ||
        (step < 0 && end < start)
    );

    if(start < end){
        for(i = start; i <= end && i < self->len; i += step){
            obj = CDSListIndex(self, i);
            CDSListAppend(list, obj);
        }
    } else {
        for(i = start; i >= end && i >= 0; i += step){
            obj = CDSListIndex(self, i);
            CDSListAppend(list, obj);
        }
    }

    return list;
}

void CDSListFree(
    struct CDSList* self,
    int freePtr
){
    if(self->valueFree){
        size_t i;
        void* obj;
        for(i = 0; i < self->len; ++i){
            obj = CDSListIndex(self, i);
            self->valueFree(obj);
        }
    }
    free(self->data);
    if(freePtr){
        free(self);
    }
}

void* CDSListIndex(
    struct CDSList* self,
    long index
){
    index = _ListIndexWrap(self, index);
    _ListIndexIsValid(self, index);
    size_t dataIndex = self->objSize * index;
    return (void*)&self->data[dataIndex];
}

void CDSListAppend(
    struct CDSList* self,
    void* object
){
    char* data = CDSListAppendEmpty(self);
    memcpy(
        data,
        object,
        self->objSize
    );
}

char* CDSListAppendEmpty(
    struct CDSList* self
){
    size_t dataIndex = self->len * self->objSize;
    ++self->len;
    _ListCheckResize(self);
    return &self->data[dataIndex];
}

char* CDSListPop(
    struct CDSList* self
){
    if(self->len == 0){
        return NULL;
    }
    --self->len;
    return &self->data[self->len * self->objSize];
}

void CDSListRemove(
    struct CDSList* self,
    long index
){
    index = _ListIndexWrap(self, index);
    _ListIndexIsValid(self, index);
    if(self->valueFree){
        void* object = CDSListIndex(self, index);
        self->valueFree(object);
    }

    --self->len;

    // Do not shift if they removed the last element in the list
    if(index < self->len){
        memmove(
            &self->data[index * self->objSize],
            &self->data[(index + 1) * self->objSize],
            self->objSize * (self->len - index)
        );
    }
}

void CDSListInsert(
    struct CDSList* self,
    long index,
    void* object
){
    size_t len = self->len;
    index = _ListIndexWrap(self, index);
    _ListIndexIsValid(self, index);
    size_t dataIndex = self->objSize * index;

    ++self->len;
    _ListCheckResize(self);

    // Do not shift if they inserted after the last element in the list
    if(index < len){
        memmove(
            &self->data[(index + 1) * self->objSize],
            &self->data[index * self->objSize],
            self->objSize * (len - index)
        );
    }

    memcpy(
        &self->data[dataIndex],
        object,
        self->objSize
    );
}

void CDSListExtend(
    struct CDSList* self,
    struct CDSList* other
){
    size_t dataIndex = self->len * self->objSize;

    assert(self->objSize == other->objSize);
    self->len += other->len;
    _ListCheckResize(self);

    memcpy(
        &self->data[dataIndex],
        other->data,
        other->objSize * other->len
    );
}

void CDSListInsertionSort(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc
){
    size_t i;
    int64_t j;
    char* swap = (char*)malloc(sizeof(char) * self->objSize);
    char* data = self->data;
    size_t objSize = self->objSize;

    for(i = 1; i < self->len; ++i){
        for(
            j = i;
            j > 0
            &&
            cmpfunc(
                &data[j * objSize],
                &data[(j - 1) * objSize]
            ) == -1;
            --j
        ){
            memcpy(
		swap,
		&data[(j - 1) * objSize],
		objSize
	    );
	    memcpy(
                &data[(j - 1) * objSize],
		&data[j * objSize],
		objSize
	    );
	    memcpy(
	        &data[j * objSize],
		swap,
		objSize
	    );
        }
    }
    free(swap);
}

// merge sort + helpers

void _ListMergeSortPart(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc,
    size_t low,
    size_t high,
    char* temp
);

void _ListMergeSort(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc,
    size_t low,
    size_t mid,
    size_t high,
    char*  temp
);

void CDSListMergeSort(
    struct CDSList * self,
    CDSComparatorLTGTET cmpfunc
){
    char* temp = (char*)malloc(sizeof(char) * self->len * self->objSize);
    _ListMergeSortPart(
        self,
        cmpfunc,
        0,
        self->len - 1,
        temp
    );
    free(temp);
}

void _ListMergeSort(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc,
    size_t low,
    size_t mid,
    size_t high,
    char*  temp
){
    int cmp;
    size_t i, m, k, l;
    char* arr = self->data;

    l = low;
    m = mid + 1;

    for(i = low; (l <= mid) && (m <= high); ++i){
        cmp = cmpfunc(
            &arr[l * self->objSize],
            &arr[m * self->objSize]
        );
        if(cmp < 0){
           memcpy(
               &temp[i * self->objSize],
               &arr[l * self->objSize],
               self->objSize
           );
           ++l;
        } else {
            memcpy(
                &temp[i * self->objSize],
                &arr[m * self->objSize],
                self->objSize
            );
            ++m;
        }
    }

    if(l > mid){
         for(k = m; k <= high; ++k){
            memcpy(
                &temp[i * self->objSize],
                &arr[k * self->objSize],
                self->objSize
            );
            ++i;
         }
    } else {
        for(k = l; k <= mid; ++k){
            memcpy(
                &temp[i * self->objSize],
                &arr[k * self->objSize],
                self->objSize
            );
            ++i;
         }
    }

    for(k = low; k <= high; ++k){
        memcpy(
            &arr[k * self->objSize],
            &temp[k * self->objSize],
            self->objSize
        );
    }
}

void _ListMergeSortPart(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc,
    size_t low,
    size_t high,
    char* temp
){
    size_t mid;

    if(low < high){
        mid = (low + high) / 2;
        _ListMergeSortPart(
            self,
            cmpfunc,
            low,
            mid,
            temp
        );
        _ListMergeSortPart(
            self,
            cmpfunc,
            mid + 1,
            high,
            temp
        );
        _ListMergeSort(
            self,
            cmpfunc,
            low,
            mid,
            high,
            temp
        );
    }
}

// end merge sort + helpers

long CDSListSearch(
    struct CDSList* self,
    CDSComparatorMatch cmpfunc,
    void* match,
    size_t start
){
    size_t i;
    int _match;
    for(i = start; i < self->len; ++i){
        _match = cmpfunc(
            &self->data[i * self->objSize],
            match
        );
        if(_match){
            return i;
        }
    }
    return -1;
}

long CDSListBinarySearch(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc,
    void* match
){
    int cmp = -1;

    long i = 0;
    size_t part;

    for(part = self->len >> 1; part > 0; part >>= 1){
        cmp = cmpfunc(
            &self->data[i * self->objSize],
            match
        );

        if(cmp > 0){
            // The current index is more than @match
            i -= part;
        } else if(cmp < 0){
            // The current index is less than @match
            i += part;
        } else {
            // The current index matches @match
            return i;
        }

        if(i < 0){
            return -1;
        }
    }

    // for the rounding error corner cases when the sum of the bit shifts
    // do not add up to the length of the array

    if(i < self->len && i >= 0){
        cmp = cmpfunc(
            (void*)&self->data[i * self->objSize],
            match
        );
    }

    if(!cmp){
        return i;
    } else if(cmp < 0){
        // The value at the current index is less than @match
        ++i;
        while(cmp < 0 && i < self->len){
            cmp = cmpfunc(
                (void*)&self->data[i * self->objSize],
                match
            );
            if(!cmp){
                return i;
            }
            ++i;
        }
    } else {
        // The value at the current index is greater than @match
        --i;
        while(cmp > 0 && i >= 0){
            cmp = cmpfunc(
                (void*)&self->data[i * self->objSize],
                match
            );
            if(!cmp){
                return i;
            }
            --i;
        }
    }

    return -1;
}
