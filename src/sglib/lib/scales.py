# -*- coding: utf-8 -*-
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

BASE_NOTE = 0
WHITE_NOTE = 1
BLACK_NOTE = 2

SCALE_NAMES = ["Major", "Melodic Minor", "Harmonic Minor",
 "Natural Minor", "Pentatonic Major", "Pentatonic Minor",
 "Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian",
 "Phrygian Dominant", "Double Harmonic"]

SCALES = {
    0: [ #Major
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE],
    1: [ #Melodic Minor
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE],
    2: [ #Harmonic Minor
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, BLACK_NOTE, WHITE_NOTE],
    3: [ #Natural Minor
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE],
    4: [ #Pentatonic Major
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, BLACK_NOTE],
    5: [ #Pentatonic Minor
        BASE_NOTE, BLACK_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE],
    6: [ #Dorian
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, WHITE_NOTE, BLACK_NOTE],
    7: [ #Phrygian
        BASE_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE],
    8: [ #Lydian
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE],
    9: [ #Mixolydian
        BASE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, WHITE_NOTE, BLACK_NOTE],
    10: [ #Locrian
        BASE_NOTE, WHITE_NOTE, BLACK_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        WHITE_NOTE, BLACK_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE],
    11: [ #Phrygian Dominant
        BASE_NOTE, WHITE_NOTE, BLACK_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, BLACK_NOTE],
    12: [ #Double Harmonic
        BASE_NOTE, WHITE_NOTE, BLACK_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, WHITE_NOTE, WHITE_NOTE,
        BLACK_NOTE, BLACK_NOTE, WHITE_NOTE],
}


def scale_to_value_list(a_scale_index, a_val_dict):
    return [a_val_dict[x] for x in SCALES[a_scale_index]]
