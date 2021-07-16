#include "models/bench_mystruct.h"
#include "bench_main.h"
#include "./util.h"


int main(){
    BenchMain();
    BenchMyStruct();

    // Just being called for the coverage, not being used in the template
    BenchObjCount(1);

    return 0;
}
