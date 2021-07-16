#ifndef TESTLIB_MATH_H
#define TESTLIB_MATH_H

#include "compiler.h"

/* Check that a test result is accurate within @deviance percentage
 * Because floating point math is often not completely accurate
 */
void test_deviance(
    SGFLT result,
    SGFLT expected,
    SGFLT deviance
);

#endif
