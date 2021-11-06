#include <stddef.h>
#include <stdio.h>
#include <time.h>

#include "./util.h"


size_t BenchObjCount(
    size_t objSize
){
    return (size_t)(BENCH_SIZE / objSize);
}

void TimeSection(
    clock_t start,
    clock_t end,
    char*   name,
    size_t  iterations
){
    int i;
    double time_used, units_per_iteration;
    char* time_unit = NULL;
    char time_units[5][20] = {
        "seconds",
        "milliseconds",
        "microseconds",
        "nanoseconds",
        "picoseconds"
    };

    time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
    units_per_iteration = (time_used / (double)(iterations));

    for(i = 0; i < 5; ++i){
        if(units_per_iteration >= 1.){
            time_unit = time_units[i];
            break;
        }
        units_per_iteration *= 1000.;
    }

    fprintf(
        stderr,
	"%s:\n"
        "  iterations: %lu\n"
        "  seconds: %f\n"
        "  average-per-iteration: %f\n"
        "  iteration-unit: %s\n",
	name,
        iterations,
	time_used,
        units_per_iteration,
        time_unit
    );
}

void TimeFunc(
    size_t (*func)(),
    char* name
){
    clock_t start, end;
    size_t iterations;
    start = clock();
    iterations = func();
    end = clock();
    TimeSection(
        start,
        end,
        name,
        iterations
    );
}
