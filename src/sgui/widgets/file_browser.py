from sglib.lib import (
    bookmark,
    util,
)
from sglib.constants import USER_HOME
from sgui import shared as glbl_shared
from sglib.lib.translate import _
from sgui.sgqt import *
import os
import shutil

BM_FILE_DIALOG_STRING = 'Stargate Bookmarks (*.pybm4)'

FILE_BROWSER_WIDGETS = []

def open_bookmarks():
    for widget in FILE_BROWSER_WIDGETS:
        widget.open_bookmarks()

class AbstractFileBrowserWidget:
    def __init__(self, a_filter_func=util.is_audio_file):
        self.scroll_dict = {}
        self.filter_func = a_filter_func
        self.hsplitter = QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.vsplitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.folders_tab_widget = QTabWidget()
        self.hsplitter.addWidget(self.folders_tab_widget)
        self.folders_widget = QWidget()
        self.vsplitter.addWidget(self.folders_widget)
        self.folders_widget_layout = QVBoxLayout()
        self.folders_widget.setLayout(self.folders_widget_layout)
        self.folders_tab_widget.setMaximumWidth(660)
        self.folders_tab_widget.addTab(self.vsplitter, _("Files"))
        self.folder_path_lineedit = QLineEdit()
        self.folder_path_lineedit.setToolTip('The current directory')
        self.folder_path_lineedit.setReadOnly(True)
        self.folders_widget_layout.addWidget(self.folder_path_lineedit)

        self.folder_filter_hlayout = QHBoxLayout()
        self.folder_filter_hlayout.addWidget(QLabel(_("Filter:")))
        self.folder_filter_lineedit = QLineEdit()
        self.folder_filter_lineedit.setToolTip(
            'Search for folders in this directory containing specific text '
            'in their file name.  Searches are not case-sensitive.'
        )
        self.folder_filter_lineedit.textChanged.connect(self.on_filter_folders)
        self.folder_filter_hlayout.addWidget(self.folder_filter_lineedit)
        self.folder_filter_clear_button = QPushButton(_("Clear"))
        self.folder_filter_clear_button.setToolTip(
            'Clear the filter, show all folders'
        )
        self.folder_filter_clear_button.pressed.connect(
            self.on_folder_filter_clear)
        self.folder_filter_hlayout.addWidget(self.folder_filter_clear_button)
        self.folders_widget_layout.addLayout(self.folder_filter_hlayout)

        self.list_folder = QListWidget()
        self.list_folder.setToolTip('The folders in the current directory')
        self.list_folder.itemClicked.connect(self.folder_item_clicked)
        self.folders_widget_layout.addWidget(self.list_folder)
        self.folder_buttons_hlayout = QHBoxLayout()
        self.folders_widget_layout.addLayout(self.folder_buttons_hlayout)
        self.up_button = QPushButton(_("Up"))
        self.up_button.setToolTip(
            "Go up one folder to this folder's parent folder"
        )
        self.up_button.pressed.connect(self.on_up_button)
        self.up_button.contextMenuEvent = self.up_contextMenuEvent
        self.folder_buttons_hlayout.addWidget(self.up_button)
        self.back_button = QPushButton(_("Back"))
        self.back_button.setToolTip("Go back to the previous folder")
        self.folder_buttons_hlayout.addWidget(self.back_button)
        self.back_button.contextMenuEvent = self.back_contextMenuEvent
        self.back_button.pressed.connect(self.on_back)

        self.menu_button = QPushButton(_("Menu"))
        self.menu_button_menu = QMenu(self.folders_tab_widget)
        self.menu_button.setMenu(self.menu_button_menu)
        self.folder_buttons_hlayout.addWidget(self.menu_button)

        self.copy_action = self.menu_button_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.copy_button_pressed)

        self.paste_action = self.menu_button_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.paste_button_pressed)

        self.menu_button_menu.addSeparator()

        self.bookmark_action = self.menu_button_menu.addAction(_("Bookmark"))
        self.bookmark_action.triggered.connect(self.bookmark_button_pressed)

        self.bookmark_subfolders_action = self.menu_button_menu.addAction(
            _("Bookmark Subfolders..."))
        self.bookmark_subfolders_action.triggered.connect(
            self.bookmark_subfolders)

        self.bookmarks_tab = QWidget()
        self.bookmarks_tab_vlayout = QVBoxLayout()
        self.bookmarks_tab.setLayout(self.bookmarks_tab_vlayout)
        self.list_bookmarks = QTreeWidget()
        self.list_bookmarks.setToolTip(
            'Bookmark folders from the file browser menu to keep here for '
            'easy access.  Some project folders are automatically kept as '
            'bookmarks'
        )
        self.list_bookmarks.setHeaderHidden(True)
        self.list_bookmarks.itemClicked.connect(self.bookmark_clicked)
        self.list_bookmarks.contextMenuEvent = self.bookmark_context_menu_event
        self.bookmarks_tab_vlayout.addWidget(self.list_bookmarks)
        self.bookmark_button_hlayout = QHBoxLayout()
        self.bookmarks_reload_button = QPushButton(_("Reload"))
        self.bookmarks_reload_button.setToolTip(
            'Reload bookmarks.  Use this when you have added bookmarks '
            'in another file browser'
        )
        self.bookmarks_tab_vlayout.addLayout(self.bookmark_button_hlayout)
        self.bookmark_button_hlayout.addWidget(self.bookmarks_reload_button)
        self.bookmarks_reload_button.pressed.connect(self.open_bookmarks)
        self.bookmarks_menu_button = QPushButton(_("Menu"))
        self.bookmark_button_hlayout.addWidget(self.bookmarks_menu_button)
        f_bookmark_menu = QMenu(self.bookmarks_tab)
        self.bookmarks_menu_button.setMenu(f_bookmark_menu)
        f_bookmark_open_action = f_bookmark_menu.addAction(_("Open..."))
        f_bookmark_open_action.triggered.connect(self.on_bookmark_open)
        f_bookmark_save_as_action = f_bookmark_menu.addAction(_("Save As..."))
        f_bookmark_save_as_action.triggered.connect(self.on_bookmark_save_as)
        self.folders_tab_widget.addTab(self.bookmarks_tab, _("Bookmarks"))

        self.file_vlayout = QVBoxLayout()
        self.file_widget = QWidget()
        self.file_widget.setLayout(self.file_vlayout)
        self.vsplitter.addWidget(self.file_widget)
        self.filter_hlayout = QHBoxLayout()
        self.filter_hlayout.addWidget(QLabel(_("Filter:")))
        self.filter_lineedit = QLineEdit()
        self.filter_lineedit.textChanged.connect(self.on_filter_files)
        self.filter_lineedit.setToolTip(
            'Search for files in this directory containing specific text '
            'in their file name.  Searches are not case-sensitive.'
        )
        self.filter_hlayout.addWidget(self.filter_lineedit)
        self.filter_clear_button = QPushButton(_("Clear"))
        self.filter_clear_button.setToolTip(
            'Clear the filter, show all files'
        )
        self.filter_clear_button.pressed.connect(self.on_filter_clear)
        self.filter_hlayout.addWidget(self.filter_clear_button)
        self.file_vlayout.addLayout(self.filter_hlayout)
        self.list_file = QListWidget()
        self.list_file.setToolTip('The files in the current directory')
        self.list_file.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection,
        )
        self.file_vlayout.addWidget(self.list_file)
        self.file_hlayout = QHBoxLayout()
        self.preview_button = QPushButton(_("Preview"))
        self.preview_button.setToolTip(
            'Preview an audio file.  Up to 30 seconds will be played'
        )
        self.file_hlayout.addWidget(self.preview_button)
        self.stop_preview_button = QPushButton(_("Stop"))
        self.stop_preview_button.setToolTip(
            'Stop playing audio after "Preview" has been pressed'
        )
        self.file_hlayout.addWidget(self.stop_preview_button)
        self.refresh_button = QPushButton(_("Refresh"))
        self.refresh_button.setToolTip(
            'Refresh the folder, show any new files, remove any files '
            'that were deleted'
        )
        self.file_hlayout.addWidget(self.refresh_button)
        self.refresh_button.pressed.connect(self.on_refresh)
        self.file_vlayout.addLayout(self.file_hlayout)

        self.vsplitter.setCollapsible(0, False)
        self.vsplitter.setCollapsible(1, False)

        self.last_open_dir = USER_HOME
        self.history = [USER_HOME]
        self.set_folder(".")
        self.multifx_clipboard = None
        self.audio_items_clipboard = []
        self.hsplitter.setSizes([300, 9999])
        FILE_BROWSER_WIDGETS.append(self)

    def set_multiselect(self, a_bool):
        mode = (
            QAbstractItemView.SelectionMode.ExtendedSelection
            if a_bool else
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_file.setSelectionMode(mode)

    def open_file_in_browser(self, a_path):
        f_path = str(a_path)
        f_dir = os.path.dirname(f_path)
        if os.path.isdir(f_dir):
            # Set the Files tab as the selected tab
            self.folders_tab_widget.setCurrentWidget(self.vsplitter)
            self.set_folder(f_dir, True)
            f_file = os.path.basename(f_path)
            self.select_file(f_file)
        else:
            QMessageBox.warning(
                self.vsplitter,
                _("Error"),
                _("The folder did not exist:\n\n{}").format(f_dir),
            )

    def on_bookmark_save_as(self):
        f_file, f_filter = QFileDialog.getSaveFileName(
            parent=self.bookmarks_tab,
            caption=_('Save bookmark file...'),
            directory=USER_HOME,
            filter=BM_FILE_DIALOG_STRING,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            if not f_file.endswith(".pybm4"):
                f_file += ".pybm4"
            shutil.copy(bookmark.BOOKMARKS_FILE, f_file)

    def on_bookmark_open(self):
        f_file, f_filter = QFileDialog.getOpenFileName(
            parent=self.bookmarks_tab,
            caption=_('Open bookmark file...'),
            directory=USER_HOME,
            filter=BM_FILE_DIALOG_STRING,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            shutil.copy(f_file, bookmark.BOOKMARKS_FILE)
            self.open_bookmarks()

    def on_refresh(self):
        self.set_folder(".")

    def on_back(self):
        if len(self.history) > 1:
            self.history.pop(-1)
            self.set_folder(self.history[-1], a_full_path=True)

    def open_path_from_action(self, a_action):
        self.set_folder(a_action.path, a_full_path=True)

    def back_contextMenuEvent(self, a_event):
        f_menu = QMenu(self.back_button)
        f_menu.triggered.connect(self.open_path_from_action)
        for f_path in reversed(self.history):
            f_action = f_menu.addAction(f_path)
            f_action.path = f_path
        f_menu.exec(QCursor.pos())

    def up_contextMenuEvent(self, a_event):
        if (
            util.IS_LINUX and self.last_open_dir != "/"
        ) or (
            util.IS_WINDOWS and self.last_open_dir
        ):
            f_menu = QMenu(self.up_button)
            f_menu.triggered.connect(self.open_path_from_action)
            f_arr = self.last_open_dir.split(os.path.sep)
            f_paths = []
            if util.IS_WINDOWS:
                for f_i in range(1, len(f_arr)):
                    f_paths.append("\\".join(f_arr[:f_i]))
                f_paths[0] += "\\"
            else:
                f_arr = f_arr[1:]
                for f_i in range(len(f_arr)):
                    f_paths.append("/{}".format("/".join(f_arr[:f_i])))
            for f_path in reversed(f_paths):
                f_action = f_menu.addAction(f_path)
                f_action.path = f_path
            if util.IS_WINDOWS:
                f_action = f_menu.addAction("")
                f_action.path = ""
            f_menu.exec(QCursor.pos())

    def on_filter_folders(self):
        self.on_filter(self.folder_filter_lineedit, self.list_folder)

    def on_filter_files(self):
        self.on_filter(self.filter_lineedit, self.list_file)

    def on_filter(self, a_line_edit, a_list_widget):
        f_text = str(a_line_edit.text()).lower().strip()
        for f_i in range(a_list_widget.count()):
            f_item = a_list_widget.item(f_i)
            f_item_text = str(f_item.text()).lower()
            if f_text in f_item_text:
                f_item.setHidden(False)
            else:
                f_item.setHidden(True)

    def on_folder_filter_clear(self):
        self.folder_filter_lineedit.setText("")

    def on_filter_clear(self):
        self.filter_lineedit.setText("")

    def open_bookmarks(self):
        self.list_bookmarks.clear()
        f_dict = bookmark.get_file_bookmarks()
        for k in sorted(f_dict.keys(), key=lambda s: s.lower()):
            f_parent = QTreeWidgetItem()
            f_parent.setText(0, k)
            self.list_bookmarks.addTopLevelItem(f_parent)
            for k2 in sorted(f_dict[k].keys(), key=lambda s: s.lower()):
                f_child = QTreeWidgetItem()
                f_child.setText(0, k2)
                f_parent.addChild(f_child)
            f_parent.setExpanded(True)

    def bookmark_subfolders(self):
        self.bookmark_button_pressed(a_recursive=True)

    def bookmark_button_pressed(self, a_recursive=False):
        def on_ok(a_val=None):
            f_text = str(f_category.currentText()).strip()
            if not f_text:
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _("Category cannot be empty"),
                )
                return
            elif f_text.lower() == "system":
                QMessageBox.warning(
                    f_window,
                    _("Error"),
                    _("Category cannot be 'system'"),
                )
                return
            if a_recursive:
                added_bm = False
                for f_i in range(dir_list_widget.count()):
                    item = dir_list_widget.item(f_i)
                    if not item.isHidden() and item.isSelected():
                        bookmark.add_file_bookmark(
                            item.dirname_abbrev[-30:],
                            item.dir_name,
                            f_text,
                        )
                        added_bm = True
                if not added_bm:
                    QMessageBox.warning(
                        f_window, _("Error"), _("No folders selected"))
                    return
            else:
                f_val = str(f_lineedit.text()).strip()
                if not f_val:
                    QMessageBox.warning(
                        f_window, _("Error"), _("Name cannot be empty"))
                    return
                bookmark.add_file_bookmark(
                    f_val, self.last_open_dir, f_text)
            self.open_bookmarks()
            if not a_recursive:
                f_window.close()

        def filter_changed(self, a_val=None):
            filter_text = str(filter_lineedit.text()).lower()
            for f_i in range(dir_list_widget.count()):
                item = dir_list_widget.item(f_i)
                item.setHidden(
                    filter_text not in item.dirname_abbrev.lower())

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QDialog(self.list_bookmarks)
        f_window.setMinimumWidth(300)
        f_window.setWindowTitle(_("Add Bookmark"))
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_grid_layout = QGridLayout()
        f_layout.addLayout(f_grid_layout)
        f_dict = bookmark.get_file_bookmarks()
        f_dict.pop('system')
        if not f_dict:
            f_dict = {'default':None}
        f_grid_layout.addWidget(QLabel(_("Category:")), 0, 0)
        f_category = QComboBox()
        f_category.setToolTip('Bookmarks are grouped by category names')
        f_category.setEditable(True)
        f_category.addItems(sorted(f_dict.keys(), key=lambda s: s.lower()))
        f_grid_layout.addWidget(f_category, 0, 1)
        if a_recursive:
            f_grid_layout.addWidget(QLabel(_("Filter:")), 2, 0)
            filter_lineedit = QLineEdit()
            f_grid_layout.addWidget(filter_lineedit, 2, 1)
            filter_lineedit.textChanged.connect(filter_changed)
        else:
            f_lineedit = QLineEdit()
            f_lineedit.setToolTip('The name of this bookmark')
            f_lineedit.setText(os.path.basename(self.last_open_dir))
            f_grid_layout.addWidget(QLabel(_("Name:")), 1, 0)
            f_grid_layout.addWidget(f_lineedit, 1, 1)
        f_hlayout2 = QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        if a_recursive:
            f_ok_button = QPushButton(_("Add"))
            f_cancel_button = QPushButton(_("Close"))
        else:
            f_ok_button = QPushButton(_("OK"))
            f_cancel_button = QPushButton(_("Cancel"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)
        if a_recursive:
            glbl_shared.APP.setOverrideCursor(
                QtCore.Qt.CursorShape.WaitCursor,
            )
            dirs = [os.path.join(x, a)
                for x, y, z in os.walk(self.last_open_dir) for a in y
                if "__MACOSX" not in x]
            dirs.sort()
            glbl_shared.APP.restoreOverrideCursor()
            dir_list_widget = QListWidget()
            dir_list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.MultiSelection,
            )
            f_layout.addWidget(dir_list_widget)
            for dirname in dirs:
                dirname_abbrev = dirname.replace(self.last_open_dir, "", 1)
                item = QListWidgetItem(dirname_abbrev)
                item.dir_name = dirname
                item.dirname_abbrev = dirname_abbrev
                dir_list_widget.addItem(item)
            dir_list_widget.selectAll()
        f_window.exec()

    def copy_button_pressed(self):
        f_clipboard = glbl_shared.APP.clipboard()
        f_clipboard.setText(self.last_open_dir)

    def paste_button_pressed(self):
        f_clipboard = QApplication.clipboard()
        f_text = f_clipboard.text()
        if f_text is None:
            QMessageBox.warning(self.paste_from_clipboard, _("Error"),
            _("No file path in the system clipboard."))
        else:
            f_text = str(f_text).strip()
            if os.path.exists(f_text):
                if os.path.isfile(f_text):
                    self.open_file_in_browser(f_text)
                elif os.path.isdir(f_text):
                    self.set_folder(f_text, True)
                else:
                    QMessageBox.warning(
                        self.hsplitter,
                        _("Error"),
                        "'{}' exists, but did not test True for being "
                        "a file or a folder".format(f_text)
                    )
            else:
                #Don't show more than 100 chars just in case somebody had an
                #entire book copied to the clipboard
                f_str = f_text[100:]
                QMessageBox.warning(
                    self.hsplitter, _("Error"),
                    _("'{}' does not exist.").format(f_str))

    def bookmark_clicked(self, a_item):
        #test = QTreeWidgetItem()
        #test.parent()
        f_parent = a_item.parent()
        if f_parent is not None:
            f_parent_str = str(f_parent.text(0))
            f_dict = bookmark.get_file_bookmarks()
            f_folder_name = str(a_item.text(0))
            if f_parent_str in f_dict:
                if f_folder_name in f_dict[f_parent_str]:
                    self.set_folder(f_dict[f_parent_str][f_folder_name], True)
                    # Set the Files tab as the selected tab
                    self.folders_tab_widget.setCurrentWidget(self.vsplitter)
                else:
                    QMessageBox.warning(
                        glbl_shared.MAIN_WINDOW,
                        _("Error"),
                        _("This bookmark no longer exists.  You may have "
                        "deleted it in another window."),
                    )
                self.open_bookmarks()

    def delete_bookmark(self):
        f_items = self.list_bookmarks.selectedItems()
        if len(f_items) > 0:
            f_parent = f_items[0].parent()
            if f_parent is None:
                f_parent = f_items[0]
                for f_i in range(f_parent.childCount()):
                    f_child = f_parent.child(f_i)
                    bookmark.delete_file_bookmark(
                        f_parent.text(0), f_child.text(0))
            else:
                bookmark.delete_file_bookmark(
                    f_parent.text(0), f_items[0].text(0))
                self.list_bookmarks.clear()
            self.open_bookmarks()

    def bookmark_context_menu_event(self, a_event):
        f_menu = QMenu(self.list_bookmarks)
        f_del_action = f_menu.addAction(_("Delete"))
        f_del_action.triggered.connect(self.delete_bookmark)
        f_menu.exec(QCursor.pos())

    def folder_item_clicked(self, a_item):
        self.set_folder(a_item.text())

    def on_up_button(self):
        self.set_folder("..")

    def set_folder(self, a_folder, a_full_path=False):
        if (
            util.IS_WINDOWS
            and
            not a_full_path
            and
            a_folder == '..'
            and
            self.last_open_dir == ''
        ):
            return
        a_folder = str(a_folder)
        file_pos = self.list_file.currentRow()
        folder_pos = self.list_folder.currentRow()
        self.scroll_dict[self.last_open_dir] = (file_pos, folder_pos)
        self.list_file.clear()
        self.list_folder.clear()
        self.folder_filter_lineedit.clear()
        f_old_path = self.last_open_dir
        if a_full_path and a_folder:  # a_folder being empty is handled...
            self.last_open_dir = a_folder
        else:
            if util.IS_WINDOWS and (
                (a_full_path and not a_folder)
                or (
                    not a_full_path
                    and
                    len(self.last_open_dir) == 3
                    and
                    a_folder == ".."
                )
            ):
                self.last_open_dir = ""
                self.folder_path_lineedit.setText("")
                for drive, label in util.get_win_drives():
                    f_item = QListWidgetItem(drive)
                    f_item.setToolTip(label)
                    self.list_folder.addItem(f_item)
                return
            else:
                self.last_open_dir = os.path.abspath(
                    os.path.join(self.last_open_dir, a_folder))
        self.last_open_dir = os.path.normpath(self.last_open_dir)
        if self.last_open_dir != self.history[-1]:
            #don't keep more than one copy in history
            if self.last_open_dir in self.history:
                self.history.remove(self.last_open_dir)
            self.history.append(self.last_open_dir)
        self.folder_path_lineedit.setText(self.last_open_dir)
        try:
            f_list = os.listdir(self.last_open_dir)
        except PermissionError:
            QMessageBox.warning(
                glbl_shared.MAIN_WINDOW,
                _("Error"),
                _("Access denied, you do not have "
                "permission to access {}".format(self.last_open_dir)))
            self.set_folder(f_old_path, True)
            return
        f_list.sort(key=lambda x: x.lower())
        for f_file in f_list:
            f_full_path = os.path.join(self.last_open_dir, f_file)
            if not f_file.startswith("."):
                if os.path.isdir(f_full_path):
                    f_item = QListWidgetItem(f_file)
                    f_item.setToolTip(f_file)
                    self.list_folder.addItem(f_item)
                elif self.filter_func(f_file) and \
                os.path.isfile(f_full_path):
                    if not util.str_has_bad_chars(f_full_path):
                        f_item = QListWidgetItem(f_file)
                        f_item.setToolTip(f_file)
                        self.list_file.addItem(f_item)
                    else:
                        QMessageBox.warning(
                            glbl_shared.MAIN_WINDOW,
                            _("Error"),
                            _("Not adding '{}' because it contains bad chars, "
                            "you must rename this file path without:\n{}"
                            ).format(
                                f_full_path,
                                "\n".join(util.bad_chars),
                            )
                        )
        self.on_filter_files()
        self.on_filter_folders()
        if self.last_open_dir in self.scroll_dict:
            file_pos, folder_pos = self.scroll_dict[self.last_open_dir]
            self.list_file.setCurrentRow(file_pos)
            self.list_folder.setCurrentRow(folder_pos)


    def select_file(self, a_file):
        """ Select the file if present in the list, a_file should be
            a file name, not a full path
        """
        for f_i in range(self.list_file.count()):
            f_item = self.list_file.item(f_i)
            if str(f_item.text()) == str(a_file):
                self.list_file.setCurrentRow(f_i)
                break

    def files_selected(self):
        f_result = []
        for f_file in self.list_file.selectedItems():
            f_result.append(
                os.path.join(
                    *(str(x) for x in (self.last_open_dir, f_file.text()))
                )
            )
        return f_result


class FileBrowserWidget(AbstractFileBrowserWidget):
    def __init__(self):
        AbstractFileBrowserWidget.__init__(self)
        self.load_button = QPushButton(_("Load"))
        self.file_hlayout.addWidget(self.load_button)
        self.list_file.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )

