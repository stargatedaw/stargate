#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/signal_routing/dry_wet_pan.h"

void dry_wet_pan_set(
    struct DryWetPan* self,
    SGFLT dry_db,
    SGFLT wet_db,
    SGFLT pan
){
    SGFLT dry_linear, wet_linear;

    if(
        dry_db != self->dry_db
        ||
        wet_db != self->wet_db
        ||
        pan != self->pan
    ){
        self->pan = pan;
        self->dry_db = dry_db;
        self->wet_db = wet_db;

        if(wet_db <= -40){
            wet_linear = 0.0;
        } else {
            wet_linear = f_db_to_linear_fast(wet_db);
        }

        if(dry_db <= -40){
            dry_linear = 0.0;
        } else {
            dry_linear = f_db_to_linear_fast(dry_db);
        }

        if(pan == 0.0){
            self->wet_left = self->wet_right = wet_linear;
            self->dry_left = self->dry_right = dry_linear;
        } else if(pan < 0.0){  // left
            self->dry_left = (1.0 - (pan * -1.0)) * dry_linear;
            self->dry_right = dry_linear;
            self->wet_left = wet_linear;
            self->wet_right = (1.0 - (pan * -1.0)) * wet_linear;
        } else {  // right
            self->dry_left = dry_linear;
            self->dry_right = (1.0 - pan) * dry_linear;
            self->wet_left = (1.0 - pan) * wet_linear;
            self->wet_right = wet_linear;
        }
    }
}

void dry_wet_pan_run(
    struct DryWetPan* self,
    SGFLT dry_left,
    SGFLT dry_right,
    SGFLT wet_left,
    SGFLT wet_right
){
    self->output.left =
        (dry_left * self->dry_left) + (wet_left * self->wet_left);
    self->output.right =
        (dry_right * self->dry_right) + (wet_right * self->wet_right);
}

void dry_wet_pan_init(struct DryWetPan* self){
    self->dry_db = -123456.7;
    self->wet_db = -123456.7;
    self->pan = -123456.7;
}

