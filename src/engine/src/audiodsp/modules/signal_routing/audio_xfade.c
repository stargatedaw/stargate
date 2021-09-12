#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"


/*void v_axf_set_xfade(
 * t_audio_xfade *,
 * SGFLT a_point // 0 to 1
 * )
 */
void v_axf_set_xfade(t_audio_xfade * a_axf_ptr, SGFLT a_point){
    a_axf_ptr->in1_mult = 1.0f - a_point;
    a_axf_ptr->in2_mult = a_point;
}

void g_axf_init(t_audio_xfade * f_result, SGFLT a_mid_point){
    f_result->mid_point = a_mid_point;
    f_result->mid_point_50_minus = 50.0f - f_result->mid_point;
    f_result->in1_mult = .5f;
    f_result->in2_mult = .5f;
}

/*t_audio_xfade * g_axf_get_audio_xfade
 * (
 * SGFLT a_mid_point //This is the negative gain at 0.5 for both channels.
 *                   //-3 or -6 is a good value
 * )
 */
t_audio_xfade * g_axf_get_audio_xfade(SGFLT a_mid_point){
    t_audio_xfade * f_result = (t_audio_xfade*)malloc(sizeof(t_audio_xfade));
    g_axf_init(f_result, a_mid_point);
    return f_result;
}

/* SGFLT f_axf_run_xfade(t_audio_xfade * a_axf_ptr, SGFLT a_in1, SGFLT a_in2)
 */
SGFLT f_axf_run_xfade(t_audio_xfade * a_axf_ptr, SGFLT a_in1, SGFLT a_in2){
    return ((a_axf_ptr->in1_mult) * a_in1) + ((a_axf_ptr->in2_mult) * a_in2);
}

