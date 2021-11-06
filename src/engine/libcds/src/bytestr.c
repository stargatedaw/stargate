#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "cds/bytestr.h"
#include "cds/list.h"


struct CDSByteStr* CDSByteStrNew(
    char* data,
    char assign,
    char freeData
){
    struct CDSByteStr* self = (struct CDSByteStr*)malloc(
        sizeof(struct CDSByteStr)
    );
    CDSByteStrInit(
        self,
        data,
        assign,
        freeData
    );
    return self;
}

void CDSByteStrInit(
    struct CDSByteStr* self,
    char* data,
    char assign,
    char freeData
){
    if(assign){
        self->freeData = freeData;
        self->data = data;
    } else {
        // The data should be freed, so assign 1 instead of freeData
        self->freeData = 1;
        self->data = (char*)malloc(sizeof(char) * strlen(data) + 1);
        strcpy(self->data, data);
    }
    self->len = strlen(data);
}

void CDSByteStrFree(
    struct CDSByteStr* self,
    int freePtr
){
    if(self->freeData){
        free(self->data);
    }
    if(freePtr){
        free(self);
    }
}

struct CDSByteStr* CDSByteStrSlice(
    struct CDSByteStr* self,
    long start,
    long end,
    long step
){
    size_t i, j, size;
    char* result;

    if(start < 0){
        start += self->len;
    }

    if(end < 0){
        end += self->len;
    }

    assert(
        (step > 0 && end >= start)
        ||
        (step < 0 && end <= start)
    );

    if(step > 0){
        size = ((end - start) / step) + 2;
        result = (char*)malloc(sizeof(char) * size);
        result[size - 1] = '\0';

        j = start;
        for(
            i = 0;
            i < (size - 1) && j <= end;
            ++i
        ){
            result[i] = self->data[j];
            j += step;
        }
    } else {
        size = ((start - end) / (step * -1)) + 2;
        result = (char*)malloc(sizeof(char) * size);
        result[size - 1] = '\0';

        j = start;
        for(
            i = 0;
            i < (size - 1) && j >= end;
            ++i
        ){
            result[i] = self->data[j];
            j += step;
        }
    }

    return CDSByteStrNew(
        result,
        1,
        1
    );
}

struct CDSByteStr* CDSByteStrJoin(
    struct CDSByteStr* self,
    struct CDSList*    strings
){
    long i, j, size;
    char* result;
    struct CDSByteStr* s;

    if(strings->len == 0){
        return CDSByteStrNew("", 0, 1);
    }

    size = (strings->len - 1) * self->len;
    for(i = 0; i < strings->len; ++i){
        s = (struct CDSByteStr*)CDSListIndex(strings, i);
        size += s->len;
    }
    size += 1;  // null terminator

    result = (char*)malloc(size);
    result[size - 1] = '\0';

    s = (struct CDSByteStr*)CDSListIndex(strings, 0);
    memcpy(result, s->data, s->len);
    j = s->len;
    for(i = 1; i < strings->len; ++i){
        memcpy(&result[j], self->data, self->len);
        j += self->len;

        s = (struct CDSByteStr*)CDSListIndex(strings, i);
        memcpy(&result[j], s->data, s->len);
        j += s->len;
    }

    return CDSByteStrNew(result, 1, 1);
}

long CDSByteStrSearch(
    struct CDSByteStr* self,
    struct CDSByteStr* substr,
    long start
){
    char* ptr;

    if (start < 0){
        start += self->len;
    }

    ptr = strstr(&self->data[start], substr->data);

    if(ptr){
        return (long)(ptr - self->data);
    } else {
        return -1;
    }
}

int CDSByteStrStartsWith(
    struct CDSByteStr* self,
    struct CDSByteStr* substr
){
    if(strncmp(self->data, substr->data, substr->len) == 0){
        return 1;
    } else {
        return 0;
    }
}

int CDSByteStrEndsWith(
    struct CDSByteStr* self,
    struct CDSByteStr* substr
){
    int result;
    if(substr->len > self->len){
        return 0;
    }
    if(substr->len == 0){
        return 1;
    }

    result = strncmp(
        &self->data[self->len - substr->len],
        substr->data,
        substr->len
    );
    if(result == 0){
        return 1;
    } else {
        return 0;
    }
}

static inline int _IsStripChar(char tmp){
    if(
        tmp == ' '
        ||
        tmp == '\t'
        ||
        tmp == '\r'
        ||
        tmp == '\n'
    ){
        return 1;
    } else {
        return 0;
    }
}

struct CDSByteStr* CDSByteStrStrip(
    struct CDSByteStr* self
){
    size_t start, end, len;
    char tmp;
    char* result;

    for(start = 0; start < self->len; ++start){
        tmp = self->data[start];
        if(!_IsStripChar(tmp)){
            break;
        }
    }
    if(start == self->len){
        return CDSByteStrNew("", 0, 1);
    }

    for(end = self->len - 1; end >= 0; --end){
        tmp = self->data[end];
        if(!_IsStripChar(tmp)){
            break;
        }
    }
    len = (end - start) + 1;
    result = (char*)malloc(len + 1);
    result[len] = '\0';
    strncpy(result, &self->data[start], len);
    return CDSByteStrNew(result, 1, 1);
}
