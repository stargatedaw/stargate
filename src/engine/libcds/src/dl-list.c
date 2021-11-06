#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "cds/dl-list.h"


struct CDSDLList* CDSDLListNew(
    size_t objSize,
    size_t allocSize,
    void (*valueFree)(void*)
){
    struct CDSDLList* self = (struct CDSDLList*)malloc(
        sizeof(struct CDSDLList)
    );
    CDSDLListInit(
        self,
        objSize,
        allocSize,
        valueFree
    );
    return self;
}

void CDSDLListInit(
    struct CDSDLList* self,
    size_t            objSize,
    size_t            allocSize,
    void (*valueFree)(void*)
){
    *self = (struct CDSDLList){
        .objSize   = objSize,
        .valueFree = valueFree,
    };
    CDSObjectStoreInit(
        &self->objects,
        // allocate the memory for the value immediately after the node
        // itself, hence both.
        sizeof(struct CDSDLListNode) + objSize,
        allocSize,
        NULL  // Handled by the doubly linked list
    );
}

void CDSDLListFree(
    struct CDSDLList* self,
    int freePtr
){
    size_t i;
    struct CDSDLListNode* node;
    struct CDSDLListNode* next;

    node = self->head;
    for(i = 0; i < self->len; ++i){
        if(self->valueFree){
            self->valueFree(node->value);
        }
        next = node->next;
        node = next;
    }

    CDSObjectStoreFree(&self->objects, 0);

    if(freePtr){
        free(self);
    }
}

struct CDSDLListNode* CDSDLListNodeNew(
    struct CDSDLList* self,
    void*             value
){
    struct CDSDLListNode* node = (struct CDSDLListNode*)CDSObjectStoreGet(
        &self->objects
    );
    *node = (struct CDSDLListNode){
        .next  = NULL,
        .prev  = NULL,
        .value = NULL,
    };
    if(self->objSize == 0){
        // assign the pointer directly
        node->value = value;
    } else if(value) {
        // copy to space allocated after the dllist node
        node->value = (char*)node + sizeof(struct CDSDLListNode);
        memcpy(
            node->value,
            value,
            self->objSize
        );
    }  // else leave as NULL
    return node;
}

void CDSDLListNodeFree(
    struct CDSDLList*     self,
    struct CDSDLListNode* node
){
    if(self->valueFree){
        self->valueFree(node->value);
    }
    CDSObjectStoreDelete(
        &self->objects,
        (char*)node
    );
}

void CDSDLListInsertAfter(
    struct CDSDLList*     self,
    struct CDSDLListNode* node,
    void*                 value
){
    struct CDSDLListNode* newNode = CDSDLListNodeNew(self, value);
    assert(node != NULL || self->len == 0);
    ++self->len;

    if(self->len == 1){
        self->head = newNode;
        self->tail = newNode;
        return;
    }

    if(self->tail == node){
        self->tail = newNode;
    }

    if(node->next){
        node->next->prev = newNode;
    }

    newNode->next = node->next;
    node->next = newNode;
    newNode->prev = node;
}

void CDSDLListInsertBefore(
    struct CDSDLList*     self,
    struct CDSDLListNode* node,
    void*                 value
){
    struct CDSDLListNode* newNode = CDSDLListNodeNew(self, value);
    assert(node != NULL || self->len == 0);
    ++self->len;

    if(self->len == 1){
        self->head = newNode;
        self->tail = newNode;
        return;
    }

    if(self->head == node){
        self->head = newNode;
    }

    if(node->prev){
        node->prev->next = newNode;
    }

    newNode->prev = node->prev;
    newNode->next = node;
    node->prev = newNode;
}

void CDSDLListRemove(
    struct CDSDLList*     self,
    struct CDSDLListNode* node
){
    --self->len;
    if(self->valueFree){
        self->valueFree(node->value);
    }

    if(self->len == 0){
        self->head = NULL;
        self->tail = NULL;
        CDSDLListNodeFree(self, node);
        return;
    }

    if(self->head == node){
        self->head = node->next;
    }
    if(self->tail == node){
        self->tail = node->prev;
    }

    if(node->prev){
        node->prev->next = node->next;
    }

    if(node->next){
        node->next->prev = node->prev;
    }

    if(self->valueFree){
        self->valueFree(node);
    }
    CDSDLListNodeFree(self, node);
}

void CDSDLListSwap(
    struct CDSDLList*     self,
    struct CDSDLListNode* oldNode,
    struct CDSDLListNode* newNode,
    int freeOld
){
    newNode->next = oldNode->next;
    newNode->prev = oldNode->prev;
    if(oldNode->next){
        oldNode->next->prev = newNode;
    }
    if(oldNode->prev){
        oldNode->prev->next = newNode;
    }

    if(oldNode == self->head){
        self->head = newNode;
    }
    if(oldNode == self->tail){
        self->tail = newNode;
    }

    if(freeOld){
        if(self->valueFree){
            self->valueFree(oldNode->value);
        }
        CDSDLListNodeFree(self, oldNode);
    }
}
