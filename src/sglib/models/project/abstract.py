"""
Utility functions that are global to the entire application
"""

from sglib.lib import util
from sglib.lib.engine import close_engine, reopen_engine
from sglib.models.track_plugin import track_plugins
from sglib.models.daw.track_colors import TrackColors
from sglib.lib.translate import _
from sglib.log import LOG
import datetime
import os
import traceback


class AbstractProject:
    """ Abstract class containing the minimum contract
        to run SG Plugins for host project file saving
    """
    def __init__(self):
        self.plugin_pool_folder = None

    def ipc(self):
        """ Return the IPC for this host """
        raise NotImplementedError

    def commit(self, *args, **kwargs):
        """ Used for undo history """
        pass

    def create_file(self, a_folder, a_file, a_text):
        """  Call save_file only if the file doesn't exist... """
        if not os.path.isfile(os.path.join(
        self.project_folder, a_folder, a_file)):
            self.save_file(a_folder, a_file, a_text)
        else:
            assert(False)

    def save_file(self, a_folder, a_file, a_text, a_force_new=False):
        """ Writes a file to disk and updates the project
            history to reflect the changes
        """
        f_full_path = os.path.join(
            *(str(x) for x in (self.project_folder, a_folder, a_file)))
        if not a_force_new and os.path.isfile(f_full_path):
            f_old = util.read_file_text(f_full_path)
            if f_old == a_text:
                return None
            f_existed = 1
        else:
            f_old = ""
            f_existed = 0
        util.write_file_text(f_full_path, a_text)
        return f_existed, f_old

    def get_track_plugins(self, a_track_num):
        f_folder = self.track_pool_folder
        f_path = os.path.join(*(str(x) for x in (f_folder, a_track_num)))
        if os.path.isfile(f_path):
            f_str = util.read_file_text(f_path)
            return track_plugins.from_str(f_str)
        else:
            return None

    def get_track_colors(self):
        path = os.path.join(self.host_folder, "track_colors.txt")
        if os.path.isfile(path):
            content = util.read_file_text(path)
            return TrackColors.from_str(content)
        else:
            return TrackColors()

    def save_track_colors(self, a_colors):
        path = os.path.join(self.host_folder, "track_colors.txt")
        util.write_file_text(path, a_colors)

    def get_plugin_audio_pool_uids(self):
        result = set()
        for plugins in (
            self.get_track_plugins(x)
            for x in range(self.TRACK_COUNT)
        ):
            if not plugins:
                continue
            for uid in plugins.get_audio_pool_uids():
                result.add(uid)
        return result

