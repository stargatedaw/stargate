#ifndef CDS_DL_LIST_H
#define CDS_DL_LIST_H

#include <stddef.h>

#include "./objectstore.h"
#include "./types.h"


/* A doubly-linked list
 *
 * @head:      The first node in the list
 * @tail:      The last node in the list
 * @len:       The length of the list
 * @objSize:   The size of the value to be stored.
 *             Setting to 0 will do pointer assignment instead of copying
 *             the adata
 * @valueFree: A function to free removed objects, or NULL if the object does
 *             not contain any pointers that need to be freed.  Note that
 *             @valueFree should not free the pointer itself, only child
 *             allocations.
 * @objects:   Stores the CDSDLListNode's associated with this list
 */
struct CDSDLList{
    struct CDSDLListNode* head;
    struct CDSDLListNode* tail;
    size_t len;
    size_t objSize;
    void (*valueFree)(void*);
    struct CDSObjectStore objects;
};

/* A node in a doubly-linked list
 *
 * @prev:  The previous node in the list (if any)
 * @next:  The next node in the list (if any)
 * @value: The data value associated with this node
 */
struct CDSDLListNode{
    struct CDSDLListNode* prev;
    struct CDSDLListNode* next;
    char*                 value;
};

/* Return a pointer to a new doubly linked list on the heap
 *
 * @objSize:   The sizeof() the objects to be stored in the list
 *             Setting to 0 will do pointer assignment instead of copying
 *             the adata
 * @allocSize: The count of objects to allocate per allocation.  Size of the
 *             memory allocation will be @allocSize * @objSize
 * @valueFree: A function to free removed objects, or NULL if the object does
 *             not contain any pointers that need to be freed.  Note that
 *             @valueFree should not free the pointer itself, only child
 *             allocations.
 */
struct CDSDLList* CDSDLListNew(
    size_t objSize,
    size_t allocSize,
    void (*valueFree)(void*)
);

/* Initialize an existing list
 *
 * @self:       THe doubly linked list to initialize
 * @objSize:    The sizeof() the objects to be stored in the list
 *              Setting to 0 will do pointer assignment instead of copying
 *              the adata
 * @allocSize:  The count of objects to allocate per allocation.  Size of the
 *              memory allocation will be @allocSize * @objSize
 * @valueFree:  A function to free removed objects, or NULL if the object does
 *              not contain any pointers that need to be freed.  Note that
 *              @valueFree should not free the pointer itself, only child
 *              allocations.
 */
void CDSDLListInit(
    struct CDSDLList* self,
    size_t            objSize,
    size_t            allocSize,
    void (*valueFree)(void*)
);

/* Free a doubly linked list
 *
 * @self:    The doubly linked list to free
 * @freePtr: Also call free on @self
 */
void CDSDLListFree(
    struct CDSDLList* self,
    int freePtr
);

/* Create a new node in a doubly linked list without inserting
 * Do not use this node in a different doubly linked list
 *
 * @self:  THe doubly linked list to create a new node for
 * @value: The value associated with thenew list node
 *         This will be copied if @self->objSize > 0
 *         This will be assigned if @self->objSize == 0
 *         This will be ignored if @value == 0
 */
struct CDSDLListNode* CDSDLListNodeNew(
    struct CDSDLList* self,
    void*             value
);

/* Free a doubly linked list node by returning the objectstore
 *
 * @self: The objectstore @node belongs to
 * @node: The node to free
 */
void CDSDLListNodeFree(
    struct CDSDLList*     self,
    struct CDSDLListNode* node
);

/* Insert a new node with @value after @node
 *
 * @self:  The doubly linked list to insert into
 * @node:  The node to insert after
 * @value: The value to insert.  This will be copied to the doubly-linked
 *         list's memory, not assigned
 *         This will be copied if @self->objSize > 0
 *         This will be assigned if @self->objSize == 0
 *         This will be ignored if @value == 0
 */
void CDSDLListInsertAfter(
    struct CDSDLList*     self,
    struct CDSDLListNode* node,
    void*                 value
);

/* Insert a new node with @value before @node
 *
 * @self:  The doubly linked list to insert into
 * @node:  The node to insert before
 * @value: The value to insert.  This will be copied to the doubly-linked
 *         list's memory, not assigned
 *         This will be copied if @self->objSize > 0
 *         This will be assigned if @self->objSize == 0
 *         This will be ignored if @value == 0
 */
void CDSDLListInsertBefore(
    struct CDSDLList*     self,
    struct CDSDLListNode* node,
    void*                 value
);

/* Remove a node from the doubly linked list and free memory if necessary
 *
 * @self: The doubly linked list to remove a node from
 * @node: The node to remove
 */
void CDSDLListRemove(
    struct CDSDLList*     self,
    struct CDSDLListNode* node
);

/* Remove a node from the doubly linked list and replace with another at
 * the same position
 *
 * @self:    The doubly linked list to remove a node from
 * @oldNode: The node to remove
 * @newNode: The node to add
 * @freeOld: Free the memory associated with @oldNode
 */
void CDSDLListSwap(
    struct CDSDLList*     self,
    struct CDSDLListNode* oldNode,
    struct CDSDLListNode* newNode,
    int freeOld
);

#endif
