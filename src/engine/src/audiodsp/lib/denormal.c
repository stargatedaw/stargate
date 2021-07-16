#include "audiodsp/lib/denormal.h"


/* SGFLT f_remove_denormal(SGFLT a_input)
 *
 * Prevent recursive modules like filters and feedback delays from
 * consuming too much CPU
 */
SGFLT f_remove_denormal(SGFLT a_input)
{
    if((a_input > 1.0e-15) || (a_input < -1.0e-15)){
        return a_input;
    } else {
        return 0.0f;
    }

}

