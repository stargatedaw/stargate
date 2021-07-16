#include "audiodsp/lib/lmalloc.h"
#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/signal_routing/dry_wet.h"

/*void v_dw_set_dry_wet(
 * t_dw_dry_wet* a_dw,
 * SGFLT a_dry_db, //dry value in decibels, typically -50 to 0
 * SGFLT a_wet_db) //wet value in decibels, typically -50 to 0
 */
void v_dw_set_dry_wet(t_dw_dry_wet* a_dw,SGFLT a_dry_db,SGFLT a_wet_db)
{
    if((a_dw->dry_db) != (a_dry_db))
    {
        a_dw->dry_db = a_dry_db;
        a_dw->dry_linear = f_db_to_linear(a_dry_db);
    }

    if((a_dw->wet_db) != (a_wet_db))
    {
        a_dw->wet_db = a_wet_db;
        a_dw->wet_linear = f_db_to_linear(a_wet_db);
    }
}

/* void v_dw_run_dry_wet(
 * t_dw_dry_wet* a_dw,
 * SGFLT a_dry, //dry signal
 * SGFLT a_wet) //wet signal
 */
void v_dw_run_dry_wet(t_dw_dry_wet* a_dw, SGFLT a_dry, SGFLT a_wet)
{
    a_dw->output = ((a_dw->dry_linear) * a_dry) + ((a_dw->wet_linear) * a_wet);
}

t_dw_dry_wet* g_dw_get_dry_wet()
{
    t_dw_dry_wet* f_result;

    lmalloc((void**)&f_result, sizeof(t_dw_dry_wet));

    f_result->wet_db = -50.0f;
    f_result->wet_linear = 0.0f;
    f_result->dry_db = 0.0f;
    f_result->dry_linear = 1.0f;
    f_result->output = 0.0f;

    return f_result;
}
