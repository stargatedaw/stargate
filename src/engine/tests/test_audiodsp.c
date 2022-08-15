#include "test_main.h"

#include "audiodsp/lib/test_amp.h"
#include "audiodsp/lib/test_denormal.h"
#include "audiodsp/lib/test_resampler_linear.h"
#include "audiodsp/modules/modulation/test_adsr.h"

void TestAudioDSP(){
    TestDenormalAll();
    TestAmpAll();
    TestADSRAll();
    TestResamplerLinear();
}
