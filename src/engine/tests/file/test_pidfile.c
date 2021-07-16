#include <assert.h>
#include <stdlib.h>

#include "test_pidfile.h"

#include "file/pidfile.h"
#include "files.h"

static void TestPidfileCreateDelete(){
    char path[30] = "./tmp/test_pidfile_all.pid";
    create_pidfile(path);
    assert(i_file_exists(path));
    delete_file(path);
}

static void TestPidfilePath(){
    char* path = pidfile_path();
    free(path);
}

void TestPidfileAll(){
    TestPidfileCreateDelete();
    TestPidfilePath();
}

