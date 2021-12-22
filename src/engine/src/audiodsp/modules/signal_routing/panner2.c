#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/signal_routing/panner2.h"


void g_pn2_init(t_pn2_panner2 * self){
    self->gainL = 1.0f;
    self->gainR = 1.0f;
}

void v_pn2_set(t_pn2_panner2 * self, SGFLT a_pan, SGFLT a_law){
    if(a_pan == 0.0f){
        self->gainL = f_db_to_linear_fast(a_law);
        self->gainR = self->gainL;
    } else if(a_pan == -1.0f){
        self->gainL = 1.0f;
        self->gainR = 0.0f;
    } else if(a_pan == 1.0f){
        self->gainL = 0.0f;
        self->gainR = 1.0f;
    } else if(a_pan < 0.0f){
        self->gainL = f_db_to_linear_fast((1.0f + a_pan) * a_law);
        self->gainR = f_db_to_linear_fast((-1.0f * a_pan) * - 24.0f);
    } else {
        self->gainL = f_db_to_linear_fast(a_pan * - 24.0f);
        self->gainR = f_db_to_linear_fast((1.0f - a_pan) * a_law);
    }
}

void v_pn2_set_normalize(t_pn2_panner2 * self, SGFLT a_pan, SGFLT a_law){
    SGFLT normalize = f_db_to_linear_fast(-a_law);
    v_pn2_set(self, a_pan, a_law);
    self->gainL *= normalize;
    self->gainR *= normalize;
}
