"""
    API for loading and saving project notes (text notes, not MIDI notes)
"""
from sglib import constants


def load():
    return constants.WAVE_EDIT_PROJECT.get_notes()

def save(notes):
    constants.WAVE_EDIT_PROJECT.write_notes(notes)

