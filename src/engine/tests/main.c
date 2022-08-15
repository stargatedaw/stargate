#include "test_audiodsp.h"
#include "test_csv.h"
#include "test_daw.h"
#include "test_files.h"
#include "test_plugins.h"
#include "test_wave_edit.h"
#include "test_main.h"


int main(){
    TestAudioDSP();
    TestCSV();
    TestDAW();
    TestFilePath();
    TestFilesAll();
    TestPlugins();
    TestWaveEdit();

    return 0;
}
