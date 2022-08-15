#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "files.h"

static void TestWriteChownReadDelete(){
    char path[50] = "./tmp/file_read_write_delete.txt";
    char text[50] = "TestWriteReadDelete()";
    char buffer[50];

    v_write_to_file(path, text);
#if SG_OS == _OS_LINUX
    chown_file(path);
#endif
    get_string_from_file(
        path,
        50,
        buffer
    );
    assert(!strcmp(text, buffer));
    delete_file(path);
    // Test failing to delete
    delete_file(path);
}

static void TestListDir(){
    g_get_dir_list("./tmp");
}

void TestFilesAll(){
    TestWriteChownReadDelete();
    TestListDir();
}
