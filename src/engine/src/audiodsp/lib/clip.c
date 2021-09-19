#include "audiodsp/lib/clip.h"

inline SGFLT fclip(SGFLT value, SGFLT min, SGFLT max){
    if(value > max){
        return max;
    } else if(value < min){
        return min;
    }
    return value;
}

inline SGFLT fclip_min(SGFLT value, SGFLT min){
    if(value < min){
        return min;
    }
    return value;
}

inline SGFLT fclip_max(SGFLT value, SGFLT max){
    if(value > max){
        return max;
    }
    return value;
}
