#include "test_audiodsp.h"

#include "audiodsp/lib/test_amp.h"
#include "audiodsp/lib/test_denormal.h"

void TestAudioDSP(){
    TestDenormalAll();
    TestAmpAll();
}
