#ifndef UTIL_AUDIO_UTIL
#define UTIL_AUDIO_UTIL

#include "compiler.h"

/*For time(affecting pitch) time stretching...  Since this is done
 offline anyways, it's not super optimized... */
void v_rate_envelope(
    SGPATHSTR * a_file_in,
    SGPATHSTR * a_file_out,
    SGFLT a_start_rate,
    SGFLT a_end_rate
);

/*For pitch(affecting time) pitch shifting...  Since this is done
 offline anyways, it's not super optimized... */
void v_pitch_envelope(
    SGPATHSTR * a_file_in,
    SGPATHSTR * a_file_out,
    SGFLT a_start_pitch,
    SGFLT a_end_pitch
);

#endif
