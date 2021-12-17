#include "test_wave_edit.h"
#include "wave_edit.h"
#include "worker.h"


void TestWaveEditConfigE2E(){
    int buffer_size = 128;
    SGFLT** buffer = malloc(sizeof(SGFLT*) * 2);
    buffer[0] = malloc(sizeof(SGFLT) * buffer_size);
    buffer[1] = malloc(sizeof(SGFLT) * buffer_size);
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
        "/home/fd/src/github.com/stargateaudio/stargate-sample-pack/"
        "stargate-sample-pack/karoryfer/kicks/kick_Szpaderski_24_open.wav"
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
        "/home/fd/src/github.com/stargateaudio/stargate-sample-pack/"
        "stargate-sample-pack/karoryfer/kicks/kick_marching_20_old.wav"
    );
    v_we_configure(
        WN_CONFIGURE_KEY_WE_SET,
        "0|0|0.0|1000.0|0|0.0|3|0.0|0|0.0|1.0|0.0|1000.0|0|0.0|"
        "1.0|0|5|-24|-24|0|-1|0.0|-1|0.0|0|0|0"
    );
}

void TestWaveEdit(){
    TestWaveEditConfigE2E();
}
