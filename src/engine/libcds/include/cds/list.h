#ifndef CDS_LIST_H
#define CDS_LIST_H

#include <stddef.h>

#include "./types.h"
#include "cds/comparator.h"


/* A list data structure
 *
 * @objSize:   The sizeof() the object type to be stored in this list.
 * @len:       The length of the list, specifically the count of objects stored
 * @max:       The lengith of the underlying memory allocated for the list
 *             before it will have to be grown.  Specifically the max count of
 *             objects that could be stored.
 * @data:      The objects being stored, as raw bytes
 * @valueFree: A function pointer to be called on each list item to free any
 *             pointers nested within.  If the object contains no pointers or
 *             the pointers are still referenced by other objects, pass NULL
 *             for this argument.
 */
struct CDSList {
    size_t objSize;
    size_t len;
    size_t max;
    char*  data;
    void (*valueFree)(void*);
};

/* Instantiate a new CDSList on the heap
 *
 * @objSize:    The sizeof() the object type to be stored in this list.
 * @intialSize: The initial ->max of the CDSList.  If the intent is to
 *              populate with a known number objects immediately, it makes
 *              sense to choose a size >= that number to prevent costly
 *              resize operations.
 * @valueFree:  A function pointer to be called on each list item to free any
 *              pointers nested within.  If the object contains no pointers or
 *              the pointers are still referenced by other objects, pass NULL
 *              for this argument.
 */
struct CDSList* CDSListNew(
    size_t objSize,
    size_t initialSize,
    void (*valueFree)(void*)
);

/* Initialize a list that is already allocated
 *
 * @objSize:    The sizeof() the object type to be stored in this list.
 * @intialSize: The initial ->max of the CDSList.  If the intent is to
 *              populate with a known number objects immediately, it makes
 *              sense to choose a size >= that number to prevent costly
 *              resize operations.
 * @valueFree:  A function pointer to be called on each list item to free any
 *              pointers nested within.  If the object contains no pointers or
 *              the pointers are still referenced by other objects, pass NULL
 *              for this argument.
 */
void CDSListInit(
    struct CDSList* self,
    size_t objSize,
    size_t initialSize,
    void (*valueFree)(void*)
);

/* Return a new list that is a slice of an existing list
 *
 * @self:  The list to return a slice of
 * @start: The first element for the new list.  This may be a larger number
 *         than @end if @step is a negative number.
 * @end:   Do not include any elements after @end in @return.  However, this
 *         element may not be included if @end - @start is not a multiple of
 *         @step.
 * @step:  Include ever @step'th element after start.  Can be a negative
 *         number to reverse the list
 */
struct CDSList* CDSListSlice(
    struct CDSList* self,
    long start,
    long end,
    long step
);

/* Free a CDSList and all associated memory
 *
 * @self:      The CDSList to free
 * @freePtr:   1 to call free(self), or 0 to not (for when self is passed as
 *             as a pointer with &)
 */
void CDSListFree(
    struct CDSList* self,
    int freePtr
);

/* Return a pointer to a list index
 * This is used for both GET and SET operations, for example:
 *
 * struct MyStruct* myStruct = (struct MyStruct*)CDSListIndex(list, 2);
 * // Use the data structure, or set with:
 * *myStruct = (struct MyStruct){...};
 *
 * @self:   The list to index
 * @index:  A value  < @self->len to index.
 *          Negative indices may be used, for example -1 to index the last
 *          element of the list, -2 for 2nd to last, etc...
 *          If an invalid index is used, this will assert()
 * @return: A void* to the object
 */
void* CDSListIndex(
    struct CDSList* self,
    long index
);

/* Append an item to the end of the list, growing the list by 1
 *
 * @self:   The list to append to
 * @object: The object to append.  It will be dereferenced and copied, based
 *          on the objSize that the list was created with
 */
void CDSListAppend(
    struct CDSList* self,
    void* object
);

/* Append an empty item to the end of the list, growing the list by 1
 * The use-case for this function is allowing the calling code to write
 * directly to the memory rather than instantiating an object on the stack
 * or heap and copying the memory to the data structure.
 * Usually this approach is more efficient.
 *
 * @self:   The list to append to
 * @return: A pointer to the uninitialized memory
 */
char* CDSListAppendEmpty(
    struct CDSList* self
);

/* Remove and return the last element of the list as raw bytes
 * If not intending to use the object, but it contains pointers that
 * should be freed, you should cast and call an appropriate freeing
 * function, BUT DO NOT free the pointer to the object itself.
 *
 * @self:   The list to pop from
 * @return: A pointer to a copy of the object as raw bytes,
 *          or NULL if the list is empty.
 *          - Do not free the @return pointer itself.
 *          - The pointer becomes invalid next time an object is
 *            added to the list.
 */
char* CDSListPop(
    struct CDSList* self
);

/* Remove an item from any index in the list in 0(n)
 *
 * @self:  The list to remove an element from
 * @index: The index of the element to remove
 */
void CDSListRemove(
    struct CDSList* self,
    long index
);

/* Insert an object into the list in O(n)
 *
 * @self:   The list to insert an element into
 * @index:  The index to insert the element at
 * @object: A pointer to the object to insert
 */
void CDSListInsert(
    struct CDSList* self,
    long index,
    void* object
);

/* Append an entire list to another
 *
 * @self:  The list to be appended to
 * @other: The list to be appended from
 */
void CDSListExtend(
    struct CDSList* self,
    struct CDSList* other
);

/* Insertion sort a list in O(n^2)
 * Recommended only for small lists that are known to be nearly completely
 * sorted already, where performance will be O(n)
 *
 * @self:    The list to sort
 * @cmpfunc: A function pointer, see CDSComparatorLTGTET for details
 */
void CDSListInsertionSort(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc
);

/* Merge sort a list in O(n log n)
 * A good general purpose sorting algorithm for most use-cases
 *
 * @self:    The list to sort
 * @cmpfunc: A function pointer, see CDSComparatorLTGTET for details
 */
void CDSListMergeSort(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc
);

/* Search a CDSList for a matching object in O(n)
 *
 * @self:    The list to search
 * @cmpfunc: A function pointer, see CDSComparatorMatch for details
 * @match:   A pointer to an arbitrary object to be passed as the 2nd argument
 *           to @cmpfunc
 * @start:   The index to begin searching at (usually zero)
 * @return:  The index of the first matching value object, or -1 if no matches
 */
long CDSListSearch(
    struct CDSList* self,
    CDSComparatorMatch cmpfunc,
    void* match,
    size_t start
);

/* Binary search a CDSList for a matching object in O(log n)
 * NOTE: The list must be sorted ascending, or this function will likely not
 *       return the correct result.
 *
 * @self:    The list to search
 * @cmpfunc: A function pointer, see CDSComparatorLTGTET for details
 * @match:   A pointer to an arbitrary object to be passed as the 2nd argument
 *           to @cmpfunc
 * @return:  The index of the first matching value object, or -1 if no matches
 */
long CDSListBinarySearch(
    struct CDSList* self,
    CDSComparatorLTGTET cmpfunc,
    void* match
);
#endif
