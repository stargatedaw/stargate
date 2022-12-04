"""
    Library functions related to special features of the Windows portable
    flash drive install.
"""

from sglib.constants import IS_MACOS, IS_WINDOWS, USER_HOME
from sglib.log import LOG
import os
import pathlib

def escape_path(path):
    if IS_WINDOWS:
        folder_drive = pathlib.Path(path).drive.upper()
        user_drive = pathlib.Path(USER_HOME).drive.upper()
        assert folder_drive and user_drive, (path, USER_HOME)
        if user_drive == folder_drive:
            relpath = os.path.relpath(path, USER_HOME)
            path = os.path.join("{{ USER_HOME }}", relpath)
        else:
            LOG.warning(
                'Path set to a different drive than portable install at '
                f'"{USER_HOME}".  "{path}" will not be accessible on '
                'another computer'
            )
    if IS_MACOS:
        path_split = os.path.split(path)
        home_split = os.path.split(USER_HOME)
        if (
            path_split[0] == 'Volumes' 
            and 
            path_split[1] == home_split[1]
        ):
            relpath = os.path.relpath(path, USER_HOME)
            path = os.path.join("{{ USER_HOME }}", relpath)
        else:
            LOG.warning(
                'Path set to a different storage device than portable '
                f'install at "{USER_HOME}".  "{path}" will not be '
                'accessible on another computer'
            )
    return path

def unescape_path(path):
    path = path.replace("{{ USER_HOME }}", USER_HOME)
    path = os.path.abspath(path)
    return path

