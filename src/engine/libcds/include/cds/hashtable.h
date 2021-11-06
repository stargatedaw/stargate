#ifndef CDS_HASHTABLE_H
#define CDS_HASHTABLE_H

#include <stdint.h>

#include "./types.h"
#include "cds/hashtable/bucket.h"
#include "cds/hashtable/hash.h"


/* A hashtable data structure
 *
 * @len:       The number of key/value pairs currently in the hashtable
 * @max:       The number of buckets in the hashtable.  Generally you would only
 *             care about this if debugging performance or memory usage
 * @buckets:   The key/value pair storage
 * @valueFree: A function pointer to a function to free the value.
 *             - For data structures that do not contain pointers that need to
 *               be freed, you can pass the stdlib "free" function
 *             - If you do not wish to free the memory, you can pass NULL.
 *             - Otherwise, pass your own custom freeing function
 */
struct CDSHashTable{
    size_t len;
    size_t max;
    struct CDSHashBucket* buckets;
    void(*valueFree)(void*);
};


/* Create a new hashtable on the heap
 *
 * @initialSize: The initial number of buckets.  This is not the maximum
 *               number of key/value pairs the hashtable can hold before
 *               a resize.  The best case would be
 *               (intiialSize * HASH_BUCKET_SIZE) if the hashing distributed
 *               the keys perfectly evenly, but the worst case is
 *               (HASH_BUCKET_SIZE) if all of the keys land in the same bucket.
 * @valueFree:   A function pointer to a function to free the value.
 *               - For data structures that do not contain pointers that need
 *                 to be freed, you can pass the stdlib "free" function
 *               - If you do not wish to free the memory, you can pass NULL.
 *               - Otherwise, pass your own custom freeing function
 */
struct CDSHashTable* CDSHashTableNew(
    size_t initialSize,
    void(*valueFree)(void*)
);

/* Initialize an existing hashtable on the heap or stack
 *
 * @initialSize: The initial number of buckets.  This is not the maximum
 *               number of key/value pairs the hashtable can hold before
 *               a resize.  The best case would be
 *               (intiialSize * HASH_BUCKET_SIZE) if the hashing distributed
 *               the keys perfectly evenly, but the worst case is
 *               (HASH_BUCKET_SIZE) if all of the keys land in the same bucket.
 * @valueFree:   A function pointer to a function to free the value.
 *               - For data structures that do not contain pointers that need
 *                 to be freed, you can pass the stdlib "free" function
 *               - If you do not wish to free the memory, you can pass NULL.
 *               - Otherwise, pass your own custom freeing function
 */
void CDSHashTableInit(
    struct CDSHashTable* self,
    size_t initialSize,
    void(*valueFree)(void*)
);

/* Free the memory allocated to a hashtable
 *
 * @self:      The hashtable to free
 */
void CDSHashTableFree(
    struct CDSHashTable* self,
    int freePtr
);

/* Resize a hashtable.  Generally you do not want to use this, CDSHashTableSet
 * will call it automatically.  However, you may want to (carefully) shrink
 * a hashtable.
 *
 * @self:        The hashtable to resize
 * @initialSize: The number of buckets the new hashtable will have
 */
void CDSHashTableResize(
    struct CDSHashTable* self,
    size_t initialSize
);

/* Get the key/value pair associated with @key in O(1)
 *
 * @self:    The hashtable to search
 * @hash:    The hash of @key
 * @key:     The key to search for
 * @keySize: The length of @key in bytes
 */
struct CDSHashTableEntry* CDSHashTableGet(
    struct CDSHashTable* self,
    CDSHash hash,
    char*  key,
    size_t keySize
);

/* Set a key/value pair.  Either add or overwrite an existing value in O(1)
 *
 * @self:    The hashtable to set the key/value pair
 * @hash:    The hash of @key
 * @key:     The key to set
 * @keySize: The length of @key in bytes
 * @value:   A pointer to a value
 */
void CDSHashTableSet(
    struct CDSHashTable* self,
    CDSHash hash,
    char*  key,
    size_t keySize,
    void*  value
);

/* De;ete a key/value pair from the hashtable
 *
 * @self:      The hashtable to delete a key/value pair from
 * @hash:      The hash of @key
 * @key:       The key to delete
 * @keySize:   The length of @key in bytes
 */
void CDSHashTableDelete(
    struct CDSHashTable* self,
    CDSHash hash,
    char*  key,
    size_t keySize
);
#endif
