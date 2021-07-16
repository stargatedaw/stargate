from sglib import constants
from sglib.log import LOG
from sgui.daw import shared

def change_sequence(name):
    """ Change the sequence currently being played by the engine
    """
    playlist = constants.DAW_PROJECT.get_playlist()
    lookup = constants.DAW_PROJECT.sequence_uids_by_name()
    if name in lookup:  # Existing
        uid, sequence = lookup[name]
    else:  # Create new
        constants.DAW_PROJECT.create_sequence(name)
    constants.DAW_IPC.change_sequence(uid)
    constants.DAW_CURRENT_SEQUENCE_UID = uid
    shared.CURRENT_SEQUENCE = sequence
    shared.SEQUENCER.open_sequence()
    shared.SEQUENCER.set_playback_pos(0)
    shared.SEQ_WIDGET.scrollbar.setValue(0)

