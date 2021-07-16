#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/modules/filter/formant_filter.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/filter/svf_stereo.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"

SG_THREAD_LOCAL SGFLT f_formant_pitches[3][10]
 =
{
    {65.7647152829, 64.0195500087, 60.2218660311, 48.5454706023, 54.9116472027,
     58.8633387057, 61.4815007463, 50.3695077237, 59.892097194, 57.0},
    {72.7050324737, 80.6019976328, 81.769564049, 85.5572660335, 83.1263160229,
     76.408607741, 68.1946296497, 68.8021425265, 74.224633736, 71.55592468},
    {86.6556686271, 86.4414926111, 86.937176301, 90.2902566975, 87.4190618187,
     80.2973738117, 86.4414926111, 85.175079641, 86.2972222721, 85.175079641}
};

void g_for_init(t_for_formant_filter * f_result, SGFLT a_sr){
    int f_i = 0;
    int f_i2;

    while(f_i < 3)
    {
        f_i2 = 0;
        while(f_i2 < 2)
        {
            f_result->filters[f_i][f_i2] = g_svf_get(a_sr);
            v_svf_set_res(f_result->filters[f_i][f_i2], -1.5f);
            f_i2++;
        }
        f_i++;
    }

    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->pitch_tmp = 0.0f;
    f_result->last_pos = -99.0f;
    f_result->last_wet = 0.0f;
    g_axf_init(&f_result->xfade, -3.0f);
}

t_for_formant_filter * g_for_formant_filter_get(SGFLT a_sr)
{
    t_for_formant_filter * f_result;

    lmalloc((void**)&f_result, sizeof(t_for_formant_filter));
    g_for_init(f_result, a_sr);
    return f_result;
}

void v_for_formant_filter_set(t_for_formant_filter* a_for, SGFLT a_pos, SGFLT a_wet)
{
    if(a_pos != a_for->last_pos)
    {
        a_for->last_pos = a_pos;
        int iter = 0;

        while(iter < 3)
        {
            a_for->pitch_tmp =
                f_linear_interpolate_ptr(
                    f_formant_pitches[(iter)], a_pos);
            v_svf_set_cutoff_base(
                a_for->filters[(iter)][0], (a_for->pitch_tmp));
            v_svf_set_cutoff_base(
                a_for->filters[(iter)][1], (a_for->pitch_tmp));
            v_svf_set_cutoff(a_for->filters[(iter)][0]);
            v_svf_set_cutoff(a_for->filters[(iter)][1]);
            ++iter;
        }
    }


    if(a_for->last_wet != a_wet)
    {
        a_for->last_wet = a_wet;
        v_axf_set_xfade(&a_for->xfade, a_wet);
    }
}

void v_for_formant_filter_run(
    t_for_formant_filter* a_for,
    SGFLT a_input0,
    SGFLT a_input1
){
    int iter = 0;
    a_for->output0 = 0.0f;
    a_for->output1 = 0.0f;

    while(iter < 3)
    {
        a_for->output0 +=
            v_svf_run_4_pole_bp(a_for->filters[(iter)][0], a_input0);
        a_for->output1 +=
            v_svf_run_4_pole_bp(a_for->filters[(iter)][1], a_input1);
        ++iter;
    }

    a_for->output0 *= 0.33333f;
    a_for->output1 *= 0.33333f;

    a_for->output0 = f_axf_run_xfade(&a_for->xfade, a_input0, a_for->output0);
    a_for->output1 = f_axf_run_xfade(&a_for->xfade, a_input1, a_for->output1);
}


SG_THREAD_LOCAL SGFLT growl_table[25][3][5]
 =
{
    {
        {67.35f, 73.633f, 89.038f, 92.901f, 98.902f},
        {1.0f, 0.631f, 0.1f, 0.016f, 0.001f},
        {-0.75, -0.556, -0.167, -0.077, 0.0}
    }, //alto a
    {
        {55.35f, 79.35f, 88.409f, 91.883f, 98.902f},
        {1.0f, 0.063f, 0.032f, 0.018f, 0.001f},
        {-1.333, -0.75, -0.167, 0.067, 0.3}
    }, //alto e
    {
        {53.038f, 80.4f, 88.409f, 93.863f, 98.902f},
        {1.0f, 0.1f, 0.032f, 0.016f, 0.001f},
        {-1.8, -0.4, -0.167, 0.067, 0.3}
    }, //alto i
    {
        {57.389f, 67.35f, 89.223f, 92.901f, 98.902f},
        {1.0f, 0.355f, 0.158f, 0.04f, 0.002f},
        {-1.0, -0.75, -0.4, -0.077, -0.037}
    }, //alto o
    {
        {51.755f, 65.038f, 87.283f, 92.901f, 98.902f},
        {1.0f, 0.251f, 0.032f, 0.01f, 0.001f},
        {-1.8, -1.333, 0.176, 0.222, 0.3}
    }, //alto u
    {
        {62.37f, 71.892f, 85.252f, 86.726f, 88.726f},
        {1.0f, 0.447f, 0.355f, 0.355f, 0.1f},
        {-1.333, -1.0, -0.273, -0.167, -0.077}
    }, //bass a
    {
        {55.35f, 79.565f, 86.37f, 89.038f, 90.8f},
        {1.0f, 0.251f, 0.355f, 0.251f, 0.126f},
        {-2.5, -0.75, -0.4, -0.167, -0.167}
    }, //bass e
    {
        {47.213f, 80.901f, 87.755f, 90.519f, 92.091f},
        {1.0f, 0.032f, 0.158f, 0.079f, 0.04f},
        {-1.333, -0.556, -0.4, -0.167, -0.167}
    }, //bass i
    {
        {55.35f, 66.233f, 86.37f, 87.755f, 89.646f},
        {1.0f, 0.282f, 0.089f, 0.1f, 0.01f},
        {-2.5, -0.75, -0.4, -0.167, -0.167}
    }, //bass o
    {
        {53.038f, 62.37f, 86.37f, 88.248f, 89.942f},
        {1.0f, 0.1f, 0.025f, 0.04f, 0.016f},
        {-2.5, -0.75, -0.4, -0.167, -0.167}
    }, //bass u
    {
        {64.02f, 73.175f, 88.726f, 90.233f, 92.143f},
        {1.0f, 0.501f, 0.071f, 0.063f, 0.013f},
        {-0.75, -0.556, -0.167, -0.077, 0.0}
    }, //countertenor a
    {
        {57.0f, 81.389f, 88.409f, 90.233f, 91.883f},
        {1.0f, 0.2f, 0.126f, 0.1f, 0.1f},
        {-1.0, -0.75, -0.4, -0.167, -0.167}
    }, //countertenor e
    {
        {48.545f, 81.863f, 89.646f, 92.143f, 93.341f},
        {1.0f, 0.063f, 0.063f, 0.016f, 0.016f},
        {-2.5, -0.556, -0.4, -0.167, -0.167}
    }, //countertenor i
    {
        {56.602f, 67.777f, 88.409f, 90.233f, 91.883f},
        {1.0f, 0.316f, 0.05f, 0.079f, 0.02f},
        {-2.5, -0.75, -0.4, -0.167, -0.167}
    }, //countertenor o
    {
        {54.0f, 63.214f, 88.726f, 90.233f, 92.4f},
        {1.0f, 0.1f, 0.071f, 0.032f, 0.02f},
        {-2.5, -1.333, -0.4, -0.167, -0.167}
    }, //countertenor u
    {
        {67.35f, 73.633f, 89.646f, 94.775f, 98.902f},
        {1.0f, 0.501f, 0.025f, 0.1f, 0.003f},
        {-0.75, -0.556, -0.167, -0.077, 0.0}
    }, //soprano a
    {
        {53.038f, 83.213f, 89.038f, 93.389f, 98.902f},
        {1.0f, 0.1f, 0.178f, 0.01f, 0.002f},
        {-1.333, -0.4, -0.167, 0.067, 0.3}
    }, //soprano e
    {
        {48.545f, 84.384f, 89.942f, 94.775f, 98.902f},
        {1.0f, 0.251f, 0.05f, 0.05f, 0.006f},
        {-1.333, -0.556, -0.4, -0.167, -0.167}
    }, //soprano i
    {
        {57.389f, 67.35f, 89.223f, 94.325f, 98.902f},
        {1.0f, 0.282f, 0.079f, 0.079f, 0.003f},
        {-1.0, -0.75, -0.4, -0.077, -0.037}
    }, //soprano o
    {
        {51.755f, 65.038f, 88.409f, 94.325f, 98.902f},
        {1.0f, 0.158f, 0.018f, 0.01f, 0.001f},
        {-1.8, -1.333, 0.176, 0.222, 0.3}
    }, //soprano u
    {
        {63.755f, 72.545f, 88.085f, 89.646f, 91.618f},
        {1.0f, 0.501f, 0.447f, 0.398f, 0.079f},
        {-0.75, -0.556, -0.167, -0.077, 0.0}
    }, //tenor a
    {
        {55.35f, 80.4f, 87.755f, 91.35f, 93.293f},
        {1.0f, 0.2f, 0.251f, 0.2f, 0.1f},
        {-1.0, -0.75, -0.4, -0.167, -0.167}
    }, //tenor e
    {
        {49.783f, 82.05f, 89.038f, 91.618f, 93.098f},
        {1.0f, 0.178f, 0.126f, 0.1f, 0.032f},
        {-2.5, -0.556, -0.4, -0.167, -0.167}
    }, //tenor i
    {
        {55.35f, 67.35f, 87.755f, 89.038f, 90.233f},
        {1.0f, 0.316f, 0.251f, 0.251f, 0.05f},
        {-2.5, -0.75, -0.4, -0.167, -0.167}
    }, //tenor o
    {
        {53.038f, 62.37f, 88.409f, 89.646f, 91.883f},
        {1.0f, 0.1f, 0.141f, 0.2f, 0.05f},
        {-2.5, -1.333, -0.4, -0.167, -0.167}
    } //tenor u
};

void g_grw_init(t_grw_growl_filter * f_result, SGFLT a_sr)
{
    int f_i;

    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;

    for(f_i = 0; f_i < 5; ++f_i)
    {
        g_svf2_init(&f_result->bands[f_i].filter, a_sr);
        v_svf2_set_res(&f_result->bands[f_i].filter, -1.5f);
        f_result->bands[f_i].amp = 1.0f;
    }

    g_axf_init(&f_result->xfade, -3.0f);

    f_result->last_pos = -99.0f;
    f_result->last_type = 99.99f;
    f_result->last_wet = 0.0f;

}

t_grw_growl_filter * g_grw_growl_filter_get(SGFLT a_sr)
{
    t_grw_growl_filter * f_result;
    lmalloc((void**)&f_result, sizeof(t_grw_growl_filter));
    g_grw_init(f_result, a_sr);
    return f_result;
}

void v_grw_growl_filter_set(t_grw_growl_filter* a_grw, SGFLT a_pos,
    SGFLT a_wet, SGFLT a_type)
{
    if(a_pos != a_grw->last_pos || a_type != a_grw->last_type)
    {
        t_svf2_filter * f_filter;
        a_grw->last_pos = a_pos;
        a_grw->last_type = a_type;
        int iter;
        SGFLT f_pos_f = a_pos + a_type;
        int f_pos = (int)f_pos_f;
        int f_pos_plus_one = f_pos + 1;
        if(f_pos_plus_one > 24)
        {
            f_pos_plus_one = 24;
        }

        SGFLT f_pos_frac = f_pos_f - (SGFLT)f_pos;

        for(iter = 0; iter < 5; ++iter)
        {
            f_filter = &a_grw->bands[iter].filter;
            v_svf2_set_cutoff_base(f_filter,
                f_linear_interpolate(growl_table[f_pos][0][(iter)],
                growl_table[f_pos_plus_one][0][(iter)],
                f_pos_frac) + 12.0f);
            v_svf2_set_res(f_filter,
                f_linear_interpolate(growl_table[f_pos][2][(iter)],
                    growl_table[f_pos_plus_one][2][(iter)], f_pos_frac));
            v_svf2_set_cutoff(f_filter);
            a_grw->bands[iter].amp =
                f_linear_interpolate(growl_table[f_pos][1][(iter)],
                growl_table[f_pos_plus_one][1][(iter)], f_pos_frac);
        }
    }

    if(a_grw->last_wet != a_wet)
    {
        a_grw->last_wet = a_wet;
        v_axf_set_xfade(&a_grw->xfade, a_wet);
    }
}

void v_grw_growl_filter_run(t_grw_growl_filter* a_grw,
        SGFLT a_input0, SGFLT a_input1)
{
    int f_i;
    t_svf2_filter * f_filter;
    SGFLT f_amp;
    a_grw->output0 = 0.0f;
    a_grw->output1 = 0.0f;

    for(f_i = 0; f_i < 5; ++f_i)
    {
        f_filter = &a_grw->bands[f_i].filter;
        f_amp = a_grw->bands[f_i].amp;
        v_svf2_run_2_pole_bp(f_filter, a_input0, a_input1);
        a_grw->output0 += f_filter->output0 * f_amp;
        a_grw->output1 += f_filter->output1 * f_amp;
    }

    a_grw->output0 *= 0.33333f;
    a_grw->output1 *= 0.33333f;

    a_grw->output0 = f_axf_run_xfade(&a_grw->xfade, a_input0, a_grw->output0);
    a_grw->output1 = f_axf_run_xfade(&a_grw->xfade, a_input1, a_grw->output1);
}

