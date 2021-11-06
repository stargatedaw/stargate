#ifndef TEST_TIME_H
#define TEST_TIME_H

#include <stddef.h>
#include <time.h>

// passed in from Makefile
#ifndef ITERATIONS
    #define ITERATIONS 1000000
#endif

// passed in from Makefile
#ifndef BENCH_SIZE_MB
    #define BENCH_SIZE_MB 100UL
#endif

// for memory constrained benchmarks, attempt to stay below this many bytes
#define BENCH_SIZE (BENCH_SIZE_MB * 1024UL * 1024UL)


/* Estimate how many objects can be allocated without exceeding BENCH_SIZE
 *
 * @objSize: The sizeof() the object(s) to be allocated, add multiple
 *           sizeof()'s together if needed.
 */
size_t BenchObjCount(
    size_t objSize
);

/* Time a function and print YAML performance data to stderr
 *
 * @func: The function to run and time
 * @name: The name of the section in the YAML output, something descriptive
 *        and unique to what happened
 */
void TimeFunc(
    size_t (*func)(),
    char* name
);

/* Time a section of code and print YAML performance data to stderr
 *
 * @start:      The return of a call to clock(); from <time.h> from before the
 *              section of code starts.
 * @end:        The return of a call to clock(); from <time.h> from after the
 *              section of code ends.
 * @name:       The name of the section in the YAML output, something
 *              descriptive and unique to what happened
 * @iterations: The number of operations, used to compute the per-operation
 *              average time.
 */
void TimeSection(
    clock_t start,
    clock_t end,
    char*   name,
    size_t  iterations
);

#endif
