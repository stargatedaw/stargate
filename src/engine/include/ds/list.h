#ifndef UTIL_DS_LIST
#define UTIL_DS_LIST

#include <stddef.h>
#include <stdlib.h>
#include <string.h>

/* Comparison function for sorting algorithms
 *
 * Use 'less than' for ascending sorts and 'greater than' for descending
 *
 * @return 1 for true, or 0 for false */
typedef int (*shds_cmpfunc)(void*, void*);

/* Comparison function for determining less-than/equal/greater-than
 *
 * @return -1 for 'less than', 0 for 'equal' or 1 for 'greater than' */
typedef int (*shds_eqfunc)(void*, void*);

/* Destructor for freeing the memory of an object in a data structure.
 *
 * Pass a NULL pointer to not free the memory, pass 'free',
 * or a custom function */
typedef void (*shds_dtor)(void*);

/* Custom memory allocator.  Given that libshds is a single-header library
 * that is platform-agnostic, implementing a custom memory allocator is
 * an exercise left to the user, this simply wraps malloc by default for
 * maximum portability.
 *
 * Possible optimizations are allocating aligned memory using
 * posix_memalign, or using mmap to allocate hugepages
 *
 * @size The size of the memory to allocate in bytes */
void * shds_alloc(size_t size);

/* This is to realloc as shds_alloc is to malloc
 *
 * @data The existing pointer to reallocate
 * @size The size of the memory to allocate in bytes */
void * shds_realloc(void *data, size_t size);

/* Complement to shds_alloc.  It simply wraps 'free' by default, but can
 * be replaced for instances where that isn't appropriate, such as
 * implementations of shds_alloc that use mmap to allocate hugepages.
 *
 * @ptr A pointer to the memory to be freed */
void shds_free(void *ptr);

/* List data structure */
struct ShdsList {
    /* A dynamic array of void* pointers to the items in the list */
    void **data;
    /* The current length of the list */
    size_t len;
    /* The size of ->data, the list will be grown if ->len exceeds this */
    size_t max_size;
    /* The function used to free values, or NULL to not free values */
    shds_dtor dtor;
};

/* The constructor for the list data structure
 *
 * See shds_list_init for args
 */
struct ShdsList * shds_list_new(size_t default_size, shds_dtor dtor);

/* Initialize a list
 *
 * @self:        A pointer to the list to initialize
 * @default_size The initial maximum size of the list length will be zero
 * @dtor         The destructor to call on the stored values when
 *               freeing the list
 */
void shds_list_init(
    struct ShdsList* self,
    size_t default_size,
    shds_dtor dtor
);
/* Append an object to the end of the list in O(1),
 * with an amoritized worst-case of O(n) if the list must be grown */
void shds_list_append(struct ShdsList *self, void *value);

/* Grow a list by doubling the capacity.
 *
 * This is called automatically by _append() */
void shds_list_grow(struct ShdsList * self);

/* Insertion Sort a list */
void shds_list_isort(struct ShdsList * self, shds_cmpfunc cmpfunc);

void shds_list_free(struct ShdsList* self, int free_ptr);
#endif
