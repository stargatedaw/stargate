#include <assert.h>
#include <math.h>

#include "./math.h"
#include "compiler.h"

void test_deviance(
    SGFLT result,
    SGFLT expected,
    SGFLT deviance
){
    SGFLT diff = fabs(result - expected);
    SGFLT percent = fabs(expected) * deviance * 0.01;
    assert(diff <= percent);
}
