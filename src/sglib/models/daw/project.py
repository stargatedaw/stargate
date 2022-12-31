from . import _shared
from .atm_sequence import DawAtmRegion
from .audio_item import DawAudioItem
from .item import item
from .seq_item import sequencer_item
from .sequencer import sequencer
from sglib import constants
from sglib.math import clip_value
from sglib.models.daw.playlist import Playlist
from sglib.models.daw.routing import MIDIRoutes, RoutingGraph
from sglib.models.stargate import AudioInputTracks
from sglib import constants
from sglib.models.project.abstract import AbstractProject
from sglib.models.track_plugin import track_plugin, track_plugins
from sglib.models.stargate import *
from sglib.lib import history
from sglib.lib import util
from sglib.lib.util import *
from sglib.lib.translate import _
from sglib.log import LOG
import copy
import math
import os
import re
import shutil

try:
    from sg_py_vendor.pymarshal.json import *
except ImportError:
    from pymarshal.json import *


folder_daw = os.path.join("projects", "daw")
folder_items = os.path.join(folder_daw, "items")
folder_tracks = os.path.join(folder_daw, "tracks")
folder_automation = os.path.join(folder_daw, 'automation')

FOLDER_SONGS = os.path.join(folder_daw, "songs")
FILE_PLAYLIST = os.path.join(folder_daw, 'playlist.json')
file_sequences_atm = os.path.join(folder_daw, "automation.txt")
file_routing_graph = os.path.join(folder_daw, "routing.txt")
file_midi_routing = os.path.join(
    folder_daw,
    "midi_routing.txt",
)
file_pyitems = os.path.join(folder_daw, "items.txt")
file_takes = os.path.join(folder_daw, "takes.txt")
file_pytracks = os.path.join(folder_daw, "tracks.txt")
file_pyinput = os.path.join(folder_daw, "input.txt")
file_notes = os.path.join(folder_daw, "notes.txt")

class DawProject(AbstractProject):
    def __init__(self, a_with_audio):
        self.undo_context = 0
        self.TRACK_COUNT = _shared.TRACK_COUNT_ALL
        self.last_item_number = 1
        self.clear_history()
        self.suppress_updates = False
        self._items_dict_cache = None
        self._sequence_cache = {}
        self._item_cache = {}

    def quirks(self):
        """ Make modifications to the project folder format as needed, to
            bring old projects up to date on format changes
        """
        # TODO Stargate v2: Remove all existing quirks
        self._quirk_per_song_automation()

    def _quirk_per_song_automation(self):
        """ When the song list feature was implemented, this was overlooked,
            and automation was shared between all songs, which is never really
            ideal, and often just bad.  So copy automation.txt for the
            automation folder for each song uid, as this will be equivalent
            to what already existed, and not delete somebody's automation
        """
        if not os.path.isfile(self.automation_file):
            return
        LOG.info('Migrating project to per-song automation files')
        uids = [os.path.basename(x) for x in os.listdir(self.song_folder)]
        for uid in uids:
            path = os.path.join(self.automation_folder, uid)
            LOG.info(f'Copying {self.automation_file} to {path}')
            shutil.copy(self.automation_file, path)
        os.remove(self.automation_file)

    def ipc(self):
        return constants.DAW_IPC

    def save_file(self, a_folder, a_file, a_text, a_force_new=False):
        f_result = AbstractProject.save_file(
            self, a_folder, a_file, a_text, a_force_new)
        if f_result:
            f_existed, f_old = f_result
            f_history_file = history.history_file(
                a_folder, a_file, a_text, f_old, f_existed)
            self.history_files.append(f_history_file)

    def set_undo_context(self, a_context):
        self.undo_context = a_context

    def clear_undo_context(self, a_context):
        self.history_commits[a_context] = []

    def commit(self, a_message, a_discard=False):
        """ Commit the project history """
        if self.undo_context not in self.history_commits:
            self.history_commits[self.undo_context] = []
        if self.history_undo_cursor > 0:
            self.history_commits[self.undo_context] = self.history_commits[
                self.undo_context][:self.history_undo_cursor]
            self.history_undo_cursor = 0
        if self.history_files and not a_discard:
            f_commit = history.history_commit(
                self.history_files, a_message)
            self.history_commits[self.undo_context].append(f_commit)
        self.history_files = []

    def clear_history(self):
        self.history_undo_cursor = 0
        self.history_files = []
        self.history_commits = {}

    def undo(self):
        if self.undo_context not in self.history_commits or \
        self.history_undo_cursor >= len(
        self.history_commits[self.undo_context]):
            return False
        self.history_undo_cursor += 1
        self.history_commits[self.undo_context][
            -1 * self.history_undo_cursor].undo(self.project_folder)
        return True

    def redo(self):
        if self.undo_context not in self.history_commits or \
        self.history_undo_cursor == 0:
            return False
        self.history_commits[self.undo_context][
            -1 * self.history_undo_cursor].redo(self.project_folder)
        self.history_undo_cursor -= 1
        return True

    def get_files_dict(self, a_folder, a_ext=None):
        f_result = {}
        f_files = []
        if a_ext is not None :
            for f_file in os.listdir(a_folder):
                if f_file.endswith(a_ext):
                    f_files.append(f_file)
        else:
            f_files = os.listdir(a_folder)
        for f_file in f_files:
            f_result[f_file] = read_file_text(
                os.path.join(a_folder, f_file))
        return f_result

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file)
        )[0]
        self.automation_folder = os.path.join(
            self.project_folder,
            folder_automation,
        )
        self.items_folder = os.path.join(
            self.project_folder,
            folder_items,
        )
        self.host_folder = os.path.join(
            self.project_folder, folder_daw)
        self.track_pool_folder = os.path.join(
            self.project_folder, folder_tracks)
        self.song_folder = os.path.join(
            self.project_folder,
            FOLDER_SONGS,
        )
        #files
        self.pyitems_file = os.path.join(
            self.project_folder, file_pyitems)
        self.takes_file = os.path.join(
            self.project_folder, file_takes)
        self.pyscale_file = os.path.join(
            self.project_folder, "default.pyscale")
        self.pynotes_file = os.path.join(
            self.project_folder, file_notes)
        self.routing_graph_file = os.path.join(
            self.project_folder, file_routing_graph)
        self.midi_routing_file = os.path.join(
            self.project_folder, file_midi_routing)
        self.automation_file = os.path.join(
            self.project_folder, file_sequences_atm)
        self.playlist_file = os.path.join(
            self.project_folder,
            FILE_PLAYLIST,
        )
        self.audio_inputs_file = os.path.join(
            self.project_folder, file_pyinput)

        self.project_folders = [
            self.automation_folder,
            self.items_folder,
            self.project_folder,
            self.song_folder,
            self.track_pool_folder,
        ]
        # Do it here in case we add new folders later after a project
        # has already been created
        for project_dir in self.project_folders:
            if not os.path.isdir(project_dir):
                LOG.info(f'Creating directory: {project_dir}')
                os.makedirs(project_dir)

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        self.quirks()
        if not os.path.exists(a_project_file):
            LOG.info("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

        if a_notify_osc:
            constants.DAW_IPC.open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        j = marshal_json(Playlist.new())
        j = json.dumps(j, indent=2, sort_keys=True)
        self.save_file("", FILE_PLAYLIST, j)

        self.save_file(
            FOLDER_SONGS,
            "0",
            str(sequencer(name='default')),
        )
        self.create_file("", file_pyitems, terminating_char)
        f_tracks = tracks()
        for i in range(_shared.TRACK_COUNT_ALL):
            f_tracks.add_track(i, track(
                a_track_uid=i, a_track_pos=i,
                a_name="Main" if i == 0 else "track{}".format(i)))
            plugins = track_plugins()
            for i2 in range(constants.TOTAL_PLUGINS_PER_TRACK):
                plugins.plugins.append(
                    track_plugin(i2, 0, -1),
                )
            self.save_track_plugins(i, plugins)

        self.create_file("", file_pytracks, str(f_tracks))

        self.commit("Created project")
        if a_notify_osc:
            constants.DAW_IPC.open_song(self.project_folder)

    def active_audio_pool_uids(self):
        playlist = self.get_playlist()
        result = set()
        for uid in (x.seq_uid for x in playlist.pool):
            f_sequence = self.get_sequence(uid=uid)
            f_item_uids = set(x.item_uid for x in f_sequence.items)
            f_items = [self.get_item_by_uid(x) for x in f_item_uids]
            result.update(
                set(y.uid for x in f_items for y in x.items.values())
            )
        for uid in self.get_plugin_audio_pool_uids():
            result.add(uid)
        return result

    def get_notes(self):
        if os.path.isfile(self.pynotes_file):
            return read_file_text(self.pynotes_file)
        else:
            return ""

    def write_notes(self, a_text):
        write_file_text(self.pynotes_file, a_text)

    def set_midi_scale(self, a_key, a_scale):
        write_file_text(
            self.pyscale_file, "{}|{}".format(a_key, a_scale))

    def get_midi_scale(self):
        if os.path.exists(self.pyscale_file):
            f_list = read_file_text(self.pyscale_file).split("|")
            return (int(f_list[0]), int(f_list[1]))
        else:
            return None

    def get_routing_graph(self) -> RoutingGraph:
        if os.path.isfile(self.routing_graph_file):
            with open(self.routing_graph_file) as f_handle:
                return RoutingGraph.from_str(f_handle.read())
        else:
            return RoutingGraph()

    def save_routing_graph(self, a_graph, a_notify=True):
        self.save_file("", file_routing_graph, str(a_graph))
        if a_notify:
            constants.DAW_IPC.update_track_send()

    def check_output(self, a_track=None):
        """ Ensure that any track with items or plugins is routed to main
            if it does not have any routings
        """
        if a_track is not None and a_track <= 0:
            return
        graph = self.get_routing_graph()
        sequence = self.get_sequence()
        modified = False
        tracks = set(x.track_num for x in sequence.items)
        if 0 in tracks:
            tracks.remove(0)
        if a_track is not None:
            tracks.add(a_track)

        for i in tracks:
            if graph.set_default_output(i):
                modified = True

        if modified:
            self.save_routing_graph(graph)
            self.commit("Set default output")

    def get_midi_routing(self):
        if os.path.isfile(self.midi_routing_file):
            with open(self.midi_routing_file) as f_handle:
                return MIDIRoutes.from_str(f_handle.read())
        else:
            return MIDIRoutes()

    def save_midi_routing(self, a_routing, a_notify=True):
        self.save_file("", file_midi_routing, str(a_routing))
        if a_notify:
            self.commit("Update MIDI routing")

    def get_takes(self):
        if os.path.isfile(self.takes_file):
            with open(self.takes_file) as fh:
                return SgTakes.from_str(fh.read())
        else:
            return SgTakes()

    def save_takes(self, a_takes):
        self.save_file("", file_takes, str(a_takes))

    def get_items_dict(self):
        if self._items_dict_cache:
            return self._items_dict_cache
        try:
            f_file = open(self.pyitems_file, "r")
        except:
            return name_uid_dict()
        f_str = f_file.read()
        f_file.close()
        return name_uid_dict.from_str(f_str)

    def save_items_dict(self, a_uid_dict):
        self._items_dict_cache = a_uid_dict
        self.save_file("", file_pyitems, str(a_uid_dict))

    def create_sequence(self, name):
        """ Create a new sequence with the next available uid
            @raises: IndexError if no more uids left
        """
        uid = self.get_next_sequence_uid()
        sequence = self.get_sequence(uid, name)
        self.save_file(
            FOLDER_SONGS,
            uid,
            str(sequence),
        )
        self.save_atm_sequence(DawAtmRegion(), uid)
        constants.DAW_IPC.new_sequence(uid)
        return uid, sequence

    def get_next_sequence_uid(self):
        """ Get the next available sequence uid, or None if no uids are
            available
            @raises: IndexError if no more uids left
        """
        for i in range(constants.DAW_MAX_SONG_COUNT):
            path = os.path.join(
                self.song_folder,
                str(i),
            )
            if not os.path.exists(path):
                return i
        raise IndexError

    def sequence_uids_by_name(self):
        """ Return a dict of {'sequence name': (uid, sequence)}
        """
        result = {}
        for i in range(constants.DAW_MAX_SONG_COUNT):
            path = os.path.join(
                self.song_folder,
                str(i),
            )
            if os.path.exists(path):
                sequence = self.get_sequence(i)
                result[sequence.name] = (i, sequence)
        return result

    def get_sequence(
        self,
        uid=None,
        name='default',
    ):
        """ Get an existing sequence, or create a new empty sequence
        """
        if uid is None:
            uid = constants.DAW_CURRENT_SEQUENCE_UID
        assert (
            uid >= 0
            and
            uid < constants.DAW_MAX_SONG_COUNT
        ), uid
        if uid in self._sequence_cache:
            return self._sequence_cache[uid]
        sequencer_file = os.path.join(
            self.song_folder,
            str(uid),
        )
        if os.path.isfile(sequencer_file):
            with open(sequencer_file) as f_file:
                return sequencer.from_str(f_file.read())
        else:
            return sequencer(name)

    def import_midi_file(
        self,
        a_midi_file,
        a_beat_offset,
        a_track_offset,
    ):
        """
            @a_midi_file:  An instance of DawMidiFile
        """
        f_sequencer = self.get_sequence()
        f_active_tracks = [
            x + a_track_offset
            for x in a_midi_file.result_dict
            if x + a_track_offset < _shared.TRACK_COUNT_ALL
        ]
        f_end_beat = math.ceil(
            max(
                x.get_length()
                for x in a_midi_file.result_dict.values()
            )
        )
        f_sequencer.clear_range(f_active_tracks, a_beat_offset, f_end_beat)
        for k,v in a_midi_file.result_dict.items():
            f_track = a_track_offset + int(k)
            if f_track >= _shared.TRACK_COUNT_ALL:
                break
            f_item_ref = sequencer_item(
                f_track, a_beat_offset, v.get_length(), v.uid)
            f_sequencer.add_item_ref_by_uid(f_item_ref)
        self.save_sequence(f_sequencer)

    def get_playlist(self):
        if os.path.isfile(self.playlist_file):
            with open(self.playlist_file) as f:
                j = json.load(f)
                return unmarshal_json(j, Playlist)
        else:
            return Playlist.new()

    def save_playlist(self, playlist):
        j = marshal_json(playlist)
        j = json.dumps(j, indent=2, sort_keys=True)
        self.save_file("", FILE_PLAYLIST, j)
        self.commit("Update playlist")

    def get_atm_sequence(self, song_uid=None):
        if song_uid is None:
            song_uid = constants.DAW_CURRENT_SEQUENCE_UID
        path = os.path.join(self.automation_folder, str(song_uid))
        if os.path.isfile(path):
            with open(path) as f:
                return DawAtmRegion.from_str(f.read())
        else:
            return DawAtmRegion()

    def save_atm_sequence(self, a_sequence, song_uid):
        if song_uid is None:
            song_uid = constants.DAW_CURRENT_SEQUENCE_UID
        self.save_file(folder_automation, str(song_uid), str(a_sequence))
        self.commit("Update automation")
        constants.DAW_IPC.save_atm_sequence()

    def all_items(self):
        """ Generator function to open, modify and save all items
        """
        for name in self.get_item_list():
            item = self.get_item_by_name(name)
            yield item
            self.save_item_by_uid(item.uid, item)

    def replace_all_audio_file(self, old_uid, new_uid):
        """ Replace all instances of an audio file with another in all
            sequencer items in the project

            @old_uid: The UID of the old audio file in the audio pool
            @new_uid: The UID of the new audio file in the audio pool
        """
        for item in self.all_items():
            item.replace_all_audio_file(old_uid, new_uid)

    def clone_sef(self, audio_item):
        """ Clone start/end/fade for all instances of a file in the project
        """
        for item in self.all_items():
            item.clone_sef(audio_item)

    def rename_items(self, a_item_names, a_new_item_name):
        """ @a_item_names:  A list of str
        """
        assert isinstance(a_item_names, list), a_item_names
        f_items_dict = self.get_items_dict()
        if len(a_item_names) > 1 or f_items_dict.name_exists(a_new_item_name):
            f_suffix = 1
            f_new_item_name = f"{a_new_item_name}-"
            for f_item_name in a_item_names:
                while f_items_dict.name_exists(
                    f"{f_new_item_name}{f_suffix}",
                ):
                    f_suffix += 1
                f_items_dict.rename_item(
                    f_item_name,
                    f_new_item_name + str(f_suffix),
                )
        else:
            f_items_dict.rename_item(a_item_names[0], a_new_item_name)
        self.save_items_dict(f_items_dict)

    def get_item_string(self, a_item_uid):
        try:
            f_file = open(
                os.path.join(
                    *(str(x) for x in (self.items_folder, a_item_uid))
                ),
            )
        except:
            return ""
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_item_by_uid(self, a_item_uid):
        a_item_uid = int(a_item_uid)
        if a_item_uid in self._item_cache:
            _item = self._item_cache[a_item_uid]
        else:
            _item = item.from_str(
                self.get_item_string(a_item_uid),
                a_item_uid,
            )
        assert _item.uid == a_item_uid, (
            "UIDs do not match",
            _item.uid,
            a_item_uid,
        )
        return _item

    def get_item_by_name(self, a_item_name):
        items_dict = self.get_items_dict()
        uid = items_dict.get_uid_by_name(a_item_name)
        return self.get_item_by_uid(uid)

    def save_audio_inputs(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", file_pyinput, str(a_tracks))

    def get_audio_inputs(self):
        if os.path.isfile(self.audio_inputs_file):
            with open(self.audio_inputs_file) as f_file:
                f_str = f_file.read()
            return AudioInputTracks.from_str(f_str)
        else:
            return AudioInputTracks()

    def reorder_tracks(self, a_dict):
        constants.IPC.pause_engine()
        f_tracks = self.get_tracks()
        f_tracks.reorder(a_dict)

        f_audio_inputs = self.get_audio_inputs()
        f_audio_inputs.reorder(a_dict)

        f_midi_routings = self.get_midi_routing()
        f_midi_routings.reorder(a_dict)

        f_track_plugins = {
            k:self.get_track_plugins(k)
            for k in f_tracks.tracks
        }
        # Delete the existing track files
        for k in f_track_plugins:
            f_path = os.path.join(
                *(str(x) for x in (self.track_pool_folder, k))
            )
            if os.path.exists(f_path):
                os.remove(f_path)
        for k, v in f_track_plugins.items():
            if v:
                self.save_track_plugins(a_dict[k], v)

        f_graph = self.get_routing_graph()
        f_graph.reorder(a_dict)

        sequences = self.sequence_uids_by_name()
        for name, tup in sequences.items():
            uid = tup[0]
            sequence = self.get_sequence(uid)
            sequence.reorder(a_dict)
            self.save_sequence(sequence, a_notify=False, uid=uid)

        self.save_tracks(f_tracks)
        self.save_audio_inputs(f_audio_inputs)
        self.save_routing_graph(f_graph, a_notify=False)
        self.save_midi_routing(f_midi_routings, a_notify=False)

        constants.DAW_IPC.open_song(self.project_folder, False)
        constants.IPC.resume_engine()
        self.commit("Re-order tracks", a_discard=True)
        self.clear_history()

    def get_tracks_string(self):
        try:
            f_file = open(
                os.path.join(self.project_folder, file_pytracks))
        except:
            return terminating_char
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_tracks(self):
        return tracks.from_str(self.get_tracks_string())

    def get_track_plugin_uids(self, a_track_num):
        f_plugins = self.get_track_plugins(a_track_num)
        if f_plugins:
            return set(x.plugin_uid for x in f_plugins.plugins)
        else:
            return f_plugins

    def create_empty_item(self, a_item_name="item"):
        f_items_dict = self.get_items_dict()
        f_item_name = self.get_next_default_item_name(
            a_item_name,
            a_items_dict=f_items_dict,
        )
        f_uid = f_items_dict.add_new_item(f_item_name)
        self.save_file(folder_items, str(f_uid), item(f_uid))
        constants.DAW_IPC.save_item(f_uid)
        self.save_items_dict(f_items_dict)
        return f_uid

    def copy_item(self, a_old_item: str, a_new_item: str):
        f_items_dict = self.get_items_dict()
        f_uid = f_items_dict.add_new_item(a_new_item)
        f_old_uid = f_items_dict.get_uid_by_name(a_old_item)
        f_new_item = copy.deepcopy(self.get_item_by_uid(f_old_uid))
        f_new_item.uid = f_uid
        self.save_file(
            folder_items,
            str(f_uid),
            str(f_new_item),
        )
        constants.DAW_IPC.save_item(f_uid)
        self.save_items_dict(f_items_dict)
        return f_uid

    def save_item_by_uid(self, a_uid, a_item, a_new_item=False):
        a_uid = int(a_uid)
        a_item = copy.deepcopy(a_item)
        a_item.uid = a_uid
        self._item_cache[a_uid] = a_item
        if not self.suppress_updates:
            self.save_file(
                folder_items,
                str(a_uid),
                str(a_item),
                a_new_item,
            )
            constants.DAW_IPC.save_item(a_uid)

    def save_sequence(
        self,
        a_sequence,
        a_notify=True,
        uid=None,
    ):
        if self.suppress_updates:
            return
        a_sequence.fix_overlaps()
        if uid is None:
            uid = str(constants.DAW_CURRENT_SEQUENCE_UID)
        self._sequence_cache[uid] = a_sequence
        self.save_file(
            FOLDER_SONGS,
            uid,
            str(a_sequence),
        )
        if a_notify:
            constants.DAW_IPC.save_sequence(uid)
        self.check_output()

    def save_tracks(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", file_pytracks, str(a_tracks))
            #Is there a need for a configure message here?

    def save_track_plugins(self, a_uid, a_track):
        """ @a_uid:   int, the track number
            @a_track: track_plugins
        """
        int(a_uid)  # Test that it can be cast to an int
        f_folder = folder_tracks
        if not self.suppress_updates:
            self.save_file(f_folder, str(a_uid), str(a_track))

    def item_exists(self, a_item_name, a_name_dict=None):
        if a_name_dict is None:
            f_name_dict = self.get_items_dict()
        else:
            f_name_dict = a_name_dict
        if str(a_item_name) in f_name_dict.uid_lookup:
            return True
        else:
            return False

    def get_next_default_item_name(
        self,
        a_item_name="item",
        a_items_dict=None,
    ):
        f_item_name = str(a_item_name)
        f_end_number = re.search(r"[0-9]+$", f_item_name)
        if f_item_name == "item":
            f_start = self.last_item_number
        else:
            if f_end_number:
                f_num_str = f_end_number.group()
                f_start = int(f_num_str)
                f_item_name = f_item_name[:-len(f_num_str)]
                f_item_name = f_item_name.strip('-')
            else:
                f_start = 1
        if a_items_dict:
            f_items_dict = a_items_dict
        else:
            f_items_dict = self.get_items_dict()
        for i in range(f_start, 10000):
            f_result = "{}-{}".format(f_item_name, i).strip('-')
            if not f_result in f_items_dict.uid_lookup:
                if f_item_name == "item":
                    self.last_item_number = i
                return f_result

    def get_item_list(self):
        f_result = self.get_items_dict()
        return sorted(f_result.uid_lookup.keys())

    def check_audio_files(self):
        """ Verify that all audio files exist  """
        f_result = []
        f_sequences = self.get_sequences_dict()
        f_audio_pool = constants.PROJECT.get_audio_pool()
        by_uid = f_audio_pool.by_uid()
        f_to_delete = []
        f_commit = False
        for k, v in by_uid.items():
            if not os.path.isfile(v):
                f_to_delete.append(k)
        if f_to_delete:
            f_commit = True
            f_audio_pool.remove_by_uid(f_to_delete)
            self.save_audio_pool(f_audio_pool)
            LOG.error("Removed missing audio item(s) from audio_pool")
        f_audio_pool = constants.PROJECT.get_audio_pool()
        by_uid = f_audio_pool.by_uid()
        for f_uid in list(f_sequences.uid_lookup.values()):
            f_to_delete = []
            f_sequence = self.get_audio_sequence(f_uid)
            for k, v in list(f_sequence.items.items()):
                if v.uid not in by_uid:
                    f_to_delete.append(k)
            if len(f_to_delete) > 0:
                f_commit = True
                for f_key in f_to_delete:
                    f_sequence.remove_item(f_key)
                f_result += f_to_delete
                self.save_audio_sequence(f_uid, f_sequence)
                LOG.error("Removed missing audio item(s) "
                    "from sequence {}".format(f_uid))
        if f_commit:
            self.commit("check_audio_file")
        return f_result

