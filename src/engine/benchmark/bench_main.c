#include <assert.h>

#include "_main.h"
#include "bench_main.h"

void BenchMain(){
    int retcode = _main();
    assert(retcode == 0);
}
