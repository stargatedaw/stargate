"""
    API for loading and saving project notes (text notes, not MIDI notes)
"""
from sglib import constants


def load():
    return constants.DAW_PROJECT.get_notes()

def save(notes):
    constants.DAW_PROJECT.write_notes(notes)

