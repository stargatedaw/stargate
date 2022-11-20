#include "audiodsp/lib/clip.h"

SGFLT fclip(SGFLT value, SGFLT min, SGFLT max){
    if(value > max){
        return max;
    } else if(value < min){
        return min;
    }
    return value;
}

SGFLT fclip_min(SGFLT value, SGFLT min){
    if(value < min){
        return min;
    }
    return value;
}

SGFLT fclip_max(SGFLT value, SGFLT max){
    if(value > max){
        return max;
    }
    return value;
}
