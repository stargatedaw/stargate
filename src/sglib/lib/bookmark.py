from .util import (
    read_file_text,
    write_file_text,
)
from sglib.constants import CONFIG_DIR
from sglib.log import LOG
import os

BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "file_browser_bookmarks.txt")

def get_file_bookmarks():
    try:
        f_result = {}
        if os.path.isfile(BOOKMARKS_FILE):
            f_text = read_file_text(BOOKMARKS_FILE)
            f_arr = f_text.split("\n")
            for f_line in f_arr:
                f_line_arr = f_line.split("|||", 2)
                if len(f_line_arr) != 3:
                    break
                if os.path.isdir(f_line_arr[2]):
                    if not f_line_arr[1] in f_result:
                        f_result[f_line_arr[1]] = {}
                    f_result[f_line_arr[1]][f_line_arr[0]] = f_line_arr[2]
                else:
                    LOG.warning("Warning:  Not loading bookmark '{}' "
                        "because the directory '{}' does not "
                        "exist.".format(f_line_arr[0], f_line_arr[2]))
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
            LOG.warning("{} was not in the bookmarks file, it may "
                "have been deleted in a different "
                "file browser widget".format(f_key))

