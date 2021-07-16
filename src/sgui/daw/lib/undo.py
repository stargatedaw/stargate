from sglib import constants
from sgui.daw import painter_path, shared

def undo():
    painter_path.clear_caches()
    return constants.DAW_PROJECT.undo()

def redo():
    painter_path.clear_caches()
    return constants.DAW_PROJECT.redo()

