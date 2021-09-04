from .util import (
    read_file_text,
    write_file_text,
)
from sglib.constants import CONFIG_DIR, IS_PORTABLE_INSTALL, USER_HOME
from sglib.log import LOG
import os
import pathlib

BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "file_browser_bookmarks.txt")

def get_file_bookmarks():
    try:
        f_result = {}
        if os.path.isfile(BOOKMARKS_FILE):
            f_text = read_file_text(BOOKMARKS_FILE)
            f_arr = f_text.split("\n")
            for f_line in f_arr:
                if not f_line.strip():
                    continue
                name, category, path = f_line.split("|||", 2)
                if IS_PORTABLE_INSTALL:
                    path = path.replace("{{ USER_HOME }}", USER_HOME)
                    path = os.path.abspath(path)
                if os.path.isdir(path):
                    if category not in f_result:
                        f_result[category] = {}
                    f_result[category][name] = path
                else:
                    LOG.warning(
                        f"Not loading bookmark '{name}' "
                        f"because the directory '{path}' does not "
                        "exist."
                    )
        return f_result
    except Exception as ex:
        LOG.error("Error getting bookmarks:\n".format(ex))
        return {}

def write_file_bookmarks(a_dict):
    f_result = []
    for k in sorted(a_dict.keys()):
        v = a_dict[k]
        for k2 in sorted(v.keys()):
            v2 = v[k2]
            f_result.append("{}|||{}|||{}".format(k2, k, v2))
    write_file_text(BOOKMARKS_FILE, "\n".join(f_result))

def add_file_bookmark(a_name, a_folder, a_category):
    f_dict = get_file_bookmarks()
    f_category = str(a_category)
    if not f_category in f_dict:
        f_dict[f_category] = {}
    if IS_PORTABLE_INSTALL:
        folder_drive = pathlib.Path(a_folder).drive.upper()
        user_drive = pathlib.Path(USER_HOME).drive.upper()
        assert folder_drive and user_drive, (a_folder, USER_HOME)
        if user_drive == folder_drive:
            relpath = os.path.relpath(a_folder, USER_HOME)
            a_folder = os.path.join("{{ USER_HOME }}", relpath)
        else:
            LOG.warning(
                'Bookmark set to a different drive than portable install at '
                f'"{USER_HOME}".  "{a_folder}" will not be accessible on '
                'another computer'
            )
    f_dict[f_category][str(a_name)] = str(a_folder)
    write_file_bookmarks(f_dict)

def delete_file_bookmark(a_category, a_name):
    f_dict = get_file_bookmarks()
    f_key = str(a_category)
    f_name = str(a_name)
    if f_key in f_dict:
        if f_name in f_dict[f_key]:
            f_dict[f_key].pop(f_name)
            write_file_bookmarks(f_dict)
        else:
            LOG.warning(
                f"{f_key} was not in the bookmarks file, it may "
                "have been deleted in a different file browser widget"
            )

