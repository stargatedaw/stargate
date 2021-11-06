#ifndef CDS_OBJECTSTORE_H
#define CDS_OBJECTSTORE_H

#include <stddef.h>

#include "cds/types.h"


/* A generic object store
 * Allocates groups of objects to minimize the number of memory allocations
 * and keep the objects in (virtually) contiguous memory
 *
 * If using to store data structure entry types, call the correspodning
 * Init function on the result of CDSObjectStoreGet() instead of using
 * the entry type's New function to allocate.
 *
 * @objSize:   The sizeof() the objects to be stored
 * @allocSize: The count of objects to allocate per allocation.  Size of the
 *             memory allocation will be @allocSize * @objSize
 * @row:       The current row of @data for the next returned object
 * @column:    The current column of @data for the next returned object
 * @data:      2-dimensional array of objects.  Once all memory is consumed,
 *             another row of objects will be allocated
 * @dataMax:   The size of the current allocation of the first dimension
 *             of @data
 * @freed:     A list of pointers that have been freed and can be re-used.
 * @freedLen:  The current number of freed pointers in @freed
 * @freedMax:  The maximum number of pointers @freed can hold before a
 *             call to realloc is required
 * @valueFree: A function pointer to be called on each object to free any
 *             pointers nested within.  If the object contains no pointers or
 *             the pointers are still referenced by other objects, pass NULL
 *             for this argument.
 */
struct CDSObjectStore{
    size_t objSize;
    size_t allocSize;
    size_t row;
    size_t column;
    char** data;
    size_t dataMax;
    char** freed;
    size_t freedLen;
    size_t freedMax;
    void (*valueFree)(void*);
};

/* Return a new objectstore on the heap
 *
 * @objSize:   The sizeof() the objects to be stored
 * @allocSize: The count of objects to allocate per allocation.  Size of the
 *             memory allocation will be @allocSize * @objSize
 * @valueFree: A function pointer to be called on each object to free any
 *             pointers nested within.  If the object contains no pointers or
 *             the pointers are still referenced by other objects, pass NULL
 *             for this argument.
 */
struct CDSObjectStore* CDSObjectStoreNew(
    size_t objSize,
    size_t allocSize,
    void (*valueFree)(void*)
);

/* Initialize an objectstore on the heap or stack
 *
 * @self:      The objectstore to initialize
 * @objSize:   The sizeof() the objects to be stored
 * @allocSize: The count of objects to allocate per allocation.  Size of the
 *             memory allocation will be @allocSize * @objSize
 * @valueFree: A function pointer to be called on each object to free any
 *             pointers nested within.  If the object contains no pointers or
 *             the pointers are still referenced by other objects, pass NULL
 *             for this argument.
 */
void CDSObjectStoreInit(
    struct CDSObjectStore* self,
    size_t objSize,
    size_t allocSize,
    void (*valueFree)(void*)
);

/* Free an object store and all of it's associated memory
 *
 * @self: The objectstore to free
 */
void CDSObjectStoreFree(
    struct CDSObjectStore* self,
    int freePtr
);

/* Return a pointer to a specific object
 *
 * @self:   The objectstore to index
 * @row:    The row of the object
 * @column: The column of the object
 */
char* CDSObjectStoreIndex(
    struct CDSObjectStore* self,
    size_t row,
    size_t column
);

/* Allocate a new object or re-use a previously deleted object
 *
 * @self: The objectstore to allocate an object from
 */
char* CDSObjectStoreGet(
    struct CDSObjectStore* self
);

/* Delete an object allocated using an objectstore
 * Note that any nested pointers will be freed either when the object is
 * re-used, or when the objectstore is freed
 *
 * @self:   The objectstore that @object belongs to
 * @object: A pointer to the object allocated by CDSObjectStoreGet
 */
void CDSObjectStoreDelete(
    struct CDSObjectStore* self,
    char* object
);

#endif
