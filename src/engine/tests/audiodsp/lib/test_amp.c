#include <assert.h>

#include "test_amp.h"
#include "audiodsp/lib/amp.h"
#include "compiler.h"
#include "testlib/math.h"


static void TestDbToLinear(){
    struct TestCase{
        SGFLT arg;
        SGFLT expected;
    };
    struct TestCase TestCases[3] = {
        {0., 1.},
        {-6., 0.5},
        {6., 2.},
    };
    int i;
    SGFLT result;
    struct TestCase* test_case;
    for(i = 0; i < 3; ++i){
        test_case = &TestCases[i];
        result = f_db_to_linear(test_case->arg);
        test_deviance(
            result,
            test_case->expected,
            1.
        );
        // and backwards
        result = f_linear_to_db(test_case->expected);
        test_deviance(
            result,
            test_case->arg,
            1.
        );
    }
}

void TestAmpAll(){
    TestDbToLinear();
}
