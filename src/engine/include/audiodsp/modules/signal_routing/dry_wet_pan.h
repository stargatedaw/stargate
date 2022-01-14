#ifndef DRY_WET_PAN_H
#define DRY_WET_PAN_H

#include "compiler.h"

struct DryWetPan {
    SGFLT dry_db;
    SGFLT wet_db;
    SGFLT pan;
    SGFLT dry_left;
    SGFLT dry_right;
    SGFLT wet_left;
    SGFLT wet_right;
    struct SamplePair output;
};

void dry_wet_pan_set(struct DryWetPan*, SGFLT, SGFLT, SGFLT);
void dry_wet_pan_run(struct DryWetPan*, SGFLT, SGFLT, SGFLT, SGFLT);
void dry_wet_pan_init(struct DryWetPan*);

#endif /* DRY_WET_PAN_H */

