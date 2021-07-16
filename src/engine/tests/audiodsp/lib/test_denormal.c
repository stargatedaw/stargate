#include <assert.h>

#include "audiodsp/lib/denormal.h"
#include "compiler.h"
#include "test_denormal.h"


void TestDenormalAll(){
    SGFLT flt;
    flt = f_remove_denormal(1e-16);
    assert(flt == (SGFLT)0.);

    flt = f_remove_denormal(1e-14);
    assert(flt == (SGFLT)1e-14);

    flt = f_remove_denormal(-1e-14);
    assert(flt == (SGFLT)-1e-14);
}
