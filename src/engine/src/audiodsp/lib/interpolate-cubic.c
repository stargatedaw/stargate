#include "audiodsp/lib/interpolate-cubic.h"
#include "audiodsp/lib/lmalloc.h"


/* SGFLT f_cubic_interpolate(
 * SGFLT a_a, //item 0
 * SGFLT a_b, //item 1
 * SGFLT a_position)  //position between the 2, range:  0 to 1
 */
/*
SGFLT f_cubic_interpolate(SGFLT a_a, SGFLT a_b, SGFLT a_position)
{
    return (((a_a - a_b) * a_position) + a_a);
}
*/


/* SGFLT f_cubic_interpolate_ptr_wrap(
 * SGFLT * a_table,
 * int a_table_size,
 * SGFLT a_ptr,
 * t_cubic_interpolater * a_cubic)
 *
 * This method uses a pointer instead of an array the SGFLT* must be malloc'd
 * to (sizeof(SGFLT) * a_table_size)
 */
SGFLT f_cubic_interpolate_ptr_wrap(
    SGFLT * a_table, 
    int a_table_size,
    SGFLT a_ptr
){
    int int_pos = (int)a_ptr;
    SGFLT mu = (SGFLT)a_ptr - (SGFLT)int_pos;
    SGFLT mu2 = mu * mu;
    int int_pos_plus1 = int_pos + 1;
    int int_pos_minus1 = int_pos - 1;
    int int_pos_minus2 = int_pos - 2;

    if(unlikely(int_pos >= a_table_size))
    {
        int_pos = int_pos - a_table_size;
    }
    else if(unlikely(int_pos < 0))
    {
        int_pos = int_pos + a_table_size;
    }

    if(unlikely(int_pos_plus1 >= a_table_size))
    {
        int_pos_plus1 = int_pos_plus1 - a_table_size;
    }
    else if(unlikely(int_pos_plus1 < 0))
    {
        int_pos_plus1 = int_pos_plus1 + a_table_size;
    }

    if(unlikely(int_pos_minus1 >= a_table_size))
    {
        int_pos_minus1 = int_pos_minus1 - a_table_size;
    }
    else if(unlikely(int_pos_minus1 < 0))
    {
        int_pos_minus1 = int_pos_minus1 + a_table_size;
    }

    if(unlikely(int_pos_minus2 >= a_table_size))
    {
        int_pos_minus2 = int_pos_minus2 - a_table_size;
    }
    else if(unlikely(int_pos_minus2 < 0))
    {
        int_pos_minus2 = int_pos_minus2 + a_table_size;
    }

    SGFLT a[4];
    a[0] =
        a_table[int_pos_plus1] -
        a_table[int_pos] -
        a_table[int_pos_minus2] +
        a_table[int_pos_minus1];
    a[1] =
        a_table[int_pos_minus2] -
        a_table[int_pos_minus1] -
        a[0];
    a[2] =
        a_table[int_pos] -
        a_table[int_pos_minus2];
    a[3] = a_table[int_pos_minus1];

    return a[0] * mu * mu2 + a[1] * mu2 + a[2] * mu + a[3];
}

/* SGFLT f_cubic_interpolate_ptr_wrap(
 * SGFLT * a_table,
 * SGFLT a_ptr,
 * t_cubic_interpolater * a_lin)
 *
 * This method uses a pointer instead of an array the SGFLT* must be
 * malloc'd to (sizeof(SGFLT) * a_table_size)
 *
 * THIS DOES NOT CHECK THAT YOU PROVIDED A VALID POSITION
 */

SGFLT f_cubic_interpolate_ptr(SGFLT * a_table, SGFLT a_ptr){
    int int_pos = (int)a_ptr;
    int int_pos_plus1 = (int_pos) + 1;
    int int_pos_minus1 = (int_pos) - 1;
    int int_pos_minus2 = (int_pos) - 2;

#ifdef NO_HARDWARE
    // Check this when run with no hardware, but otherwise save the CPU.
    // Anything sending a position to this should already know that the
    // position is valid.
    sg_assert(
        int_pos_minus1 >= 0,
        "f_cubic_interpolate_ptr: m1 underrun %i",
        int_pos_minus1
    );
    sg_assert(
        int_pos_minus2 >= 0,
        "f_cubic_interpolate_ptr: m2 underrun %i",
        int_pos_minus2
    );
#endif

    SGFLT mu = a_ptr - (SGFLT)int_pos;

    SGFLT mu2 = (mu) * (mu);
    SGFLT a0 = a_table[int_pos_plus1] - a_table[int_pos] -
            a_table[int_pos_minus2] + a_table[int_pos_minus1];
    SGFLT a1 = a_table[int_pos_minus2] -
            a_table[int_pos_minus1] - a0;
    SGFLT a2 = a_table[int_pos] - a_table[int_pos_minus2];
    SGFLT a3 = a_table[int_pos_minus1];

    return (a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3);
}


/* SGFLT f_cubic_interpolate_ptr_ifh(
 * SGFLT * a_table,
 * int a_table_size,
 * int a_whole_number,
 * SGFLT a_frac,
 * t_lin_interpolater * a_lin)
 *
 * For use with the read_head type in Sampler1 Sampler
 */
SGFLT f_cubic_interpolate_ptr_ifh(
    SGFLT * a_table, 
    int a_whole_number,
    SGFLT a_frac
){
    int int_pos = a_whole_number;
    int int_pos_plus1 = (int_pos) + 1;
    int int_pos_minus1 = (int_pos) - 1;
    int int_pos_minus2 = (int_pos) - 2;

    SGFLT mu = a_frac;

    SGFLT mu2 = (mu) * (mu);
    SGFLT a0 = a_table[int_pos_plus1] - a_table[int_pos] -
            a_table[int_pos_minus2] + a_table[int_pos_minus1];
    SGFLT a1 = a_table[int_pos_minus2] -
            a_table[int_pos_minus1] - a0;
    SGFLT a2 = a_table[int_pos] - a_table[int_pos_minus2];
    SGFLT a3 = a_table[int_pos_minus1];

    return (a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3);
}

