import os

from sgui.sgqt import *
from sglib.lib.translate import _
from sglib.log import LOG
from sgui import shared as glbl_shared

def show_generic_exception(a_ex):
    LOG.exception(ex)
    QMessageBox.warning(
        glbl_shared.MAIN_WINDOW.widget,
        _("Warning"),
        _("The following error happened:\n{}").format(a_ex),
    )

def check_for_rw_perms(a_file):
    if not os.access(
        os.path.dirname(str(a_file)),
        os.W_OK,
    ):
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW.widget,
            "Error",
            f"You do not have read+write permissions to {a_file}",
        )
        return False
    else:
        return True

def check_for_empty_directory(a_dir):
    """ Return true if directory is empty, show error message and
        return False if not
    """
    if os.listdir(a_dir):
        QMessageBox.warning(
            glbl_shared.MAIN_WINDOW.widget,
            "Error",
            "You must save the project file to an empty directory, use "
            "the 'Create Folder' button to create a new, empty directory.",
        )
        return False
    else:
        return True

