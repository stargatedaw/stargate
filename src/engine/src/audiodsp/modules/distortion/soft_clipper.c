#include "audiodsp/lib/amp.h"
#include "audiodsp/modules/distortion/soft_clipper.h"


void v_scl_set(
    t_soft_clipper* self,
    SGFLT threshold_db,
    SGFLT shape,
    SGFLT out_db
){
    if(threshold_db != self->threshold_db){
        self->threshold_db = threshold_db;
        self->threshold_linear = f_db_to_linear_fast(threshold_db);
        self->threshold_linear_neg = (self->threshold_linear) * -1.0f;
    }

    if(out_db != self->out_db){
        self->out_linear = f_db_to_linear_fast(out_db);
        self->out_db = out_db;
    }

    self->shape = shape;
}

void v_scl_run(t_soft_clipper* self, SGFLT a_in0, SGFLT a_in1){
    SGFLT temp;
    if(a_in0 > (self->threshold_linear)){
        temp = a_in0 - self->threshold_linear;
        self->output0 = (
            temp * self->shape
        ) + self->threshold_linear;
    } else if(a_in0 < (self->threshold_linear_neg)) {
        temp = a_in0 - (self->threshold_linear_neg);
        self->output0 = (
            temp * self->shape
        ) + self->threshold_linear_neg;
    } else {
        self->output0 = a_in0;
    }

    if(a_in1 > self->threshold_linear){
        temp = a_in1 - self->threshold_linear;
        self->output1 = (
            temp * self->shape
        ) + self->threshold_linear;
    } else if(a_in1 < self->threshold_linear_neg){
        temp = a_in1 - self->threshold_linear_neg;
        self->output1 = (
            temp * self->shape
        ) + self->threshold_linear_neg;
    } else {
        self->output1 = a_in1;
    }

    self->output0 *= self->out_linear;
    self->output1 *= self->out_linear;

    if(self->output0 > 1.0){
        self->output0 = 1.0;
    } else if(self->output0 < -1.0){
        self->output0 = -1.0;
    }

    if(self->output1 > 1.0){
        self->output1 = 1.0;
    } else if(self->output1 < -1.0){
        self->output1 = -1.0;
    }
}

void soft_clipper_init(t_soft_clipper* self){
    self->shape = 1.0f;
    self->output0 = 0.0f;
    self->output1 = 0.0f;
    self->threshold_db = 0.0f;
    self->threshold_linear = 1.0f;
    self->threshold_linear_neg = -1.0f;
    self->out_db = 0.0;
    self->out_linear = 1.0;
}
