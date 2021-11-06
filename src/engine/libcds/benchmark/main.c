#include "./bench_hashtable.h"
#include "./bench_list.h"
#include "./bench_queue.h"


int main(){
    BenchHashTable();
    BenchQueue();
    BenchList();

    return 0;
}
