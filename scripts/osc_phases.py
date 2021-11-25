#!/usr/bin/env python3
import random

print("int OSC_CORE_PHASES[32][7] = {")
for i in range(32):
    print("    {")
    sum_phases = 0
    while sum_phases > 4. or sum_phases < 3.:
        phases = [round(random.random(), 7) for j in range(7)]
        sum_phases = sum(phases)
    print(" " * 8 + ",\n        ".join(str(x) for x in phases))
    print("    },")
print("};")
