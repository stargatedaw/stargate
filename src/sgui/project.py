import os

from sgui import util
from sglib.constants import (
    DEFAULT_PROJECT_DIR,
    MAJOR_VERSION,
    IS_PORTABLE_INSTALL,
)
from sglib.lib import portable
from sglib.lib.translate import _
from sglib.lib.util import set_file_setting, PROJECT_FILE_TYPE
from sglib.log import LOG
from sgui.sgqt import *
import shutil

__all__ = [
    'new_project',
    'open_project',
    'set_project',
    'get_history',
]

def new_project_dialog(parent, last_dir):
    f_file, _filter = QFileDialog.getSaveFileName(
        parent,
        _('Create a new project'),
        last_dir,
        options=(
            QFileDialog.Option.ShowDirsOnly
            |
            QFileDialog.Option.DontUseNativeDialog
        ),
    )
    return f_file, _filter

def new_project(a_parent=None):
    try:
        f_last_dir = DEFAULT_PROJECT_DIR
        while True:
            f_file, _filter = new_project_dialog(a_parent, f_last_dir)
            if f_file and str(f_file):
                f_file = str(f_file)
                f_last_dir = f_file
                if os.path.exists(f_file):
                    QMessageBox.warning(
                        a_parent,
                        "Error",
                        f"{f_file} already exists"
                    )
                    continue
                os.makedirs(f_file)
                f_file = os.path.join(
                    f_file,
                    f"{MAJOR_VERSION}.project",
                )
                set_project(f_file)
                return True
            else:
                return False
    except Exception as ex:
        LOG.exception(ex)
        QMessageBox.warning(a_parent, "Error", str(ex))

def clone_project(parent):
    clone, _ = open_project_dialog(parent)
    if not clone:
        return False
    new, _ = new_project_dialog(parent, DEFAULT_PROJECT_DIR)
    if not new:
        return False
    clone_dir = os.path.dirname(clone)
    shutil.copytree(clone_dir, new)
    set_project(
        os.path.join(new, f"{MAJOR_VERSION}.project"),
    )
    return True

def open_project_dialog(parent):
    f_file, f_filter = QFileDialog.getOpenFileName(
        parent=parent,
        caption='Open Project',
        directory=DEFAULT_PROJECT_DIR,
        filter=PROJECT_FILE_TYPE,
        options=QFileDialog.Option.DontUseNativeDialog,
    )
    return f_file, f_filter

def open_project(a_parent=None):
    try:
        f_file, f_filter = open_project_dialog(a_parent)
        if f_file is None:
            return False
        f_file_str = str(f_file)
        if not f_file_str:
            return False
        if not util.check_for_rw_perms(f_file):
            return False
        #global_open_project(f_file_str)
        set_project(f_file_str)
        return True
    except Exception as ex:
        LOG.exception(ex)
        QMessageBox.warning(a_parent, "Error", str(ex))

def set_project(project):
    set_file_setting("last-project", str(project))
    if IS_PORTABLE_INSTALL:
        project = portable.escape_path(project)
    history = get_history()
    if project in history:
        history.remove(project)
    history.insert(0, project)
    util.set_file_setting(
        "project-history",
        "\n".join(history[:20]),
    )

def get_history():
    history = util.get_file_setting("project-history", str, "")
    history = [
        x for x in history.split("\n")
        if (
            x.strip()
            and
            os.path.exists(x)
        )
    ]
    if IS_PORTABLE_INSTALL:
        history = [
            portable.unescape_path(x)
            for x in history
        ]
    return history

