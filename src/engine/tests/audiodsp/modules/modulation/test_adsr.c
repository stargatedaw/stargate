#include "audiodsp/modules/modulation/adsr.h"

#include "test_adsr.h"

static void TestDAHDSRdB(){
    t_adsr adsr;
    int i;
    float sr = 44100.0;

    g_adsr_init(&adsr, sr);
    v_adsr_set_adsr_db(&adsr, 0.1, 0.5, -6.0, 0.5);
    v_adsr_retrigger(&adsr);
    v_adsr_set_delay_time(&adsr, 0.05);
    v_adsr_set_hold_time(&adsr, 0.05);
    for(i = 0; i < (int)(0.04 * sr); ++i){
        v_adsr_run_db(&adsr);
        assert(adsr.output == 0.0);
    }
    for(i = 0; i < (int)(0.12 * sr); ++i){
        v_adsr_run_db(&adsr);
    }
    assert(adsr.output == 1.0);

    for(i = 0; i < (int)(0.6 * sr); ++i){
        v_adsr_run_db(&adsr);
    }
    assert(adsr.output == adsr.s_value);
    assert(adsr.stage == ADSR_STAGE_SUSTAIN);
    v_adsr_release(&adsr);
    for(i = 0; i < (int)(0.51 * sr); ++i){
        v_adsr_run_db(&adsr);
    }
    assert(adsr.output == 0.0);
    assert(adsr.stage == ADSR_STAGE_OFF);
}

static void TestDAHDSR(){
    t_adsr adsr;
    int i;
    float sr = 44100.0;

    g_adsr_init(&adsr, sr);
    v_adsr_set_adsr(&adsr, 0.1, 0.5, 0.5, 0.5);
    v_adsr_retrigger(&adsr);
    v_adsr_set_delay_time(&adsr, 0.05);
    v_adsr_set_hold_time(&adsr, 0.05);
    for(i = 0; i < (int)(0.04 * sr); ++i){
        v_adsr_run(&adsr);
        assert(adsr.output == 0.0);
    }
    for(i = 0; i < (int)(0.12 * sr); ++i){
        v_adsr_run(&adsr);
    }
    assert(adsr.output == 1.0);

    for(i = 0; i < (int)(0.6 * sr); ++i){
        v_adsr_run_db(&adsr);
    }
    assert(adsr.output == adsr.s_value);
    assert(adsr.stage == ADSR_STAGE_SUSTAIN);
    v_adsr_release(&adsr);
    for(i = 0; i < (int)(0.51 * sr); ++i){
        v_adsr_run(&adsr);
    }
    assert(adsr.output == 0.0);
    assert(adsr.stage == ADSR_STAGE_OFF);
}

void TestADSRAll(){
    TestDAHDSRdB();
    TestDAHDSR();
}

