#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "cds/hashtable/hash.h"
#include "test_hash.h"


void TestCDSHash(){
    TestCDSHashUnique();
}

/* Test that the hashing algorithm produces unique data over
 * a small sample size
 */
void TestCDSHashUnique(){
    char buffer[64];
    size_t iterations = 100;
    size_t i, j;
    CDSHash hashes[iterations];
    for(i = 0; i < iterations; ++i){
        snprintf(
            buffer,
            64,
            "%lu",
            i
        );
        hashes[i] = CDSHashNew(
            buffer,
            strlen(buffer)
        );
        // DOing this the O(n^2) way to avoid creating a dependency
        // on another data structure in this library working correctly
        for(j = 0; j < i; ++j){
            assert(hashes[j] != hashes[i]);
        }
    }
}

