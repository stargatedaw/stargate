#include "daw.h"
#include "globals.h"
#include "worker.h"


void TestDAWE2E(){
    INSTALL_PREFIX = "..";
    int buffer_size = 128;
    int i;
    struct SamplePair* buffer =
        malloc(sizeof(struct SamplePair) * buffer_size);
    v_activate(
        1,
        "./test_fixtures/projects/daw_e2e",
        44100,
        NULL,
        0
    );
    STARGATE->sample_count = buffer_size;
    v_set_host(SG_HOST_DAW);
    DAW->metronome_enabled = 1;
    v_daw_run_engine(buffer_size, buffer, NULL);
    v_daw_set_playback_mode(DAW, 1, 0.0, 1);
    for(i = 0; i < 10; ++i){
        v_daw_run_engine(buffer_size, buffer, NULL);
    }
    v_daw_set_playback_mode(DAW, 0, 0.0, 1);
    for(i = 0; i < 10; ++i){
        v_daw_run_engine(buffer_size, buffer, NULL);
    }
    free(buffer);
}

void TestDAW(){
    TestDAWE2E();
}
