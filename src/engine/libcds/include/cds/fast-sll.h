#ifndef CDS_FAST_SLL_H
#define CDS_FAST_SLL_H

#include <stddef.h>

#include "./objectstore.h"
#include "./types.h"

/* Special use-case singly-linked list
 *
 * Useful when you need:
 *   - A disposible, short-lived queue
 *   - That performs well in real-time code
 *   - That does not free old memory until the entire data structure is freed
 *   - That does not allocate memory unless being appended to
 *   - That can accommodate multiple types
 *   - The application and/or hardware is sensitive to cache performance
 *   - The application does not iterate through the queue very quickly
 *
 * Stores metadata and data of arbitrary sizes interleaved in a single
 * allocation of memory.
 */


/* An individual metadata node.
 * @size:
 *   The total size of this node, the aggregate of sizeof(CDSFastSLLNode),
 *   sizeof(common type), and the remainder being the size of the value.
 */
struct CDSFastSLLNode{
    size_t size;
};

/* Used to point to the current item in the data structure
 * @node:
 *   The current node that provided these values
 * @common:
 *   A pointer to the common struct, cast this to the type that was passed in
 *   at creation time.  Will be set to NULL if Next() is called on the last
 *   item in the list, or if @commonSize==0.
 *   If CDSFastSLL->commonSize == 0, this value will always be zero
 * @value:
 *   The value for this node.  Cast to various different types as needed.
 *   Will be set to NULL if Next() is called on the last item in the list.
 * @size:
 *   The size of @value
 * @index:
 *   The index of the current node, starting at zero
 */
struct CDSFastSLLCurrent{
    struct CDSFastSLLNode* node;
    char*  common;
    char*  value;
    size_t size;
    size_t index;
};

/* A fast, disposible singly-linked list
 * @data:
 *   The stored data
 * @allocSize:
 *   The size of @data.  If Append() runs out of memory, this will realloc to
 *   double it's size
 * @commonSize:
 *   The size of the common struct that contains data used by all values, or
 *   zero to not use a common struct.  If @value will be cast to multiple
 *   different types, you should include a type hint field in this struct.
 * @length:
 *   The count of values stored
 * @valueFree:
 *   A function for freeing any nested pointers, or NULL if no nested pointers
 *   exist.
 * @current:
 *   Used for iterating with CDSFastSLLNext, the consuming code uses this for
 *   reference to the current item
 * @nextPos:
 *   The offset from @data of the next node to be appended
 */
struct CDSFastSLL{
    char*  data;
    size_t allocSize;
    size_t commonSize;
    size_t length;
    void (*valueFree)(struct CDSFastSLLCurrent*);
    struct CDSFastSLLCurrent current;
    size_t nextPos;
};

/* Allocate a new CDSFastSLL on the heap
 * @allocSize:
 *   The initial size of @data
 * @commonSize:
 *   THe sizeof() the common struct, or zero if not using a common struct
 * @valueFree:
 *   A function for freeing any nested pointers, or NULL if no nested pointers
 *   exist.
 */
struct CDSFastSLL* CDSFastSLLNew(
    size_t allocSize,
    size_t commonSize,
    void (*valueFree)(struct CDSFastSLLCurrent*)
);

/* Initialize a CDSFastSLL
 * @self:
 *   A pointer to the struct to be initialized
 * @allocSize:
 *   The initial size of @data
 * @commonSize:
 *   THe sizeof() the common struct, or zero if not using a common struct
 * @valueFree:
 *   A function for freeing any nested pointers, or NULL if no nested pointers
 *   exist.
 */
void CDSFastSLLInit(
    struct CDSFastSLL* self,
    size_t             allocSize,
    size_t             commonSize,
    void (*valueFree)(struct CDSFastSLLCurrent*)
);

/* Free a CDSFastSLL
 * @self:
 *   The struct to free
 * @freePtr:
 *   1 to free @self, 0 to not
 */
void CDSFastSLLFree(
    struct CDSFastSLL* self,
    int freePtr
);

/* Set the current node to the next node.
 * value and common pointers will be set to NULL if there is no next node
 * Initially, self->current.value will be NULL.  After the first item has
 * been Appended to the data structure, it will be set to the first item
 * in the data structure.  Subsequent calls to next will advance it to the
 * next item
 */
void CDSFastSLLNext(
    struct CDSFastSLL* self
);

/* Reset the current node to the first node.
 * value and common pointers will be set to NULL if there is no first node
 */
void CDSFastSLLReset(
    struct CDSFastSLL* self
);

/* Append a new entry to the data structure
 * @common:
 *   A pointer to the common data for this entry, or NULL if not using a
 *   common struct
 * @size:
 *   The size of the memory to allocate
 */
char* CDSFastSLLAppend(
    struct CDSFastSLL* self,
    char*  common,
    size_t size
);

#endif
