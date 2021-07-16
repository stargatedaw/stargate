#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/peak_meter.h"


void g_pkm_redux_init(t_pkm_redux * self, SGFLT a_sr)
{
    self->gain_redux = 0.0f;
    self->counter = 0;
    self->count = (int)(a_sr / 30.0f);
}

void v_pkm_redux_lin_reset(t_pkm_redux * self)
{
    self->dirty = 0;
    self->gain_redux = 1.0f;
}

void v_pkm_redux_run(t_pkm_redux * self, SGFLT a_gain)
{
    ++self->counter;
    if(unlikely(self->counter >= self->count))
    {
        self->dirty = 1;
        self->counter = 0;
    }

    if(a_gain < self->gain_redux)
    {
        self->gain_redux = a_gain;
    }
}

void g_pkm_init(t_pkm_peak_meter * f_result)
{
    f_result->value[0] = 0.0f;
    f_result->value[1] = 0.0f;
    f_result->buffer_pos = 0;
    f_result->dirty = 0;
}

t_pkm_peak_meter * g_pkm_get()
{
    t_pkm_peak_meter * f_result;
    lmalloc((void**)(&f_result), sizeof(t_pkm_peak_meter));

    g_pkm_init(f_result);

    return f_result;
}

SGFLT f_pkm_compare(SGFLT a_audio, SGFLT a_peak)
{
    SGFLT f_value = a_audio;

    if(a_audio < 0.0f)
    {
        f_value = a_audio * -1.0f;
    }

    if(f_value > a_peak)
    {
        return f_value;
    }
    else
    {
        return a_peak;
    }
}

/* For the host to call after reading the peak value
 */
void v_pkm_reset(t_pkm_peak_meter * self)
{
    self->dirty = 1;
}

void v_pkm_run(t_pkm_peak_meter * self,
        SGFLT * a_in0, SGFLT * a_in1, int a_count)
{
    if(self->dirty)
    {
        self->dirty = 0;
        self->value[0] = 0.0f;
        self->value[1] = 0.0f;
    }
    self->buffer_pos = 0;
    while(self->buffer_pos < a_count)
    {
        self->value[0] = f_pkm_compare(a_in0[self->buffer_pos], self->value[0]);
        self->value[1] = f_pkm_compare(a_in1[self->buffer_pos], self->value[1]);
        self->buffer_pos += PEAK_STEP_SIZE;
    }
}

