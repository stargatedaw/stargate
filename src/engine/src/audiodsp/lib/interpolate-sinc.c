#include <math.h>
#include <stdlib.h>

#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/interpolate-sinc.h"
#include "audiodsp/lib/lmalloc.h"


//SGFLT f_sinc_interpolate(t_sinc_interpolator*,SGFLT,int);

/* SGFLT f_sinc_interpolate(
 * t_sinc_interpolator* a_sinc,
 * SGFLT * a_array, //The array to interpolate from
 * SGFLT a_pos) //The position in the array to interpolate
 *
 * This function assumes you added adequate 0.0f's to the beginning and
 * end of the array, it does not check array boundaries
 */
SGFLT f_sinc_interpolate(t_sinc_interpolator  * a_sinc,
        SGFLT * a_array, SGFLT a_pos)
{
    a_sinc->pos_int = (int)a_pos;
    a_sinc->pos_frac = a_pos - (SGFLT)(a_sinc->pos_int);

    return f_sinc_interpolate2(
        a_sinc,a_array,
        a_sinc->pos_int,
        a_sinc->pos_frac
    );
}

SGFLT f_sinc_interpolate2(
    t_sinc_interpolator * a_sinc,
    SGFLT * a_array,
    int a_int_pos,
    SGFLT a_SGFLT_pos
){
    a_sinc->pos_int = a_int_pos;
    a_sinc->pos_frac = a_SGFLT_pos;
    a_sinc->SGFLT_iterator_up = a_sinc->pos_frac * a_sinc->samples_per_point;

    a_sinc->SGFLT_iterator_down = a_sinc->samples_per_point -
        a_sinc->SGFLT_iterator_up;

    a_sinc->result = 0.0f;

    a_sinc->result += f_linear_interpolate_ptr(
        a_sinc->sinc_table,
        a_sinc->SGFLT_iterator_up
    ) * a_array[(a_sinc->pos_int)];

    for(
        a_sinc->i = 1;
        a_sinc->i <= a_sinc->points_div2;
        a_sinc->i += 1
    ){
        a_sinc->result += f_linear_interpolate_ptr_wrap(
            a_sinc->sinc_table,
            a_sinc->table_size,
            a_sinc->SGFLT_iterator_down
        ) * a_array[a_sinc->pos_int - a_sinc->i];
        a_sinc->result += f_linear_interpolate_ptr_wrap(
            a_sinc->sinc_table,
            a_sinc->table_size,
            a_sinc->SGFLT_iterator_up
        ) * a_array[a_sinc->pos_int + a_sinc->i];

        a_sinc->SGFLT_iterator_up += a_sinc->samples_per_point;
        a_sinc->SGFLT_iterator_down += a_sinc->samples_per_point;
    }

    return (a_sinc->result);

}

void g_sinc_init(
    t_sinc_interpolator * f_result,
    int a_points,
    int a_samples_per_point,
    double a_fc,
    double a_sr,
    SGFLT a_normalize_to
){
    double f_cutoff = a_fc / a_sr;

    if (a_points % 2)
    {
        f_result->points_div2 = (((a_points) + 1) / 2);
    }
    else
    {
        f_result->points_div2 = ((a_points) / 2);
    }

    int f_array_size = ((f_result->points_div2) * a_samples_per_point);

    lmalloc(((void**)&(f_result->sinc_table)),
        (sizeof(SGFLT) * (f_array_size)) + (sizeof(SGFLT) * 16));

    f_result->points = a_points;
    f_result->samples_per_point = a_samples_per_point;
    f_result->table_size = f_array_size;

    double f_points = (double)a_points;

    SGFLT f_high_value = 0.0f;

    double f_inc = (1.0f/((double)f_array_size)) * f_points;

    double i;
    int i_int = 0;

    double pi = 3.141592f;

    for(i = ((double)(f_result->points_div2)); i < f_points; i+=f_inc)
    {
        double f_sinc1 = sin((pi*f_cutoff*i));
        double sinclp = (f_sinc1/(pi*i));

        double f_bm2 =
                0.42659f - (0.49656f *(cos((2.0f*pi*i)/(f_points - 1.0f))));
        double f_bm3 =
                (cos((12.5664f * i)/(f_points - 1.0f) ) * .076849) + f_bm2;
        SGFLT f_out = sinclp * f_bm3;

        f_result->sinc_table[i_int] = f_out;
        i_int++;

        if(f_out > f_high_value)
        {
            f_high_value = f_out;
        }

        if(i_int >= f_array_size)
        {
            break;
        }
    }

    for(; i_int < (f_array_size + 16); ++i_int)
    {
        //Padding the end with zeroes to be safe
        f_result->sinc_table[i_int] = 0.0f;
    }

    if(a_normalize_to >= 0.0f)
    {
        SGFLT f_normalize = (a_normalize_to / f_high_value);

        for(i_int = 0; i_int < f_array_size; ++i_int)
        {
            f_result->sinc_table[i_int] =
                (f_result->sinc_table[i_int]) * f_normalize;
        }
    }

}

/* t_sinc_interpolator * g_sinc_get(
 * int a_points, //The number of points to use
 * int a_samples_per_point, //how many array elements per a_point
 * double a_fc,  //cutoff, in hz
 * double sample_rate,
 * SGFLT a_normalize_to) //A value to normalize to, typically 0.5 to 0.9
 */
t_sinc_interpolator * g_sinc_get(int a_points, int a_samples_per_point,
        double a_fc, double a_sr, SGFLT a_normalize_to)
{
    t_sinc_interpolator * f_result;
    lmalloc((void**)&f_result, sizeof(t_sinc_interpolator));

    g_sinc_init(f_result, a_points, a_samples_per_point,
        a_fc, a_sr, a_normalize_to);

    return f_result;

}


void v_ifh_run(t_int_frac_read_head* a_ifh, SGFLT a_ratio)
{
    if((a_ratio) != (a_ifh->last_increment))
    {
        a_ifh->int_increment = (int)a_ratio;
        a_ifh->SGFLT_increment = a_ratio - ((SGFLT)(a_ifh->int_increment));
        a_ifh->last_increment = a_ratio;
    }

    a_ifh->whole_number = (a_ifh->whole_number) + (a_ifh->int_increment);
    a_ifh->fraction = (a_ifh->fraction) + (a_ifh->SGFLT_increment);

    if((a_ifh->fraction) > 1.0f)
    {
        a_ifh->fraction = (a_ifh->fraction) - 1.0f;
        a_ifh->whole_number = (a_ifh->whole_number) + 1;
    }
}

void v_ifh_run_reverse(t_int_frac_read_head* a_ifh, SGFLT a_ratio)
{
    if((a_ratio) != (a_ifh->last_increment))
    {
        a_ifh->int_increment = (int)a_ratio;
        a_ifh->SGFLT_increment = a_ratio - ((SGFLT)(a_ifh->int_increment));
        a_ifh->last_increment = a_ratio;
    }

    a_ifh->whole_number = (a_ifh->whole_number) - (a_ifh->int_increment);
    a_ifh->fraction = (a_ifh->fraction) - (a_ifh->SGFLT_increment);

    if((a_ifh->fraction) < 0.0f)
    {
        a_ifh->fraction = (a_ifh->fraction) + 1.0f;
        a_ifh->whole_number = (a_ifh->whole_number) - 1;
    }
}

void v_ifh_retrigger(t_int_frac_read_head* a_ifh, int a_pos)
{
    a_ifh->whole_number = a_pos;
    a_ifh->fraction = 0.0f;
}


void v_ifh_retrigger_double(t_int_frac_read_head* a_ifh, double a_pos)
{
    a_ifh->whole_number = (int)a_pos;
    a_ifh->fraction = a_pos - ((double)a_ifh->whole_number);
}

void g_ifh_init(t_int_frac_read_head * f_result){
    f_result->SGFLT_increment = 0.0f;
    f_result->fraction = 0.0f;
    f_result->whole_number = 0;
    f_result->int_increment = 1;
    f_result->SGFLT_increment = 0.0f;
    f_result->last_increment = 0.0f;
}

t_int_frac_read_head * g_ifh_get()
{
    t_int_frac_read_head * f_result;

    lmalloc((void**)&f_result, sizeof(t_int_frac_read_head));
    g_ifh_init(f_result);
    return f_result;
}

