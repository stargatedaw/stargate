#include "file/test_pidfile.h"
#include "test_audiodsp.h"
#include "test_files.h"
#include "test_plugins.h"


int main(){
    TestAudioDSP();
    TestFilesAll();
    TestPidfileAll();
    TestPlugins();

    return 0;
}
