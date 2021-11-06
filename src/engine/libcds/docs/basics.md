# libcds basics

## Overview

The data structures in libcds achieve generic-ness by treating everything as
raw bytes (`char*`) that can then be cast to and from other pointer types.
This avoids the need for large, unreadable macros that other libraries use.

One specifies the type to the struct by passing the `sizeof()` the type
to the New or Init functions.  Note that variable sized types are not
supported unless:
- `objSize` = a fixed-size of data for each entry.
- `objSize` = `sizeof` a pointer type to be used as a dynamic array.
- `objSize` = `sizeof` a struct type that contains pointers used as dynamic
  arrays.

For example, if `objSize=20`, one could use it as a byte string just like
`char myArray[20]` provided none of the strings are longer than 20 characters
(including NULL terminator byte).  Note that strings shorter than 20 characters
will waste 20-N bytes of space in this example.  Otherwise one can use
`objSize=sizeof(char*)`, with the downside that it will put extra pressure
on your libc memory allocator.

## How to Use

Common functions between the data structures:
- New:  Allocate and initialize a new instance of the data structure on
        the heap and return a pointer to it.  Note that Init does not need
        to be called on pointer.
- Init: Initialize an existing instance of data structure
- Free: Free all memory associated with the data structure.
    - If `valueFree != NULL` was passed to Init or New, valueFree will be
      called on each entry to free any nested pointers.
    - If `freePtr==1`, the `self` pointer will be freed.

See the headers in `include/cds` for struct definitions and functions specific
to each data structure.

## Object Store

The `CDSObjectStore` struct provides large, contiguous blocks of memory for
storing objects.  This results in far fewer memory allocations and less
fragmentation, which can greatly improve performance.

Additionally, some data structures implement an object store to store their
entry structs, and support interleaving their entry struct with it's value
in memory, improving cache performance by keeping both memory allocations on
the same cache line.  Other data structures do not have entry structs and
store all values contiguously.

### Sharing Objects Between Data Structures

An object store is the best way to share objects between data structures.
The below pseudo-code shows the strategy:

```c
size_t size = sizeof(struct MyStruct);
size_t pSize = sizeof(struct MyStruct*);
// The object store is the only data structure with a non-NULL valueFree
// argument.
struct CDSObjectStore* ostore = CDSObjectStoreNew(size, ..., FreeMyStruct);
struct CDSList* list = CDSListNew(pSize, ...);  // NULL for valueFree
struct CDSQueue* queue = CDSQueueNew(pSize, ...);  // NULL for valueFree
// doubly linked list is a special case where the data structure itself is
// backed by an objectstore for it's entries, passing zero tells it not to
// allocate additional memory, and that the pointer field for the value
// will be assigned instead of memcpy'd to
struct CDSDLList* dllist = CDSDLListNew(0, ...);  // NULL for valueFree

struct MyStruct* object = (struct MyStruct*)CDSObjectStoreGet(ostore);
CDSListAppend(list, object);
CDSQueueAppend(queue, object);
CDSDLListInsertAfter(dllist, NULL, object);

// ... do some work ...

CDSDLListFree(...);
CDSQueueFree(...);
CDSListFree(...);
// free the object store after all other data structures it is backing
// are freed
CDSObjectStoreFree(...);
```
