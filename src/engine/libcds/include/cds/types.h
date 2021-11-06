#ifndef CDS_TYPES_H
#define CDS_TYPES_H

/* Forward declarations of structs
 *
 * Allows each file to return other types of structs for a given method
 */

// byte string

struct CDSByteStr;
struct CDSByteStrSplit;

// doubly-linked list

struct CDSDLList;
struct CDSDLListNode;

// hashtable
struct CDSHashTable;

// list
struct CDSList;

// objectstore
struct CDSObjectStore;

// queue
struct CDSQueue;

#endif
