#ifndef CDS_HASHTABLE_ENTRY_H
#define CDS_HASHTABLE_ENTRY_H

#include "./hash.h"


/* The full entry for a hashtable key/value pair
 *
 * @hash:      The hash of @key
 * @key:       The key
 * @keySize:   The size of @key in bytes
 * @value:     The value
 */
struct CDSHashTableEntry{
    CDSHash  hash;
    char*    key;
    size_t   keySize;
    char*    value;
};

/* Free a key/value pair
 *
 * @self:      The entry to free.  Note that @self itself is not freed, as the
 *             buckets do not contain individual memory allocations for each
 *             bucket.
 * @valueFree: A function pointer to a function that will free the value
 *             associated with @key.
 *             - For data structures that do not contain pointers that need to
 *               be freed, you can pass the stdlib "free" function
 *             - If you do not wish to free the memory, you can pass NULL.
 *             - Otherwise, pass your own custom freeing function
 */
void CDSHashTableEntryFree(
    struct CDSHashTableEntry* self,
    void (*valueFree)(void*)
);

#endif
