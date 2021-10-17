"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import argparse
import datetime
import json
import os
import shutil
import sys
import tarfile

f_prefix_dir = os.path.dirname(__file__)
f_path = os.path.join(
    f_prefix_dir,
    "..",
    "lib",
    "stargate",
    "stargate",
)
f_path = os.path.abspath(f_path)
print(f_path)
sys.path.insert(0, f_path)

f_parent_dir = os.path.dirname(os.path.abspath(__file__))
f_parent_dir = os.path.abspath(os.path.join(f_parent_dir, ".."))
sys.path.insert(0, f_parent_dir)

from sglib.constants import DEFAULT_PROJECT_DIR
from sglib.lib.translate import _
from sgui.sgqt import *
from sglib.models import theme
from sglib.lib import util


class ProjectRecoveryWidget(QListWidget):
    def __init__(
        self,
        a_backup_dir,
        a_project_dir,
    ):
        QListWidget.__init__(self)
        self.backup_dir = a_backup_dir
        self.project_dir = a_project_dir
        self.data = os.listdir(a_backup_dir)
        self.draw()

    def draw(self):
        self.clear()
        for data in self.data:
            self.addItem(data)
        self.sortItems()

    def set_selected_as_project(self):
        f_items = self.selectedItems()
        if not (
            f_items
            and
            len(f_items) == 1
        ):
            return
        f_project_dir = os.path.join(self.project_dir, "projects")
        f_tmp_dir = "{}-tmp-{}".format(
            f_project_dir,
            datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        f_item = f_items[0]
        fname = str(f_item.text())
        f_tar_path = os.path.join(
            self.backup_dir,
            fname,
        )
        shutil.move(f_project_dir, f_tmp_dir)
        with tarfile.open(f_tar_path, "r:bz2") as f_tar:
            f_tar.extractall(self.project_dir)
        shutil.rmtree(f_tmp_dir)
        QMessageBox.warning(
            self,
            _("Complete"),
            _(f"Reverted project to {fname}"),
        )

def project_recover_dialog(a_file):
    f_window = QDialog()
    f_window.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
    f_window.setWindowTitle("Project History")
    f_project_dir = os.path.dirname(str(a_file))
    f_backup_dir = os.path.join(f_project_dir, "backups")
    if not os.listdir(f_backup_dir):
        QMessageBox.warning(
            f_window,
            _("Error"),
            _(
                "No backups exist for this project, recovery is not "
                "possible."
            ),
        )
        return
    f_layout = QVBoxLayout(f_window)
    f_widget = ProjectRecoveryWidget(
        f_backup_dir,
        f_project_dir,
    )
    f_layout.addWidget(f_widget)
    f_hlayout = QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_set_project_button = QPushButton(
        _("Revert Project to Selected"))
    f_set_project_button.pressed.connect(
        f_widget.set_selected_as_project)
    f_hlayout.addWidget(f_set_project_button)
    f_hlayout.addItem(
        QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
    )
    print("showing")
    f_window.exec()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Stargate project recover script",
    )
    parser.add_argument(
        '-p',
        '--project-file',
        dest='project_file',
        help="The project file to open",
    )
    return parser.parse_args()

