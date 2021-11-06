#ifndef CDS_HASHTABLE_HASH_H
#define CDS_HASHTABLE_HASH_H

#include <stdint.h>


/* Simple non-cryptographic-grade hash
 *
 */
typedef uint64_t CDSHash;

/* Simple non-cryptographic-grade hash function
 * NOTE:  If the memory pointed to by @data contains pointers, this
 *        will not provide an identical pointer every time if the program
 *        is restarted.
 * NOTE:  For integer types, you can simply cast to CDSHash rather than
 *        hashing as char*
 *
 * @data: A pointer to the object to be hashed
 * @size: The sizeof() the object being pointed to by @data
 */
CDSHash CDSHashNew(
    char   *data,
    size_t  size
);

#endif
