#!/usr/bin/env python3

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

import os, time, difflib


class history_file:
    def __init__(self, a_folder, a_file_name, a_text_new,
                 a_text_old, a_existed):
        self.folder = str(a_folder)
        self.file_name = str(a_file_name)
        self.new_text = str(a_text_new)
        self.old_text = str(a_text_old)
        self.existed = int(a_existed)

    def __str__(self):
        """ Generate a human-readable summary of the changes """
        f_file_name = os.path.join(self.folder, self.file_name)
        f_result = "\n\n{}, existed: {}\n".format(f_file_name, self.existed)
        for f_line in difflib.unified_diff(
        self.old_text.split("\n"), self.new_text.split("\n"),
        f_file_name, f_file_name):
            f_result += f_line + "\n"
        return f_result

class history_commit:
    def __init__(self, a_files, a_message):
        self.files = a_files
        self.message = a_message
        self.timestamp = int(time.time())

    def undo(self, a_project_folder):
        for f_file in self.files:
            f_full_path = os.path.join(
                a_project_folder, f_file.folder, f_file.file_name)
            if f_file.existed == 0:
                os.remove(f_full_path)
            else:
                self._write_file(f_full_path, f_file.old_text)

    def redo(self, a_project_folder):
        for f_file in self.files:
            f_full_path = os.path.join(
                a_project_folder, f_file.folder, f_file.file_name)
            self._write_file(f_full_path, f_file.new_text)

    def _write_file(self, a_file, a_text):
        f_file = open(a_file, "w", newline="\n")
        f_file.write(a_text)
        f_file.close()

