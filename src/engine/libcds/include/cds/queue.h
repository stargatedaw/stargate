#ifndef CDS_QUEUE_H
#define CDS_QUEUE_H

#include "./types.h"


/* A FIFO queue data structure
 * If you need a LIFO/stack, use CDSList{Append,Pop}
 *
 * Note that the underlyihng data is stored in an array-of-arrays rather
 * than a linked list for efficiency and speed.
 *
 * Terminology:
 *   - left:   The side of the queue that objects enter
 *   - right:  The side of the queue that objects leave
 *
 * @objSize:   The sizeof() the object type to be stored in this queue.
 * @shardSize: The count of objects to allocate each 2nd dimension of @data
 * @len:       The length of the queue, specifically the count of objects stored
 * @max:       The lengith of the underlying memory allocated for the queue
 *             before it will have to be grown.  Specifically the max count of
 *             objects that could be stored.
 * @lptr1:     The left pointer for the 1st dimension of @data
 * @lptr2:     The left pointer for the 2nd dimension of @data
 * @rptr1:     The right pointer for the 1st dimension of @data
 * @rptr2:     The right pointer for the 2nd dimension of @data
 * @data:      The objects being stored, as an array-of-arrays of raw bytes
 * @valueFree: A function pointer to be called on each queue item to free any
 *             pointers nested within.  If the object contains no pointers or
 *             the pointers are still referenced by other objects, pass NULL
 *             for this argument.
 */
struct CDSQueue {
    size_t objSize;
    size_t shardSize;
    size_t len;
    size_t max;
    size_t lptr1;
    size_t lptr2;
    size_t rptr1;
    size_t rptr2;
    char** data;
    void (*valueFree)(void*);
};

/* Instantiate a new CDSQueue on the heap
 *
 * @objSize:    The sizeof() the object type to be stored in this queue.
 * @intialSize: The initial ->max of the CDSQueue.  Total capacity of the
 *              queue will be @initialSize * @shardSize, however it will
 *              resize automatically as it grows..
 * @shardSize:  The size of each 2nd dimension of the array-of-arrays
 *              If the intent is to populate with a known number objects
 *              immediately, it makes sense to choose a size >= that number
 *              to prevent costly resize operations.
 * @valueFree:  A function pointer to be called on each queue item to free any
 *              pointers nested within.  If the object contains no pointers or
 *              the pointers are still referenced by other objects, pass NULL
 *              for this argument.
 */
struct CDSQueue* CDSQueueNew(
    size_t objSize,
    size_t initialSize,
    size_t shardSize,
    void (*valueFree)(void*)
);

/* Initialize a queue that has already been allocated
 *
 * @objSize:    The sizeof() the object type to be stored in this queue.
 * @intialSize: The initial ->max of the CDSQueue.  Total capacity of the
 *              queue will be @initialSize * @shardSize, however it will
 *              resize automatically as it grows..
 * @shardSize:  The size of each 2nd dimension of the array-of-arrays
 *              If the intent is to populate with a known number objects
 *              immediately, it makes sense to choose a size >= that number
 *              to prevent costly resize operations.
 * @valueFree:  A function pointer to be called on each queue item to free any
 *              pointers nested within.  If the object contains no pointers or
 *              the pointers are still referenced by other objects, pass NULL
 *              for this argument.
 */
void CDSQueueInit(
    struct CDSQueue* self,
    size_t objSize,
    size_t initialSize,
    size_t shardSize,
    void (*valueFree)(void*)
);

/* Free a CDSQueue and all associated memory
 *
 * @self:      The CDSQueue to free
 * @freePtr:   1 to call free(self), or 0 to not (for when self is passed as
 *             as a pointer with &)
 */
void CDSQueueFree(
    struct CDSQueue* self,
    int freePtr
);

/* Free memory allocated to objects that have already been popped
 *
 * This is not done automatically because the calling code can hold pointers
 * to the data indefinitely.
 */
void CDSQueuePurge(
    struct CDSQueue* self
);

/* Append an item to the queue, growing the queue by 1
 *
 * @self:   The queue to append to
 * @object: The object to append.  It will be dereferenced and copied, based
 *          on the objSize that the queue was created with
 */
void CDSQueueAppend(
    struct CDSQueue* self,
    void* object
);

/* Remove and return the last element of the queue as raw bytes
 * If not intending to use the object, but it contains pointers that
 * should be freed, you should cast and call an appropriate freeing
 * function, BUT DO NOT free the pointer to the object itself.
 *
 * NOTE: You should not mix calls of CDSQueuePop and CDSQueuePopAlloc on the
 *       same queue.
 *
 * @self:   The queue to pop from
 * @return: A pointer to the object in the queue's memory as raw bytes,
 *          or NULL if the queue is empty.
 *          - Do not free the @return pointer itself.
 *          - The pointer becomes invalid next time CDSQueuePurge is called
 */
char* CDSQueuePop(
    struct CDSQueue* self
);

/* Same as CDSQueuePop, but with the following differences:
 * - The object is returned as it's own heap allocation
 * -
 * NOTE: You should not mix calls of CDSQueuePop and CDSQueuePopAlloc on the
 *       same queue.
 *
 * @self:   The queue to pop from
 * @return: A pointer to a copy of the object as raw bytes,
 *          or NULL if the queue is empty.
 *          - You must free the @return pointer.
 */
char* CDSQueuePopAlloc(
    struct CDSQueue* self
);
#endif
