#include "hashtable/test_hash.h"
#include "test_bytestr.h"
#include "test_dl-list.h"
#include "test_fast-sll.h"
#include "test_hashtable.h"
#include "test_list.h"
#include "test_objectstore.h"
#include "test_queue.h"


int main(){
    TestCDSByteStr();
    TestCDSDLList();
    TestCDSFastSLL();
    TestCDSHash();
    TestCDSHashTable();
    TestCDSList();
    TestCDSObjectStore();
    TestCDSQueue();

    return 0;
}
