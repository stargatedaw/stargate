"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

from math import log

def pitch_to_hz(a_pitch):
    return (440.0 * pow(2.0,(a_pitch - 57.0) * 0.0833333))

def hz_to_pitch(a_hz):
    return "{}f".format(round((12.0 * log(a_hz * (1.0/440.0), 2.0)) + 57.0, 3))

def db_to_lin(a_value):
    return "{}f".format(round(pow(10.0, (0.05 * a_value)), 3))

f_formant_dict = {
    "soprano a":((800, 1150, 2900, 3900, 4950), (0, -6, -32, -20, -50),  (80, 90, 120, 130, 140)),
    "soprano e":((350, 2000, 2800, 3600, 4950), (0, -20, -15, -40, -56),
                 (60, 100, 120, 150, 200)),
    "soprano i":((270, 2140, 2950, 3900, 4950), (0, -12, -26, -26, -44), (60, 90, 100, 120, 120)),
    "soprano o":((450, 800, 2830, 3800, 4950), (0, -11, -22, -22, -50), (70, 80, 100, 130, 135)),
    "soprano u":((325, 700, 2700, 3800, 4950), (0, -16, -35, -40, -60), (50, 60, 170, 180, 200)),
    "alto a":((800, 1150, 2800, 3500, 4950), (0, -4, -20, -36, -60), (80, 90, 120, 130, 140)),
    "alto e":((400, 1600, 2700, 3300, 4950), (0, -24, -30, -35, -60), (60, 80, 120, 150, 200)),
    "alto i":((350, 1700, 2700, 3700, 4950), (0, -20, -30, -36, -60), (50, 100, 120, 150, 200)),
    "alto o":((450, 800, 2830, 3500, 4950), (0, -9, -16, -28, -55), (70, 80, 100, 130, 135)),
    "alto u":((325, 700, 2530, 3500, 4950), (0, -12, -30, -40, -64), (50, 60, 170, 180, 200)),
    "countertenor a":((660, 1120, 2750, 3000, 3350), (0, -6, -23, -24, -38),
                      (80, 90, 120, 130, 140)),
    "countertenor e":((440, 1800, 2700, 3000, 3300), (0, -14, -18, -20, -20),
                      (70, 80, 100, 120, 120)),
    "countertenor i":((270, 1850, 2900, 3350, 3590), (0, -24, -24, -36, -36),
                      (40, 90, 100, 120, 120)),
    "countertenor o":((430, 820, 2700, 3000, 3300), (0, -10, -26, -22, -34),
                      (40, 80, 100, 120, 120)),
    "countertenor u":((370, 630, 2750, 3000, 3400), (0, -20, -23, -30, -34),
                      (40, 60, 100, 120, 120)),
    "tenor a":((650, 1080, 2650, 2900, 3250), (0, -6, -7, -8, -22),
               (80, 90, 120, 130, 140)),
    "tenor e":((400, 1700, 2600, 3200, 3580), (0, -14, -12, -14, -20),
               (70, 80, 100, 120, 120)),
    "tenor i":((290, 1870, 2800, 3250, 3540), (0, -15, -18, -20, -30), (40, 90, 100, 120, 120)),
    "tenor o":((400, 800, 2600, 2800, 3000), (0, -10, -12, -12, -26), (40, 80, 100, 120, 120)),
    "tenor u":((350, 600, 2700, 2900, 3300), (0, -20, -17, -14, -26), (40, 60, 100, 120, 120)),
    "bass a":((600, 1040, 2250, 2450, 2750), (0, -7, -9, -9, -20), (60, 70, 110, 120, 130)),
    "bass e":((400, 1620, 2400, 2800, 3100), (0, -12, -9, -12, -18), (40, 80, 100, 120, 120)),
    "bass i":((250, 1750, 2600, 3050, 3340), (0, -30, -16, -22, -28), (60, 90, 100, 120, 120)),
    "bass o":((400, 750, 2400, 2600, 2900), (0, -11, -21, -20, -40), (40, 80, 100, 120, 120)),
    "bass u":((350, 600, 2400, 2675, 2950), (0, -20, -32, -28, -36), (40, 80, 100, 120, 120))
}

print("static float formant_table[{}][3][5] = \n{{".format(len(f_formant_dict)))

for k in sorted(list(f_formant_dict.keys())):
    v = f_formant_dict[k]
    f_str = "{{"
    for f_val in v[0]:
        f_str += "{}, ".format(hz_to_pitch(f_val))
    f_str += "}, {"
    for f_val in v[1]:
        f_str += "{}, ".format(db_to_lin(f_val))
    f_str += "}, {"
    for f_val in v[2]:
        f_str += "{}, ".format(round((-140.0 / f_val) + 1.0, 3))
    f_str += "}},"
    print(("\t{} //{}".format(f_str, k)))
print("}")
