#ifndef CDS_HASHTABLE_BUCKET_H
#define CDS_HASHTABLE_BUCKET_H

#include "./entry.h"
#include "./hash.h"

#ifndef HASH_BUCKET_MAX
    #define HASH_BUCKET_MAX 20
#endif


/* A container for key value pairs.
 * Note that the key/value pairs are in the order their keys were
 * first set, and not otherwise sorted in any way.
 *
 * @len:     THe number of key/value pairs in this bucket
 * @entries: The key/value pairs in this bucket
 */
struct CDSHashBucket{
    size_t len;
    struct CDSHashTableEntry entries[HASH_BUCKET_MAX];
};

/* Retrieve a key/value pair from this bucket.  This is a reasonably fast
 * and efficient process, as the bucket size is bound to HASH_BUCKET_MAX
 *
 * @self:    The hash bucket to search
 * @hash:    The hash to search for
 * @key:     The key to search for
 * @keySize: The length of @key in bytes
 * @return:  A pointer to the key/value pair, or NULL if not found
 */
struct CDSHashTableEntry* CDSHashBucketGet(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*   key,
    size_t  keySize
);

/* Find the index of a key
 *
 * @self:    The hash bucket to search
 * @hash:    The hash to search for
 * @key:     The key to search for
 * @keySize: The length of @key in bytes
 * @return:  The index of the key, or -1 if not found
 */
int CDSHashBucketIndex(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*   key,
    size_t  keySize
);

/* Check if the bucket is already full
 *
 * @self:   The bucket to check
 * @return: 1 if full, or 0 if not full
 */
int CDSHashBucketIsFull(
    struct CDSHashBucket* self
);

/* Set a key/value pair
 *
 * @self:    The hash bucket to set a key/value pair
 * @hash:    The hash to set
 * @key:     The key to set
 * @keySize: The length of @key in bytes
 * @value:   The value to set
 */
void CDSHashBucketSet(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*   key,
    size_t  keySize,
    void*   value
);

/* Delete a key/value pair from a hash bucket
 *
 * @self:      The hash bucket to delete a key/value pair from
 * @hash:      The hash to delete
 * @key:       The key to delete
 * @keySize:   The length of @key in bytes
 * @valueFree: A function pointer to a function that will free the value
 *             associated with @key.
 *             - For data structures that do not contain pointers that need to
 *               be freed, you can pass the stdlib "free" function
 *             - If you do not wish to free the memory, you can pass NULL.
 *             - Otherwise, pass your own custom freeing function
 */
int CDSHashBucketDelete(
    struct CDSHashBucket* self,
    CDSHash hash,
    char*  key,
    size_t keySize,
    void(*valueFree)(void*)
);
#endif
