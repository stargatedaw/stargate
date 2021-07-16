#include "audiodsp/lib/interpolate-linear.h"
#include "audiodsp/lib/lmalloc.h"


/* SGFLT f_linear_interpolate(
 * SGFLT a_a, //item 0
 * SGFLT a_b, //item 1
 * SGFLT a_position)  //position between the 2, range:  0 to 1
 */
SGFLT f_linear_interpolate(
    SGFLT a_a,
    SGFLT a_b,
    SGFLT a_pos
){
    return ((1.0f - a_pos) * a_a) + (a_pos * a_b);
}


/* SGFLT f_linear_interpolate_ptr_wrap(
 * SGFLT * a_table,
 * int a_table_size,
 * SGFLT a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the SGFLT* must be malloc'd
 * to (sizeof(SGFLT) * a_table_size)
 */
SGFLT f_linear_interpolate_ptr_wrap(SGFLT * a_table, int a_table_size,
        SGFLT a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    if(unlikely(int_pos >= a_table_size))
    {
        int_pos -= a_table_size;
    }

    if(unlikely(int_pos_plus_1 >= a_table_size))
    {
        int_pos_plus_1 -= a_table_size;
    }

    if(unlikely(int_pos < 0))
    {
        int_pos += a_table_size;
    }

    if(unlikely(int_pos_plus_1 < 0))
    {
        int_pos_plus_1 += a_table_size;
    }

    SGFLT pos = a_ptr - int_pos;

    return f_linear_interpolate(a_table[int_pos], a_table[int_pos_plus_1], pos);
}

/* SGFLT f_linear_interpolate_ptr_wrap(
 * SGFLT * a_table,
 * SGFLT a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the SGFLT* must be malloc'd
 * to (sizeof(SGFLT) * a_table_size)
 *
 * THIS DOES NOT CHECK THAT YOU PROVIDED A VALID POSITION
 */
SGFLT f_linear_interpolate_ptr(SGFLT * a_table, SGFLT a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    SGFLT pos = a_ptr - int_pos;

    return f_linear_interpolate(a_table[int_pos], a_table[int_pos_plus_1], pos);
}

/* SGFLT f_linear_interpolate_ptr_ifh(
 * SGFLT * a_table,
 * int a_table_size,
 * int a_whole_number,
 * SGFLT a_frac,
 * )
 *
 * For use with the read_head type in Sampler1 Sampler
 */
SGFLT f_linear_interpolate_ptr_ifh(SGFLT * a_table, int a_whole_number,
        SGFLT a_frac)
{
    int int_pos = a_whole_number;
    int int_pos_plus_1 = int_pos + 1;

    SGFLT pos = a_frac;

    return f_linear_interpolate(a_table[int_pos], a_table[int_pos_plus_1], pos);
}

