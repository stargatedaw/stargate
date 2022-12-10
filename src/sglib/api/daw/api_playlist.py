try:
    from sg_py_vendor.pymarshal import pm_assert
except ImportError:
    from pymarshal import pm_assert

from sglib import constants
from sglib.models.daw.playlist import (
    Playlist,
    PlaylistEntry,
    PlaylistPoolEntry,
)

def load():
    """ Load all data for the playlist widget
        @return:
            list, The names of sequences in the playlist, in order of playback
            list, The names of all sequences, sorted alphabetically
    """
    playlist_names = []
    pool_names = []
    playlist = constants.DAW_PROJECT.get_playlist()
    by_uid = playlist.pool_by_uid()
    for entry in playlist.pool:
        pool_names.append(entry.name)
    for entry in playlist.playlist:
        playlist_names.append(
            by_uid[entry.seq_uid].name,
        )
    selected = by_uid[0].name
    return playlist_names, pool_names, selected

def new_seq(name):
    """ Add a new sequence
        @name: str, The name of the sequence
    """
    playlist = constants.DAW_PROJECT.get_playlist()
    uid, sequence = constants.DAW_PROJECT.create_sequence(name)
    playlist.add_to_pool(
        PlaylistPoolEntry(name, uid),
    )
    constants.DAW_PROJECT.save_playlist(playlist)
    return uid, sequence

def playlist_changed(playlist):
    """ Update the playlist from a list of sequence names
        @playlist: The list of str sequence names in the playlist
    """
    _playlist = constants.DAW_PROJECT.get_playlist()
    by_name = _playlist.pool_by_name()
    entries = []
    # Account for empty strings somehow getting in there
    for name in (x for x in playlist if x):
        entry = PlaylistEntry(
            by_name[name].seq_uid,
        )
        entries.append(entry)
    _playlist.playlist = entries
    constants.DAW_PROJECT.save_playlist(_playlist)

def delete_playlist_items(indices):
    """ Delete items from a playlist
        @indices: list-of-int, The selected indices
    """
    playlist = constants.DAW_PROJECT.get_playlist()
    indices.sort(reverse=True)
    for index in indices:
        playlist.playlist.pop(index)
    constants.DAW_PROJECT.save_playlist(playlist)

def change_name(orig_name, new_name):
    """ Rename a Sequence
    """
    playlist = constants.DAW_PROJECT.get_playlist()
    by_name = playlist.pool_by_name()
    pm_assert(
        new_name not in by_name,
        FileExistsError,
        (new_name, by_name),
    )
    pm_assert(
        orig_name in by_name,
        FileNotFoundError,
        (orig_name, by_name),
    )
    entry = by_name[orig_name]
    entry.name = new_name
    constants.DAW_PROJECT.save_playlist(playlist)
    sequence = constants.DAW_PROJECT.get_sequence(entry.seq_uid)
    sequence.name = new_name
    constants.DAW_PROJECT.save_sequence(sequence, uid=entry.seq_uid)

