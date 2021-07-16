from sglib import constants
from sglib.log import LOG
from sglib.api.daw import api_playlist
from sgui.daw.lib import sequence as sequence_lib
from sgui.sgqt import (
    QtCore,
    QtWidgets,
)


class PlaylistWidget:
    def __init__(self):
        self.suppress_changes = True
        self.parent = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.parent)
        splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical,
        )
        layout.addWidget(splitter)

        # Playlist
        playlist_widget = QtWidgets.QWidget()
        playlist_vlayout = QtWidgets.QVBoxLayout(playlist_widget)
        playlist_hlayout = QtWidgets.QHBoxLayout()
        playlist_vlayout.addLayout(playlist_hlayout)
        playlist_label = QtWidgets.QLabel("Playlist")
        playlist_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        playlist_hlayout.addWidget(playlist_label)
        playlist_menu_button = QtWidgets.QPushButton("Menu")
        playlist_hlayout.addWidget(playlist_menu_button)
        playlist_menu = QtWidgets.QMenu()
        delete_action = playlist_menu.addAction('Delete Selected')
        delete_action.triggered.connect(self.delete_playlist_items)
        playlist_menu_button.setMenu(playlist_menu)

        self.playlist_widget = QtWidgets.QListWidget()
        playlist_vlayout.addWidget(self.playlist_widget)
        self.playlist_widget.setAlternatingRowColors(True)
        self.playlist_widget.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.DragDrop,
        )
        self.playlist_widget.setDefaultDropAction(
            QtCore.Qt.DropAction.MoveAction
        )
        self.playlist_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        model = self.playlist_widget.model()
        model.rowsMoved.connect(self.playlist_changed)
        self.playlist_widget.itemChanged.connect(self.playlist_changed)
        self.playlist_widget.indexesMoved.connect(self.playlist_changed)
        self.playlist_widget.itemClicked.connect(self.playlist_item_clicked)
        splitter.addWidget(playlist_widget)
        splitter.setCollapsible(0, False)

        # Sequence list
        sequence_widget = QtWidgets.QWidget()
        sequence_vlayout = QtWidgets.QVBoxLayout(
            sequence_widget,
        )
        sequence_vlayout.addWidget(
            QtWidgets.QLabel("Sequence Pool"),
        )
        self.sequence_widget = QtWidgets.QListWidget()
        sequence_vlayout.addWidget(self.sequence_widget)
        self.sequence_widget.setAlternatingRowColors(True)
        self.sequence_widget.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.DragOnly,
        )
        self.sequence_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.sequence_widget.itemChanged.connect(self.sequence_changed)
        self.sequence_widget.itemClicked.connect(self.sequence_item_clicked)
        splitter.addWidget(sequence_widget)
        splitter.setCollapsible(1, False)

        # Add new sequence
        add_seq_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(add_seq_layout)
        self.add_seq_text = QtWidgets.QLineEdit()
        self.add_seq_text.returnPressed.connect(self.add_seq)
        add_seq_layout.addWidget(self.add_seq_text)
        self.add_seq_button = QtWidgets.QPushButton("Add")
        add_seq_layout.addWidget(self.add_seq_button)
        self.add_seq_button.pressed.connect(self.add_seq)
        self.suppress_changes = False

    def on_play(self):
        self.parent.setDisabled(True)

    def on_stop(self):
        self.parent.setEnabled(True)

    def add_seq(self):
        """ Add a new sequence to the pool.  Not to be confused with adding
            a sequence to the playlist.
        """
        name = self.add_seq_text.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Error",
                "Must have a name",
            )
            return
        try:
            api_playlist.new_seq(name)
        except FileExistsError:
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Error",
                "Sequence '{}' already exists".format(name),
            )
            return
        self.add_seq_text.clear()
        self.open()

    def playlist_changed(self):
        """ Add, move, delete from the playlist
        """
        if self.suppress_changes:
            return
        playlist = []
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            playlist.append(item.text())
        api_playlist.playlist_changed(playlist)

    def playlist_item_clicked(self, item):
        items = self.playlist_widget.selectedItems()
        if (
            len(items) == 1
            and
            # User did not CTRL+click unselect one of 2 items
            items[0].text() == item.text()
        ):
            name = str(item.text())
            LOG.info(f"Opening sequence {name}")
            sequence_lib.change_sequence(name)

    def sequence_item_clicked(self, item):
        items = self.sequence_widget.selectedItems()
        if (
            len(items) == 1
            and
            # User did not CTRL+click unselect one of 2 items
            items[0].text() == item.text()
        ):
            name = str(item.text())
            LOG.info(f"Opening sequence {name}")
            sequence_lib.change_sequence(name)

    def sequence_changed(self, item):
        """ Currently only catches rename events when the user double clicks
            an item and changes the name
        """
        if self.suppress_changes:
            return
        new_name = item.text().strip()
        if new_name and new_name != item.orig_name:
            try:
                api_playlist.change_name(item.orig_name, new_name)
            except FileExistsError:
                QtWidgets.QMessageBox.warning(
                    self.parent,
                    "Error",
                    "Sequence '{}' already exists".format(new_name),
                )
            except FileNotFoundError:
                LOG.exception("orig_name not found, likely a bug")
                QtWidgets.QMessageBox.warning(
                    self.parent,
                    "Error",
                    "Original Sequence name '{}' not found".format(
                        item.orig_name,
                    ),
                )
        self.open()

    def add_playlist_item(self, name):
        flags = (
            QtCore.Qt.ItemFlag.ItemIsDragEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsDropEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        self.add_item(
            name,
            self.playlist_widget,
            flags,
        )

    def add_sequence_item(self, name):
        flags = (
            QtCore.Qt.ItemFlag.ItemIsDragEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsDropEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsEditable
            |
            QtCore.Qt.ItemFlag.ItemIsEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        self.add_item(
            name,
            self.sequence_widget,
            flags,
        )

    def add_item(
        self,
        name,
        parent,
        flags,
    ):
        """ Add a QListWidgetItem to a QListWidget
            @name:   str, The name to display on the item
            @parent: QListWidget, The list widget to add the item to
            @flags:  int, The item flags
        """
        self.suppress_changes = True
        item = QtWidgets.QListWidgetItem(
            str(name),
            parent,
        )
        item.orig_name = name
        item.setFlags(flags)
        self.suppress_changes = False

    def delete_playlist_items(self):
        model = self.playlist_widget.selectionModel()
        indices = [x.row() for x in model.selectedIndexes()]
        if not indices:
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Error",
                "No items selected",
            )
            return
        if len(indices) == self.playlist_widget.count():
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Error",
                "Cannot delete all sequences from the playlist",
            )
            return
        api_playlist.delete_playlist_items(indices)
        self.open()

    def open(self):
        """ Populate the widgets from the project files
        """
        self.playlist_widget.clear()
        self.sequence_widget.clear()
        playlist_names, sequence_names = api_playlist.load()
        for name in playlist_names:
            self.add_playlist_item(name)
        for name in sequence_names:
            self.add_sequence_item(name)

