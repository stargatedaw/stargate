#ifndef _STARGATE_CLIP_H
#define _STARGATE_CLIP_H

#include "compiler.h"

inline SGFLT fclip(SGFLT value, SGFLT min, SGFLT max);
inline SGFLT fclip_min(SGFLT value, SGFLT min);
inline SGFLT fclip_max(SGFLT value, SGFLT max);

#endif
