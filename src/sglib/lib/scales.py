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
 "Phrygian Dominant", "Double Harmonic", "All"]

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

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
    13: [ # All
        BASE_NOTE, WHITE_NOTE, WHITE_NOTE,
        WHITE_NOTE, WHITE_NOTE, WHITE_NOTE,
        WHITE_NOTE, WHITE_NOTE, WHITE_NOTE,
        WHITE_NOTE, WHITE_NOTE, WHITE_NOTE],
}


def scale_to_value_list(a_scale_index, a_val_dict):
    return [a_val_dict[x] for x in SCALES[a_scale_index]]

def _scale_to_note_set(key: int, scale):
    result = set()
    key = key % 12
    for note, note_type in zip(range(key, key+12), scale):
        if note_type != BLACK_NOTE:
            result.add(note % 12)
    return result

def notes_to_scales(notes):
    result = []
    notes = {x % 12 for x in notes}
    if len(notes) < 2:
        return [f"Not enough notes: {len(notes)}, need at least 2"]
    for key in range(12):
        for idx, scale in SCALES.items():
            if SCALE_NAMES[idx] == 'All':
                continue
            _note_set = _scale_to_note_set(key, scale)
            if all(x in _note_set for x in notes):
                result.append(f'{NOTE_NAMES[key]} {SCALE_NAMES[idx]}')
    if not result:
        result.append('No keys/scales matched')
    return result

