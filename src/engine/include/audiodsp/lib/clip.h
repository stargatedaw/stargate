#ifndef _STARGATE_CLIP_H
#define _STARGATE_CLIP_H

#include "compiler.h"

SGFLT fclip(SGFLT value, SGFLT min, SGFLT max);
SGFLT fclip_min(SGFLT value, SGFLT min);
SGFLT fclip_max(SGFLT value, SGFLT max);

#endif
