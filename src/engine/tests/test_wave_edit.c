#include "wave_edit.h"
#include "worker.h"


void TestWaveEditConfigE2E(){
    int buffer_size = 128;
    struct SamplePair* buffer =
        malloc(sizeof(struct SamplePair) * buffer_size);
    v_activate(
        1,
        "./test_fixtures/projects/wave_edit_e2e",
        44100,
        NULL,
        0
    );
    STARGATE->sample_count = buffer_size;
    v_set_host(SG_HOST_WAVE_EDIT);
    v_we_configure(
        WN_CONFIGURE_KEY_LOAD_AB_OPEN,
        "./test_fixtures/1.wav"
    );
    v_we_configure(
        WN_CONFIGURE_KEY_WE_SET,
        "0|0|0.0|1000.0|0|0.0|3|0.0|0|0.0|1.0|0.0|1000.0|0|0.0|"
        "1.0|0|5|-24|-24|0|-1|0.0|-1|0.0|0|0|0"
    );
    v_run_wave_editor(buffer_size, buffer, NULL);
    v_we_configure(WN_CONFIGURE_KEY_WN_PLAYBACK, "1");
    v_run_wave_editor(buffer_size, buffer, NULL);
    v_we_configure(WN_CONFIGURE_KEY_WN_PLAYBACK, "0");
    v_we_configure(
        WN_CONFIGURE_KEY_WE_EXPORT,
        "./test_tmp/wave_edit_e2e.wav"
    );
    v_we_configure(
        WN_CONFIGURE_KEY_LOAD_AB_OPEN,
        "./test_fixtures/2.wav"
    );
    v_we_configure(
        WN_CONFIGURE_KEY_WE_SET,
        "0|0|0.0|1000.0|0|0.0|3|0.0|0|0.0|1.0|0.0|1000.0|0|0.0|"
        "1.0|0|5|-24|-24|0|-1|0.0|-1|0.0|0|0|0"
    );
    free(buffer);
}

void TestWaveEdit(){
    TestWaveEditConfigE2E();
}
