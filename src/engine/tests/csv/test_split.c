#include <assert.h>
#include <stddef.h>
#include <stdlib.h>

#include "csv/split.h"
#include "test_split.h"

void TestSplitStr(){
    char buf[1024];
    const char str[128] = "123|345|432";
    const char* _str = str;
    _str = str_split(_str, buf, '|');
    int one = atoi(buf);
    assert(one == 123);
    _str = str_split(_str, buf, '|');
    int two = atoi(buf);
    assert(two == 345);
    _str = str_split(_str, buf, '|');
    int three = atoi(buf);
    assert(three == 432);
    assert(_str == NULL);
}
