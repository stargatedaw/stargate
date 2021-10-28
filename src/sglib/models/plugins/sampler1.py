from sglib import constants
from sglib.models.plugin_file import plugin_file
import os

def get_audio_pool_uids(a_plugin_uid):
    f_file_path = os.path.join(
        *(
            str(x) for x in (
                constants.PROJECT.plugin_pool_folder,
                a_plugin_uid,
            )
        )
    )
    if os.path.isfile(f_file_path):
        f_file = plugin_file(f_file_path)
        if 'load' in f_file.configure_dict:
            return set(
                int(x)
                for x in f_file.configure_dict['load'].split("|")
                if x
            )
        else:
            return set()

