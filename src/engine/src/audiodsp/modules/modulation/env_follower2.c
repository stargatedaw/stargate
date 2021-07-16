#include <math.h>

#include "audiodsp/lib/denormal.h"
#include "audiodsp/lib/math.h"
#include "audiodsp/modules/modulation/env_follower2.h"


void g_enf_init(t_enf2_env_follower* self, SGFLT a_sr)
{
    self->envelope = 0.0f;
    self->sample_rate = a_sr;
    self->attack = -1.234f;
    self->release = -1.234f;
}

void v_enf_set(t_enf2_env_follower* self, SGFLT a_attack, SGFLT a_release)
{
    if(self->attack != a_attack)
    {
        self->attack = a_attack;
        self->a_coeff = exp(log(0.01f) / ( a_attack * self->sample_rate));
    }

    if(self->release != a_release)
    {
        self->release = a_release;
        self->r_coeff = exp(log(0.01f) / ( a_release * self->sample_rate));
    }
}

void v_enf_run(t_enf2_env_follower* self, SGFLT a_input)
{
    SGFLT tmp = f_sg_abs(a_input);
    if(tmp > self->envelope)
    {
        self->envelope = self->a_coeff * (self->envelope - tmp) + tmp;
    }
    else
    {
        self->envelope = self->r_coeff * (self->envelope - tmp) + tmp;
    }

    self->envelope = f_remove_denormal(self->envelope);
}

