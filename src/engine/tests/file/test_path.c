#include <string.h>

#include "compiler.h"
#include "file/path.h"
#include "test_main.h"


void TestVPath(){
    char result[1024];
    char expected[] = "/var/lol/something/blah";
    vpath_join(result, 3, "/var/lol", "something", "blah");
    sg_assert(
        !strcmp(result, expected),
        "Expected: %s, got: %s",
        expected,
        result
    );
}

void TestFilePath(){
    TestVPath();
}

