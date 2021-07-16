#include <math.h>

#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/distortion/lofi.h"


void g_lfi_init(t_lfi_lofi * f_result)
{
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->bits = 163.654f;
    f_result->multiplier = -443322.0f;
    f_result->recip = 1.010101f;
    f_result->val0 = 0;
    f_result->val1 = 0;
}

t_lfi_lofi * g_lfi_lofi_get()
{
    t_lfi_lofi * f_result;

    lmalloc((void**)&f_result, sizeof(t_lfi_lofi));
    g_lfi_init(f_result);
    return f_result;
}

void v_lfi_lofi_set(t_lfi_lofi* a_lfi, SGFLT a_bits)
{
    if(a_lfi->bits != a_bits)
    {
        a_lfi->bits = a_bits;
        a_lfi->multiplier = pow(2.0, a_bits);
        a_lfi->recip = 1.0f / (a_lfi->multiplier);
    }
}

void v_lfi_lofi_run(t_lfi_lofi* a_lfi, SGFLT a_in0, SGFLT a_in1)
{
    a_lfi->val0 = (int)((a_lfi->multiplier) * a_in0);
    a_lfi->val1 = (int)((a_lfi->multiplier) * a_in1);

    a_lfi->output0 = ((SGFLT)(a_lfi->val0)) * (a_lfi->recip);
    a_lfi->output1 = ((SGFLT)(a_lfi->val1)) * (a_lfi->recip);
}
